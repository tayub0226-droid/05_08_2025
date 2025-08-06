"""
Base model and database configuration.
"""
from database.database import Base, async_session as async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
import os
from pathlib import Path

# Dependency to get DB session
async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
