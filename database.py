import os
from motor.motor_asyncio import AsyncIOMotorClient
from config import ROOT_DIR
from dotenv import load_dotenv

load_dotenv(ROOT_DIR / '.env')

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
