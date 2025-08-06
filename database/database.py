# database/database.py
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import load_dotenv

from database.config import engine, async_session_maker
from models.base import Base  # ✅ use Base from base.py
from models.user import User
from models.quote import Quote
from models.chat import ChatSessionORM
from models.interaction import QuoteInteractionORM

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Main database management class with all database operations."""

    @staticmethod
    async def test_connection() -> bool:
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("✅ Database connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    @staticmethod
    async def create_tables() -> bool:
        logger.info("Creating database tables...")
        try:
            async with engine.begin() as conn:
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ All tables created successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False

    @staticmethod
    async def drop_tables() -> bool:
        logger.info("Dropping all tables...")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("✅ All tables dropped successfully")
                return True
        except Exception as e:
            logger.error(f"❌ Error dropping tables: {e}")
            return False

    @staticmethod
    async def reset_database() -> bool:
        if await DatabaseManager.drop_tables():
            return await DatabaseManager.create_tables()
        return False

    @staticmethod
    async def get_table_info() -> Dict[str, Any]:
        result = {"tables": [], "record_counts": {}}
        try:
            async with engine.begin() as conn:
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                result["tables"] = tables
                for table in tables:
                    count_result = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                    result["record_counts"][table] = count_result.scalar()
                return result
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            return {"error": str(e)}

    @classmethod
    async def get_session(cls) -> AsyncSession:
        return async_session_maker()

    @classmethod
    async def execute_query(cls, query: str, params: Optional[Dict] = None) -> List[Tuple]:
        async with async_session_maker() as session:
            try:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result.fetchall()
            except Exception as e:
                await session.rollback()
                logger.error(f"Error executing query: {e}")
                raise

# CLI for database management
async def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Database management utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    subparsers.add_parser("test", help="Test database connection")
    subparsers.add_parser("create", help="Create all database tables")
    subparsers.add_parser("drop", help="Drop all database tables")
    subparsers.add_parser("reset", help="Reset database (drop + create)")
    subparsers.add_parser("info", help="Show database information")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "test":
            await DatabaseManager.test_connection()
        elif args.command == "create":
            await DatabaseManager.create_tables()
        elif args.command == "drop":
            confirm = input("Are you sure you want to drop all tables? (yes/no): ")
            if confirm.lower() == "yes":
                await DatabaseManager.drop_tables()
        elif args.command == "reset":
            confirm = input("Are you sure you want to reset the database? (yes/no): ")
            if confirm.lower() == "yes":
                await DatabaseManager.reset_database()
        elif args.command == "info":
            info = await DatabaseManager.get_table_info()
            print(info)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
