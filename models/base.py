# models/base.py
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from database.config import async_session_maker

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
