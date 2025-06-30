from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from typing import Optional

from ..core.config import settings

# Global variables to hold the client and database instances
client: Optional[AsyncMongoClient] = None
database: Optional[AsyncDatabase] = None # Use AsyncDatabase for type hinting

async def connect_to_mongo():
    global client, database

    try:
        client = AsyncMongoClient(settings.MONGO_URI)
        database = client[settings.MONGO_DB_NAME]
        print(f"Connected to MongoDB at {settings.MONGO_URI}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        client = None
        database = None

async def close_mongo_connection():
        global client
        if client:
             client.close()
             client = None
             print("MongoDB connection closed.")

async def get_database() -> AsyncDatabase:
    if database is None:
        raise ConnectionError("Database connection is not established.")
    return database