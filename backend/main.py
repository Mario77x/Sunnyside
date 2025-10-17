from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from backend.utils.environment import load_secrets_from_mongodb
from backend.dependencies import set_database_for_dependencies

# Load environment variables from .env file first
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "sunnyside")

# Validate required environment variables
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is required but not set")

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
        
        # Load secrets from MongoDB
        await load_secrets_from_mongodb(mongodb_client, DATABASE_NAME)
        
        # Set the database for the dependency injector
        set_database_for_dependencies(database)
        
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
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5137").split(",")
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


# API v1 router
from fastapi import APIRouter
from backend.routes.auth import router as auth_router
from backend.routes.activities import router as activities_router
from backend.routes.invites import router as invites_router
from backend.routes.weather import router as weather_router
from backend.routes.llm import router as llm_router
from backend.routes.notifications import router as notifications_router
from backend.routes.contacts import router as contacts_router
from backend.routes.users import router as users_router
from backend.routes.deadlines import router as deadlines_router
from backend.routes.calendar import router as calendar_router

api_v1_router = APIRouter(prefix="/api/v1")

# Health check endpoint for API v1
@api_v1_router.get("/health")
async def api_v1_health_check():
    """
    API v1 health check endpoint that returns a simple status.
    """
    return {"status": "ok"}

# Include routers
api_v1_router.include_router(auth_router)
api_v1_router.include_router(activities_router)
api_v1_router.include_router(invites_router)
api_v1_router.include_router(weather_router)
api_v1_router.include_router(llm_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(contacts_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(deadlines_router)
api_v1_router.include_router(calendar_router)
app.include_router(api_v1_router)


# Root endpoint
@app.get("/")
async def root():
    return {"message": "Sunnyside API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)