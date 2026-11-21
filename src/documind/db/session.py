from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from documind.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def set_workspace_rls(session: AsyncSession, workspace_id: str) -> None:
    """Sets PostgreSQL transaction-local setting for Row-Level Security isolation."""
    from sqlalchemy import text
    await session.execute(text(f"SET LOCAL app.workspace_id = '{workspace_id}';"))
