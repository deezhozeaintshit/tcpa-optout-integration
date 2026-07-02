import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.database import get_db, Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"

@pytest.fixture
def anyio_backend():
    """Specify the backend for AnyIO tests."""
    return "asyncio"

@pytest.fixture
async def db_session():
    """Creates a clean, in-memory SQLite database instance for each test run."""
    engine = create_async_engine(
        TEST_DATABASE_URL, 
        connect_args={"check_same_thread": False, "uri": True}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Temporarily override worker's session maker to use test database
    from app.core import worker
    original_session_maker = worker.AsyncSessionLocal
    worker.AsyncSessionLocal = AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
        
    worker.AsyncSessionLocal = original_session_maker
    await engine.dispose()

@pytest.fixture
async def client(db_session):
    """Overrides the dependency injection for the DB session and yields an ASGI HTTP test client."""
    async def override_get_db():
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()
