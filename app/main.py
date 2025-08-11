from fastapi import FastAPI , Request , status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi # Import this function
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError # Import the specific MongoDB error base class
import logging # For logging errors
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.mongodb import connect_to_mongo,close_mongo_connection
from app.api.v1.endpoints import user_router , organization_router , doc_router , auth_router , search_router , qa_router

# Configure logging
logging.basicConfig(level=logging.ERROR) # Set desired logging level
logger = logging.getLogger(__name__)



# Lifespan event handler for FastAPI application.
# Handles startup and shutdown events.
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await connect_to_mongo()
        print("✅ MongoDB connection established")
        
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        logger.error(f"Startup error: {e}")
        raise

    yield # This separates startup from shutdown
    # Shutdown
    print("🛑 Application shutdown: Closing connections...")
    try:
        await close_mongo_connection()
        print("✅ MongoDB connection closed")
        
        
    except Exception as e:
        print(f"❌ Shutdown error: {e}")
        logger.error(f"Shutdown error: {e}")

app = FastAPI(
    title=settings.APP_NAME,
    description="This is a RAG application.",    
    version=settings.APP_VERSION,
    lifespan=lifespan  # Pass the lifespan function
)

origins = [
    "http://localhost:5173",  # for React frontend on local
    "https://org-rag.netlify.app",
]

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # or ["*"] to allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- FAST Lifecycle Events Handlers---
# @app.on_event("startup")
# async def startup_event():
#     print("Application startup event: Connecting to MongoDB...")
#     await connect_to_mongo()

# @app.on_event("shutdown")
# async def shutdown_event():
#     print("Application shutdown event: Closing MongoDB connection...")
#     await close_mongo_connection()

    # --- GLOBAL EXCEPTION HANDLERS ---

@app.exception_handler(PyMongoError)
async def mongo_exception_handler(request: Request, exc: PyMongoError):
    """
    Handles PyMongoError (all MongoDB-related exceptions).
    Returns a 500 Internal Server Error.
    """
    logger.error(f"MongoDB Error: {exc}", exc_info=True, extra={"request": request})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again later."},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handles any unhandled exception (catch-all).
    Returns a 500 Internal Server Error.
    """
    print(f"Unhandled Exception: {exc}")
    logger.error(f"Unhandled Exception: {exc}", exc_info=True, extra={"request": request})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred. Please try again later."},
    )

# --- END GLOBAL EXCEPTION HANDLERS ---

@app.get("/")
async def root():
    return {"message": "Welcome to the RAG Document Query API! Visit /docs for API documentation."}

# Include the user router
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(organization_router, prefix="/api/v1")
app.include_router(doc_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")  
app.include_router(qa_router, prefix="/api/v1")

