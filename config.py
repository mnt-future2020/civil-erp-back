from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'civil_erp_secret_key')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# RBAC Constants
MODULES = [
    "dashboard", "projects", "financial", "procurement",
    "hrms", "compliance", "einvoicing", "reports",
    "ai_assistant", "settings", "inventory"
]
PERMISSION_TYPES = ["view", "create", "edit", "delete"]

# File Upload
UPLOAD_DIR = ROOT_DIR / "uploads"
EXPORT_DIR = ROOT_DIR / "exports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.webp', '.dwg', '.dxf', '.doc', '.docx', '.xls', '.xlsx'}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
