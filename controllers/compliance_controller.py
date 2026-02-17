from database import db
from models.compliance import GSTReturn, GSTReturnCreate, RERAProject, RERAProjectCreate


async def create_gst_return(gst_data: GSTReturnCreate) -> GSTReturn:
    gst_return = GSTReturn(**gst_data.model_dump())
    gst_return.tax_payable = gst_return.cgst + gst_return.sgst + gst_return.igst - gst_return.itc_claimed
    await db.gst_returns.insert_one(gst_return.model_dump())
    return gst_return


async def get_gst_returns() -> list:
    return await db.gst_returns.find({}, {"_id": 0}).to_list(1000)


async def create_rera_project(rera_data: RERAProjectCreate) -> RERAProject:
    rera_project = RERAProject(**rera_data.model_dump())
    await db.rera_projects.insert_one(rera_project.model_dump())
    return rera_project


async def get_rera_projects() -> list:
    return await db.rera_projects.find({}, {"_id": 0}).to_list(1000)
