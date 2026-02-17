import os
from cryptography.fernet import Fernet
from config import ROOT_DIR
from dotenv import load_dotenv

load_dotenv(ROOT_DIR / '.env')

FERNET_KEY = os.environ.get('FERNET_KEY', Fernet.generate_key().decode())
fernet = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)


def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    return fernet.decrypt(value.encode()).decode()
