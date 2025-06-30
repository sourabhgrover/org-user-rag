from fastapi import FastAPI
from app.core.config import settings
from app.db.mongodb import connect_to_mongo,close_mongo_connection
app = FastAPI(
    title=settings.APP_NAME,
    description="This is a sample FastAPI application.",    
    version=settings.APP_VERSION,
)
# --- FAST Lifecycle Events Handlers---
@app.on_event("startup")
async def startup_event():
    print("Application startup event: Connecting to MongoDB...")
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown event: Closing MongoDB connection...")
    await close_mongo_connection()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}