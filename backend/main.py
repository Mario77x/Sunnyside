from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://sunnyside_db_user:GCWkLShMGwJtwNTD@cluster0.rskmhym.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = "sunnyside"

# Global variables for database connection
mongodb_client: AsyncIOMotorClient = None
database = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client, database
    mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    database = mongodb_client[DATABASE_NAME]
    
    # Test the connection
    try:
        await mongodb_client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
    
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Sunnyside API",
    description="Backend API for Sunnyside social planning application",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/healthz")
async def health_check():
    """
    Health check endpoint that verifies API and database connectivity.
    """
    try:
        # Test database connection
        await mongodb_client.admin.command('ping')
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "ok",
        "db_status": db_status
    }


def get_database_connection():
    """Get the database connection."""
    return database


# API v1 router
from fastapi import APIRouter
from backend.routes.auth import router as auth_router
from backend.routes.activities import router as activities_router
from backend.routes.invites import router as invites_router

api_v1_router = APIRouter(prefix="/api/v1")

# Include routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(activities_router)
api_v1_router.include_router(invites_router)
app.include_router(api_v1_router)


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Sunnyside API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)