import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from app.core.config import settings


def _sqlite_path(url: str) -> str | None:
    """Extract the SQLite file path from an aiosqlite URL, or None if not sqlite."""
    if "sqlite" not in url:
        return None
    # Examples:
    #   sqlite+aiosqlite:///./data/data.db
    #   sqlite+aiosqlite:///:memory:
    #   sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true
    if ":memory:" in url or "mode=memory" in url:
        return None
    try:
        path = url.split("///", 1)[1]
        # strip query string
        path = path.split("?", 1)[0]
        return path
    except IndexError:
        return None


sqlite_path = _sqlite_path(settings.DATABASE_URL)
if sqlite_path:
    os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)) or ".", exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=False,
)

# Enable WAL mode on SQLite connections for safer concurrent reads/writes.
if "sqlite" in settings.DATABASE_URL and settings.SQLITE_WAL_MODE:

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_wal(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.execute("PRAGMA busy_timeout=5000;")
            cursor.close()
        except Exception:
            # Non-SQLite or in-memory: ignore silently.
            pass


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
