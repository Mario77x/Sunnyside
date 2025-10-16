from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional

# This global variable will be set during app startup
_db: Optional[AsyncIOMotorDatabase] = None


def set_database_for_dependencies(db: AsyncIOMotorDatabase):
    """
    Call this function during the application startup to set the database
    instance that the dependency injector will use.
    """
    global _db
    _db = db


def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency function to get the database connection.
    """
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection not available. The app may not have started correctly.",
        )
    return _db