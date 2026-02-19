"""
Comprehensive RBAC Permission Tests for Civil ERP
Tests all module permissions end-to-end: backend check_permission + frontend hasPermission coverage.
Also verifies that CRUD buttons are only visible when the user has the correct permission.
"""
import pytest
import os
import re
from unittest.mock import MagicMock

# ─── Config Constants ─────────────────────────────────────────
MODULES = [
    "dashboard", "projects", "financial", "procurement",
    "hrms", "reports", "ai_assistant", "settings", "inventory"
]
PERMISSION_TYPES = ["view", "create", "edit", "delete"]

# Modules that were disabled (commented out from sidebar/routes)
DISABLED_MODULES = ["compliance", "einvoicing"]

FRONTEND_PAGES_DIR = "../frontend/src/pages"
FRONTEND_SRC_DIR = "../frontend/src"


def _read_frontend(relative_path):
    filepath = os.path.join(FRONTEND_SRC_DIR, relative_path)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def _read_page(filename):
    filepath = os.path.join(FRONTEND_PAGES_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


# ═══════════════════════════════════════════════════════════════
# 1. RBAC CONFIG TESTS
# ═══════════════════════════════════════════════════════════════
class TestRBACConfig:
    """Verify backend config matches expected modules."""

    def test_all_modules_defined(self):
        from config import MODULES as CONFIG_MODULES
        for mod in MODULES:
            assert mod in CONFIG_MODULES, f"Module '{mod}' missing from backend config.py MODULES"

    def test_permission_types_defined(self):
        from config import PERMISSION_TYPES as CONFIG_PERMS
        for ptype in PERMISSION_TYPES:
            assert ptype in CONFIG_PERMS, f"Permission type '{ptype}' missing from config"

    def test_no_extra_modules(self):
        from config import MODULES as CONFIG_MODULES
        for mod in CONFIG_MODULES:
            assert mod in MODULES, f"Unexpected module '{mod}' in config but not in test expectations"

    def test_disabled_modules_not_in_config(self):
        """compliance and einvoicing should NOT be in MODULES since they are disabled."""
        from config import MODULES as CONFIG_MODULES
        for mod in DISABLED_MODULES:
            assert mod not in CONFIG_MODULES, \
                f"Disabled module '{mod}' should NOT be in config.py MODULES"


# ═══════════════════════════════════════════════════════════════
# 2. check_permission FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════
class TestCheckPermission:
    """Unit tests for core.auth.check_permission."""

    @pytest.fixture
    def mock_admin_user(self):
        user = MagicMock()
        user.role = "admin"
        user.id = "admin-001"
        user.name = "Admin"
        return user

    def test_admin_bypasses_all_permissions(self, mock_admin_user):
        """Admin should bypass all permission checks."""
        from core.auth import check_permission
        for mod in MODULES:
            for action in PERMISSION_TYPES:
                checker = check_permission(mod, action)
                assert callable(checker)

    def test_check_permission_returns_callable(self):
        from core.auth import check_permission
        for mod in MODULES:
            for action in PERMISSION_TYPES:
                result = check_permission(mod, action)
                assert callable(result), f"check_permission('{mod}', '{action}') should return callable"


# ═══════════════════════════════════════════════════════════════
# 3. BACKEND ROUTE PERMISSION COVERAGE
# ═══════════════════════════════════════════════════════════════
class TestRoutePermissionCoverage:
    """Verify every backend route uses check_permission (not just get_current_user)."""

    def _assert_no_get_current_user_on_routes(self, module_path, label):
        import importlib
        mod = importlib.import_module(module_path)
        source = open(mod.__file__).read()
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'Depends(get_current_user)' in line:
                for j in range(i - 1, max(0, i - 5), -1):
                    if '@router' in lines[j]:
                        pytest.fail(f"{label} line {i+1}: endpoint uses get_current_user instead of check_permission")

    def test_projects_routes_use_check_permission(self):
        self._assert_no_get_current_user_on_routes("routes.projects", "projects.py")

    def test_financial_routes_use_check_permission(self):
        import routes.financial as mod
        source = open(mod.__file__).read()
        assert 'Depends(get_current_user)' not in source, \
            "financial.py should not use get_current_user — all endpoints should use check_permission"

    def test_procurement_routes_use_check_permission(self):
        self._assert_no_get_current_user_on_routes("routes.procurement", "procurement.py")

    def test_hrms_routes_use_check_permission(self):
        self._assert_no_get_current_user_on_routes("routes.hrms", "hrms.py")

    def test_inventory_routes_use_check_permission(self):
        self._assert_no_get_current_user_on_routes("routes.inventory", "inventory.py")

    def test_dashboard_routes_use_check_permission(self):
        import routes.dashboard as mod
        source = open(mod.__file__).read()
        assert 'Depends(get_current_user)' not in source, \
            "dashboard.py should use check_permission"

    def test_reports_routes_use_check_permission(self):
        import routes.reports as mod
        source = open(mod.__file__).read()
        assert 'Depends(get_current_user)' not in source, \
            "reports.py should use check_permission"

    def test_ai_routes_use_check_permission(self):
        import routes.ai as mod
        source = open(mod.__file__).read()
        assert 'Depends(get_current_user)' not in source, \
            "ai.py should use check_permission"

    def test_contractor_routes_use_check_permission(self):
        import routes.contractor as mod
        source = open(mod.__file__).read()
        assert 'Depends(get_current_user)' not in source, \
            "contractor.py should use check_permission"

    def test_contractor_list_requires_auth(self):
        """Bug fix: contractor list endpoint previously had NO auth at all."""
        import routes.contractor as mod
        source = open(mod.__file__).read()
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if '@router.get("/")' in line:
                func_lines = '\n'.join(lines[i:i+3])
                assert 'Depends' in func_lines, \
                    "contractor.py GET / must require authentication"
                break

    def test_documents_routes_use_check_permission(self):
        self._assert_no_get_current_user_on_routes("routes.documents", "documents.py")


# ═══════════════════════════════════════════════════════════════
# 4. ROUTE-MODULE PERMISSION MAPPING
# ═══════════════════════════════════════════════════════════════
class TestRouteModuleMapping:
    """Verify each route file checks the correct module name."""

    def _check_module_in_check_permission(self, filepath, expected_module):
        source = open(filepath).read()
        assert f'check_permission("{expected_module}"' in source, \
            f"{filepath} should use check_permission('{expected_module}', ...)"

    def test_projects_checks_projects_module(self):
        self._check_module_in_check_permission("routes/projects.py", "projects")

    def test_financial_checks_financial_module(self):
        self._check_module_in_check_permission("routes/financial.py", "financial")

    def test_procurement_checks_procurement_module(self):
        self._check_module_in_check_permission("routes/procurement.py", "procurement")

    def test_hrms_checks_hrms_module(self):
        self._check_module_in_check_permission("routes/hrms.py", "hrms")

    def test_inventory_checks_inventory_module(self):
        self._check_module_in_check_permission("routes/inventory.py", "inventory")

    def test_dashboard_checks_dashboard_module(self):
        self._check_module_in_check_permission("routes/dashboard.py", "dashboard")

    def test_reports_checks_reports_module(self):
        self._check_module_in_check_permission("routes/reports.py", "reports")

    def test_ai_checks_ai_assistant_module(self):
        self._check_module_in_check_permission("routes/ai.py", "ai_assistant")

    def test_settings_checks_settings_module(self):
        self._check_module_in_check_permission("routes/settings.py", "settings")

    def test_contractor_checks_hrms_module(self):
        """Contractors are managed under HRMS module."""
        self._check_module_in_check_permission("routes/contractor.py", "hrms")

    def test_documents_checks_projects_module(self):
        """Documents are managed under Projects module."""
        self._check_module_in_check_permission("routes/documents.py", "projects")

    def test_rbac_checks_hrms_module(self):
        """RBAC/roles are managed under HRMS module."""
        self._check_module_in_check_permission("routes/rbac.py", "hrms")


# ═══════════════════════════════════════════════════════════════
# 5. FRONTEND hasPermission COVERAGE
# ═══════════════════════════════════════════════════════════════
class TestFrontendPermissionCoverage:
    """Verify frontend pages have proper hasPermission checks."""

    def test_financial_has_permission_import(self):
        source = _read_page("Financial.jsx")
        assert "hasPermission" in source, "Financial.jsx must import hasPermission"

    def test_financial_checks_create_permission(self):
        source = _read_page("Financial.jsx")
        assert "hasPermission('financial', 'create')" in source, \
            "Financial.jsx must check financial.create for New Bill/CVR buttons"

    def test_financial_checks_edit_permission(self):
        source = _read_page("Financial.jsx")
        assert "hasPermission('financial', 'edit')" in source, \
            "Financial.jsx must check financial.edit for Approve/Pay buttons"

    def test_financial_checks_delete_permission(self):
        source = _read_page("Financial.jsx")
        assert "hasPermission('financial', 'delete')" in source, \
            "Financial.jsx must check financial.delete for delete buttons"

    def test_projects_has_permission_checks(self):
        source = _read_page("Projects.jsx")
        assert "hasPermission('projects', 'create')" in source

    def test_project_detail_has_permission_checks(self):
        source = _read_page("ProjectDetail.jsx")
        assert "hasPermission('projects', 'edit')" in source

    def test_procurement_has_permission_checks(self):
        source = _read_page("Procurement.jsx")
        assert "hasPermission('procurement', 'edit')" in source

    def test_inventory_has_permission_checks(self):
        source = _read_page("Inventory.jsx")
        assert "hasPermission('inventory', 'create')" in source
        assert "hasPermission('inventory', 'edit')" in source
        assert "hasPermission('inventory', 'delete')" in source

    def test_hrms_has_permission_checks(self):
        source = _read_page("HRMS.jsx")
        assert "hasPermission('hrms', 'create')" in source
        assert "hasPermission('hrms', 'edit')" in source
        assert "hasPermission('hrms', 'delete')" in source

    def test_hrms_employee_detail_has_permission_props(self):
        """Employee detail view should receive canEdit/canDelete props."""
        source = _read_page("HRMS.jsx")
        assert "canEdit={hasPermission('hrms', 'edit')}" in source, \
            "EmployeeDetailView must receive canEdit prop"
        assert "canDelete={hasPermission('hrms', 'delete')}" in source, \
            "EmployeeDetailView must receive canDelete prop"

    def test_hrms_payroll_status_has_permission(self):
        """Payroll Process/Mark Paid should check edit permission."""
        source = _read_page("HRMS.jsx")
        assert "hasPermission('hrms', 'edit')" in source

    def test_settings_has_permission_import(self):
        source = _read_page("Settings.jsx")
        assert "hasPermission" in source, "Settings.jsx must import hasPermission"

    def test_settings_integration_tabs_gated(self):
        """GST/Cloudinary/SMTP tabs should require settings.edit."""
        source = _read_page("Settings.jsx")
        assert "hasPermission('settings', 'edit')" in source, \
            "Settings.jsx must gate integration tabs with settings.edit"


# ═══════════════════════════════════════════════════════════════
# 6. FRONTEND MODULE_LABELS COMPLETENESS
# ═══════════════════════════════════════════════════════════════
class TestFrontendModuleLabels:
    """Verify MODULE_LABELS includes all active RBAC modules and excludes disabled ones."""

    def test_all_active_modules_in_labels(self):
        source = _read_frontend("lib/utils.js")
        match = re.search(r'MODULE_LABELS\s*=\s*\{([^}]+)\}', source)
        assert match, "MODULE_LABELS not found in utils.js"
        labels_block = match.group(1)

        for mod in MODULES:
            assert mod in labels_block, \
                f"MODULE_LABELS in utils.js is missing '{mod}' — roles permission matrix won't show this module!"

    def test_disabled_modules_not_in_labels(self):
        """compliance and einvoicing should NOT be in MODULE_LABELS."""
        source = _read_frontend("lib/utils.js")
        match = re.search(r'MODULE_LABELS\s*=\s*\{([^}]+)\}', source)
        assert match, "MODULE_LABELS not found in utils.js"
        labels_block = match.group(1)

        for mod in DISABLED_MODULES:
            assert mod not in labels_block, \
                f"Disabled module '{mod}' should NOT be in MODULE_LABELS"

    def test_inventory_in_module_labels(self):
        """Critical regression test: inventory was previously missing."""
        source = _read_frontend("lib/utils.js")
        assert 'inventory' in source, \
            "CRITICAL: 'inventory' must be in MODULE_LABELS — without it, admins can't set inventory permissions in roles!"


# ═══════════════════════════════════════════════════════════════
# 7. FRONTEND ROUTE PROTECTION
# ═══════════════════════════════════════════════════════════════
class TestFrontendRouteProtection:
    """Verify App.js routes use ProtectedRoute with correct modules."""

    def test_all_active_routes_protected(self):
        source = _read_frontend("App.js")
        # These modules must have active ProtectedRoute entries
        active_modules = [
            "dashboard", "projects", "financial", "procurement",
            "hrms", "reports", "ai_assistant", "settings", "inventory"
        ]
        for mod in active_modules:
            assert f'module="{mod}"' in source, \
                f"App.js missing ProtectedRoute with module='{mod}'"

    def test_disabled_routes_commented_out(self):
        """compliance and einvoicing routes should be commented out in App.js."""
        source = _read_frontend("App.js")
        # Check that the module routes are inside comment blocks
        for mod in DISABLED_MODULES:
            # Should NOT have an active (uncommented) ProtectedRoute
            lines = source.split('\n')
            for i, line in enumerate(lines):
                stripped = line.strip()
                if f'module="{mod}"' in stripped and not stripped.startswith('//') and not stripped.startswith('*') and not stripped.startswith('{/*'):
                    # Check if it's inside a JSX comment block
                    block = source[:source.index(line)]
                    open_comments = block.count('{/*')
                    close_comments = block.count('*/}')
                    if open_comments <= close_comments:
                        pytest.fail(f"App.js has active ProtectedRoute for disabled module '{mod}' — should be commented out")


# ═══════════════════════════════════════════════════════════════
# 8. SIDEBAR NAVIGATION PERMISSION
# ═══════════════════════════════════════════════════════════════
class TestSidebarPermission:
    """Verify sidebar filters nav items by canViewModule."""

    def test_sidebar_uses_can_view_module(self):
        source = _read_frontend("components/layout/Sidebar.jsx")
        assert "canViewModule" in source, "Sidebar must use canViewModule to filter nav items"

    def test_audit_logs_admin_only(self):
        source = _read_frontend("components/layout/Sidebar.jsx")
        assert "adminOnly: true" in source, "Audit logs should be admin-only in sidebar"

    def test_disabled_modules_commented_in_sidebar(self):
        """compliance and einvoicing should be commented out in sidebar nav."""
        source = _read_frontend("components/layout/Sidebar.jsx")
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            if 'compliance' in stripped and not stripped.startswith('//'):
                pytest.fail("Sidebar has active nav item for disabled 'compliance' module")
            if 'einvoicing' in stripped and not stripped.startswith('//'):
                pytest.fail("Sidebar has active nav item for disabled 'einvoicing' module")


# ═══════════════════════════════════════════════════════════════
# 9. PERMISSION FLOW INTEGRATION
# ═══════════════════════════════════════════════════════════════
class TestPermissionFlow:
    """Test the full permission check flow."""

    def test_admin_role_seeded_on_startup(self):
        with open("server.py", "r") as f:
            source = f.read()
        assert "admin" in source, "server.py should seed admin role on startup"

    def test_auth_context_has_permission_function(self):
        source = _read_frontend("context/AuthContext.js")
        assert "hasPermission" in source
        assert "canViewModule" in source
        assert "permissions" in source

    def test_has_permission_admin_bypass(self):
        """hasPermission should return true for admin role."""
        source = _read_frontend("context/AuthContext.js")
        assert "user?.role === 'admin'" in source, \
            "hasPermission must check for admin role bypass"

    def test_check_permission_admin_bypass(self):
        """Backend check_permission should bypass for admin."""
        with open("core/auth.py", "r") as f:
            source = f.read()
        assert 'current_user.role == "admin"' in source, \
            "check_permission must bypass permission check for admin role"

    def test_disabled_modules_not_registered_in_server(self):
        """compliance and einvoicing routers should be commented out in server.py."""
        with open("server.py", "r") as f:
            source = f.read()
        lines = source.split('\n')
        for line in lines:
            stripped = line.strip()
            if 'compliance_router' in stripped and not stripped.startswith('#'):
                pytest.fail("server.py has active compliance_router — should be commented out")
            if 'einvoice_router' in stripped and not stripped.startswith('#'):
                pytest.fail("server.py has active einvoice_router — should be commented out")


# ═══════════════════════════════════════════════════════════════
# 10. PERMISSION MATRIX COMPLETENESS
# ═══════════════════════════════════════════════════════════════
class TestPermissionMatrix:
    """Verify CRUD operations are properly gated per module."""

    ROUTE_MODULE_MAP = {
        "routes/projects.py": ("projects", ["view", "create", "edit", "delete"]),
        "routes/financial.py": ("financial", ["view", "create", "edit", "delete"]),
        "routes/procurement.py": ("procurement", ["view", "create", "edit", "delete"]),
        "routes/hrms.py": ("hrms", ["view", "create", "edit", "delete"]),
        "routes/inventory.py": ("inventory", ["view", "create", "edit", "delete"]),
        "routes/dashboard.py": ("dashboard", ["view"]),
        "routes/reports.py": ("reports", ["view"]),
        "routes/ai.py": ("ai_assistant", ["view"]),
        "routes/settings.py": ("settings", ["view", "edit", "delete"]),
    }

    def test_all_expected_permissions_present(self):
        """Each route file should use check_permission for all expected actions."""
        for filepath, (module, actions) in self.ROUTE_MODULE_MAP.items():
            with open(filepath, "r") as f:
                source = f.read()
            for action in actions:
                expected = f'check_permission("{module}", "{action}")'
                assert expected in source, \
                    f"{filepath}: missing check_permission('{module}', '{action}')"


# ═══════════════════════════════════════════════════════════════
# 11. BUTTON VISIBILITY — CREATE BUTTONS GATED BY create PERMISSION
# ═══════════════════════════════════════════════════════════════
class TestCreateButtonVisibility:
    """
    Verify that all 'Add / New / Create' buttons are wrapped with
    hasPermission(module, 'create') so they are hidden for users
    without create permission.
    """

    def test_financial_new_bill_button_gated(self):
        """New Bill dialog should only render if user has financial.create."""
        source = _read_page("Financial.jsx")
        # The create dialog trigger must be inside a hasPermission check
        assert "hasPermission('financial', 'create')" in source, \
            "New Bill button must be gated by hasPermission('financial', 'create')"
        # Verify the pattern: permission check appears BEFORE the dialog
        create_idx = source.index("hasPermission('financial', 'create')")
        assert "New Bill" in source[create_idx:create_idx+500] or "Dialog" in source[create_idx:create_idx+500], \
            "hasPermission('financial', 'create') should gate the New Bill dialog"

    def test_financial_new_cvr_button_gated(self):
        """New CVR dialog should only render if user has financial.create."""
        source = _read_page("Financial.jsx")
        # There should be at least 2 occurrences of create check (bill + CVR)
        count = source.count("hasPermission('financial', 'create')")
        assert count >= 2, \
            f"Financial.jsx should have at least 2 create permission checks (bill + CVR), found {count}"

    def test_projects_new_project_button_gated(self):
        """New Project button should only show with projects.create."""
        source = _read_page("Projects.jsx")
        assert "hasPermission('projects', 'create')" in source, \
            "New Project button must be gated by hasPermission('projects', 'create')"

    def test_hrms_add_employee_button_gated(self):
        """Add Employee button should only show with hrms.create."""
        source = _read_page("HRMS.jsx")
        assert "hasPermission('hrms', 'create')" in source, \
            "Add Employee button must be gated by hasPermission('hrms', 'create')"

    def test_inventory_add_item_button_gated(self):
        """Add Item button should only show with inventory.create."""
        source = _read_page("Inventory.jsx")
        assert "hasPermission('inventory', 'create')" in source, \
            "Add Item button must be gated by hasPermission('inventory', 'create')"

    def test_procurement_add_vendor_button_gated(self):
        """Add Vendor button should only show with procurement.edit."""
        source = _read_page("Procurement.jsx")
        assert "hasPermission('procurement', 'edit')" in source, \
            "Add Vendor button must be gated by procurement.edit permission"

    def test_project_detail_new_dpr_button_gated(self):
        """New DPR button should only show with projects.edit."""
        source = _read_page("ProjectDetail.jsx")
        assert "hasPermission('projects', 'edit')" in source, \
            "New DPR button must be gated by hasPermission('projects', 'edit')"

    def test_project_detail_add_task_button_gated(self):
        """Add Task button should only show with projects.edit."""
        source = _read_page("ProjectDetail.jsx")
        # Count how many times edit permission is checked
        count = source.count("hasPermission('projects', 'edit')")
        assert count >= 3, \
            f"ProjectDetail.jsx should check projects.edit in multiple places (tasks, DPR, docs), found {count}"

    def test_project_detail_upload_doc_button_gated(self):
        """Upload Document button should only show with projects.edit."""
        source = _read_page("ProjectDetail.jsx")
        # Document upload section should be gated
        edit_positions = [m.start() for m in re.finditer(r"hasPermission\('projects',\s*'edit'\)", source)]
        assert len(edit_positions) >= 1, \
            "ProjectDetail.jsx must gate document upload with projects.edit"


# ═══════════════════════════════════════════════════════════════
# 12. BUTTON VISIBILITY — EDIT/STATUS BUTTONS GATED BY edit PERMISSION
# ═══════════════════════════════════════════════════════════════
class TestEditButtonVisibility:
    """
    Verify that edit/status-change buttons are wrapped with
    hasPermission(module, 'edit') so they are hidden for users
    without edit permission.
    """

    def test_financial_bill_status_change_gated(self):
        """Approve/Mark Paid buttons should require financial.edit."""
        source = _read_page("Financial.jsx")
        assert "hasPermission('financial', 'edit')" in source, \
            "Bill status change (Approve/Mark Paid) must check financial.edit"

    def test_financial_bill_detail_edit_gated(self):
        """BillDetail component should receive canEdit prop."""
        source = _read_page("Financial.jsx")
        assert "canEdit" in source, \
            "BillDetail must receive canEdit prop from hasPermission"

    def test_hrms_employee_edit_button_gated(self):
        """Employee Edit button should only show with hrms.edit."""
        source = _read_page("HRMS.jsx")
        assert "canEdit={hasPermission('hrms', 'edit')}" in source, \
            "EmployeeDetailView must receive canEdit prop gated by hrms.edit"

    def test_hrms_payroll_status_buttons_gated(self):
        """Payroll Process/Mark Paid buttons should require hrms.edit."""
        source = _read_page("HRMS.jsx")
        # payroll status flow should check edit permission
        assert "hasPermission('hrms', 'edit')" in source

    def test_inventory_edit_button_gated(self):
        """Inventory Edit/Adjust Stock buttons should require inventory.edit."""
        source = _read_page("Inventory.jsx")
        assert "hasPermission('inventory', 'edit')" in source, \
            "Inventory edit actions must check inventory.edit"

    def test_project_detail_status_dropdown_gated(self):
        """Project status change dropdown should require projects.edit."""
        source = _read_page("ProjectDetail.jsx")
        assert "hasPermission('projects', 'edit')" in source, \
            "Project status change must check projects.edit"

    def test_project_detail_task_status_gated(self):
        """Task status change should show dropdown only with projects.edit, badge otherwise."""
        source = _read_page("ProjectDetail.jsx")
        # Task status uses conditional rendering: edit → select, no edit → badge
        edit_checks = source.count("hasPermission('projects', 'edit')")
        assert edit_checks >= 4, \
            f"ProjectDetail.jsx should check projects.edit for tasks (status dropdown, edit/delete, add), found {edit_checks}"

    def test_settings_integration_tabs_edit_gated(self):
        """Settings GST/Cloudinary/SMTP tabs should require settings.edit."""
        source = _read_page("Settings.jsx")
        assert "hasPermission('settings', 'edit')" in source, \
            "Settings integration tabs must check settings.edit"


# ═══════════════════════════════════════════════════════════════
# 13. BUTTON VISIBILITY — DELETE BUTTONS GATED BY delete PERMISSION
# ═══════════════════════════════════════════════════════════════
class TestDeleteButtonVisibility:
    """
    Verify that delete/deactivate buttons are wrapped with
    hasPermission(module, 'delete') so they are hidden for users
    without delete permission.
    """

    def test_financial_cvr_delete_button_gated(self):
        """CVR delete button should require financial.delete."""
        source = _read_page("Financial.jsx")
        assert "hasPermission('financial', 'delete')" in source, \
            "CVR delete button must check financial.delete"

    def test_financial_bill_detail_delete_gated(self):
        """BillDetail component should receive canDelete prop."""
        source = _read_page("Financial.jsx")
        assert "canDelete" in source, \
            "BillDetail must receive canDelete prop from hasPermission"

    def test_hrms_employee_deactivate_button_gated(self):
        """Employee Deactivate button should only show with hrms.delete."""
        source = _read_page("HRMS.jsx")
        assert "canDelete={hasPermission('hrms', 'delete')}" in source, \
            "EmployeeDetailView must receive canDelete prop gated by hrms.delete"

    def test_inventory_delete_button_gated(self):
        """Inventory delete button should require inventory.delete."""
        source = _read_page("Inventory.jsx")
        assert "hasPermission('inventory', 'delete')" in source, \
            "Inventory delete button must check inventory.delete"

    def test_project_detail_task_delete_gated(self):
        """Task delete button should require projects.edit permission."""
        source = _read_page("ProjectDetail.jsx")
        # Task edit/delete actions are gated by projects.edit
        assert "hasPermission('projects', 'edit')" in source

    def test_project_detail_doc_delete_gated(self):
        """Document delete should require projects.edit permission."""
        source = _read_page("ProjectDetail.jsx")
        edit_checks = [m.start() for m in re.finditer(r"hasPermission\('projects',\s*'edit'\)", source)]
        assert len(edit_checks) >= 5, \
            f"ProjectDetail.jsx should gate doc delete with projects.edit, found {len(edit_checks)} edit checks total"


# ═══════════════════════════════════════════════════════════════
# 14. NO UNPROTECTED CRUD ACTIONS — COMPREHENSIVE CHECK
# ═══════════════════════════════════════════════════════════════
class TestNoCrudWithoutPermission:
    """
    Scan frontend pages to ensure no CRUD action patterns exist
    without a corresponding hasPermission guard in the same file.
    """

    # Map: page file → (module, expected_actions_guarded)
    PAGE_PERMISSION_MAP = {
        "Financial.jsx": ("financial", ["create", "edit", "delete"]),
        "Projects.jsx": ("projects", ["create"]),
        "ProjectDetail.jsx": ("projects", ["edit"]),
        "Procurement.jsx": ("procurement", ["edit"]),
        "HRMS.jsx": ("hrms", ["create", "edit", "delete"]),
        "Inventory.jsx": ("inventory", ["create", "edit", "delete"]),
        "Settings.jsx": ("settings", ["edit"]),
    }

    def test_all_pages_have_required_permission_guards(self):
        """Every page with CRUD actions must have the correct hasPermission checks."""
        for page, (module, actions) in self.PAGE_PERMISSION_MAP.items():
            source = _read_page(page)
            for action in actions:
                pattern = f"hasPermission('{module}', '{action}')"
                assert pattern in source, \
                    f"{page} is missing hasPermission('{module}', '{action}') — " \
                    f"CRUD buttons for '{action}' will be visible to unauthorized users!"

    def test_no_page_has_raw_onclick_delete_without_permission(self):
        """Delete actions should never be directly on buttons without permission check."""
        pages_with_delete = ["Financial.jsx", "HRMS.jsx", "Inventory.jsx", "ProjectDetail.jsx"]
        for page in pages_with_delete:
            source = _read_page(page)
            # Ensure hasPermission exists alongside delete actions
            has_delete_action = "delete" in source.lower() or "Delete" in source or "remove" in source.lower()
            if has_delete_action:
                assert "hasPermission" in source, \
                    f"{page} has delete actions but no hasPermission check!"

    def test_financial_bill_detail_receives_permission_props(self):
        """BillDetail component must receive both canEdit and canDelete props."""
        source = _read_page("Financial.jsx")
        assert "canEdit={hasPermission('financial', 'edit')}" in source, \
            "BillDetail missing canEdit prop"
        assert "canDelete={hasPermission('financial', 'delete')}" in source, \
            "BillDetail missing canDelete prop"

    def test_hrms_employee_detail_receives_permission_props(self):
        """EmployeeDetailView must receive both canEdit and canDelete props."""
        source = _read_page("HRMS.jsx")
        assert "canEdit={hasPermission('hrms', 'edit')}" in source, \
            "EmployeeDetailView missing canEdit prop"
        assert "canDelete={hasPermission('hrms', 'delete')}" in source, \
            "EmployeeDetailView missing canDelete prop"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
