from fastapi import HTTPException
from typing import Optional, List
from datetime import datetime, timezone

from database import db
from models.inventory import InventoryItem, InventoryItemCreate, InventoryItemUpdate, InventoryQuantityUpdate, InventoryTransfer
from models.hrms import Employee


def _compute_status(quantity: float, minimum_quantity: float) -> str:
    if quantity <= 0:
        return "out_of_stock"
    if minimum_quantity > 0 and quantity <= minimum_quantity:
        return "low_stock"
    return "in_stock"


async def create_item(data: InventoryItemCreate, current_user: Employee) -> InventoryItem:
    item = InventoryItem(**data.model_dump())
    item.total_value = item.quantity * item.unit_price
    item.status = _compute_status(item.quantity, item.minimum_quantity)
    item.created_by = current_user.id
    await db.inventory.insert_one(item.model_dump())
    return item


async def get_items(project_id: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None) -> List[dict]:
    query = {}
    if project_id:
        query["project_id"] = project_id
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    return await db.inventory.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)


async def get_item(item_id: str) -> dict:
    item = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


async def update_item(item_id: str, data: InventoryItemUpdate) -> dict:
    existing = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    update = data.model_dump(exclude_unset=True)
    # Recalculate derived fields
    new_qty = update.get("quantity", existing["quantity"])
    new_min = update.get("minimum_quantity", existing["minimum_quantity"])
    new_price = update.get("unit_price", existing["unit_price"])
    update["total_value"] = new_qty * new_price
    update["status"] = _compute_status(new_qty, new_min)
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.inventory.update_one({"id": item_id}, {"$set": update})
    return await db.inventory.find_one({"id": item_id}, {"_id": 0})


async def update_quantity(item_id: str, data: InventoryQuantityUpdate) -> dict:
    existing = await db.inventory.find_one({"id": item_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if data.operation == "add":
        new_qty = existing["quantity"] + data.quantity
    elif data.operation == "subtract":
        new_qty = existing["quantity"] - data.quantity
        if new_qty < 0:
            raise HTTPException(status_code=400, detail="Quantity cannot go below zero")
    else:  # "set"
        new_qty = data.quantity
    unit_price = existing["unit_price"]
    min_qty = existing["minimum_quantity"]
    update = {
        "quantity": new_qty,
        "total_value": new_qty * unit_price,
        "status": _compute_status(new_qty, min_qty),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.inventory.update_one({"id": item_id}, {"$set": update})
    return await db.inventory.find_one({"id": item_id}, {"_id": 0})


async def transfer_material(data: InventoryTransfer, current_user: Employee) -> dict:
    source = await db.inventory.find_one({"id": data.from_item_id}, {"_id": 0})
    if not source:
        raise HTTPException(status_code=404, detail="Source item not found")
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Transfer quantity must be greater than zero")
    if source["quantity"] < data.quantity:
        raise HTTPException(status_code=400, detail=f"Insufficient quantity. Available: {source['quantity']} {source['unit']}")
    if source["project_id"] == data.to_project_id:
        raise HTTPException(status_code=400, detail="Source and destination project must be different")

    # Deduct from source
    new_src_qty = source["quantity"] - data.quantity
    await db.inventory.update_one({"id": data.from_item_id}, {"$set": {
        "quantity": new_src_qty,
        "total_value": new_src_qty * source["unit_price"],
        "status": _compute_status(new_src_qty, source["minimum_quantity"]),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }})

    if data.to_item_id:
        # User selected a specific destination item — add quantity to it
        dest = await db.inventory.find_one({"id": data.to_item_id}, {"_id": 0})
        if not dest:
            raise HTTPException(status_code=404, detail="Destination item not found")
        new_dest_qty = dest["quantity"] + data.quantity
        await db.inventory.update_one({"id": dest["id"]}, {"$set": {
            "quantity": new_dest_qty,
            "total_value": new_dest_qty * dest["unit_price"],
            "status": _compute_status(new_dest_qty, dest["minimum_quantity"]),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }})
    else:
        # No destination item selected — create new item in destination project
        new_item = InventoryItem(
            project_id=data.to_project_id,
            item_name=source["item_name"],
            category=source["category"],
            unit=source["unit"],
            quantity=data.quantity,
            minimum_quantity=source.get("minimum_quantity", 0),
            unit_price=source["unit_price"],
            gst_rate=source.get("gst_rate", 18.0),
            hsn_code=source.get("hsn_code"),
            location=source.get("location"),
            notes=f"Transferred from project. {data.notes or ''}".strip(),
        )
        new_item.total_value = data.quantity * source["unit_price"]
        new_item.status = _compute_status(data.quantity, new_item.minimum_quantity)
        new_item.created_by = current_user.id
        await db.inventory.insert_one(new_item.model_dump())

    return {
        "message": f"Transferred {data.quantity} {source['unit']} of '{source['item_name']}' successfully",
        "transferred_quantity": data.quantity,
        "unit": source["unit"],
        "item_name": source["item_name"]
    }


async def delete_item(item_id: str) -> dict:
    result = await db.inventory.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"message": "Item deleted"}


async def get_dashboard(project_id: Optional[str] = None) -> dict:
    query = {"project_id": project_id} if project_id else {}
    items = await db.inventory.find(query, {"_id": 0}).to_list(5000)
    total_items = len(items)
    total_value = sum(i.get("total_value", 0) for i in items)
    low_stock = len([i for i in items if i.get("status") == "low_stock"])
    out_of_stock = len([i for i in items if i.get("status") == "out_of_stock"])
    by_category = {}
    for i in items:
        cat = i.get("category", "Other")
        by_category[cat] = by_category.get(cat, 0) + 1
    by_project = {}
    for i in items:
        pid = i.get("project_id")
        by_project[pid] = by_project.get(pid, 0) + 1
    return {
        "total_items": total_items,
        "total_value": total_value,
        "low_stock_count": low_stock,
        "out_of_stock_count": out_of_stock,
        "by_category": by_category,
        "by_project": by_project
    }
