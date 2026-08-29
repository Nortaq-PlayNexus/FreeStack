"""
Database layer for FreeStack.

Provides async SQLAlchemy 2.0 session management with connection pooling,
migration support, and repository patterns.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Type, TypeVar

from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, declared_attr

from .config import settings


class Base(DeclarativeBase):
    """Base model class with common conventions."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        import re
        name = re.sub(r"([A-Z]+)", r"_\1", cls.__name__).strip("_").lower()
        return name


T = TypeVar("T", bound=Base)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self) -> None:
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def engine(self) -> AsyncEngine:
        """Get or create the async engine."""
        if self._engine is None:
            self._engine = create_async_engine(
                settings.database.url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                pool_timeout=settings.database.pool_timeout,
                pool_recycle=settings.database.pool_recycle,
                pool_pre_ping=settings.database.pool_pre_ping,
                echo=settings.database.echo,
                echo_pool=settings.database.echo_pool,
            )
            self._setup_engine_events()
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the session factory."""
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
            )
        return self._session_factory

    def _setup_engine_events(self) -> None:
        """Set up engine-level event listeners."""

        @event.listens_for(self.engine.sync_engine, "connect")
        def set_postgresql_search_path(dbapi_connection, connection_record):
            """Set search path on new connections."""
            cursor = dbapi_connection.cursor()
            cursor.execute("SET search_path TO public")
            cursor.close()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional scope for a series of operations."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """FastAPI dependency for getting a database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def init_db(self) -> None:
        """Initialize database - create all tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close all connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
            return True
        except Exception:
            return False


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with db_manager.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database on application startup."""
    await db_manager.init_db()


async def close_db() -> None:
    """Close database connections on application shutdown."""
    await db_manager.close()


class BaseRepository:
    """Base repository class with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[T]) -> None:
        self.session = session
        self.model = model

    async def get(self, id: Any) -> Optional[T]:
        """Get entity by ID."""
        return await self.session.get(self.model, id)

    async def get_by(self, **kwargs) -> Optional[T]:
        """Get entity by arbitrary filter."""
        from sqlalchemy import select
        stmt = select(self.model).filter_by(**kwargs)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        **filters
    ) -> list[T]:
        """List entities with pagination and filtering."""
        from sqlalchemy import select
        stmt = select(self.model).filter_by(**filters)

        if order_by:
            stmt = stmt.order_by(order_by)

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **filters) -> int:
        """Count entities matching filters."""
        from sqlalchemy import select, func
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs) -> T:
        """Create new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, id: Any, **kwargs) -> Optional[T]:
        """Update entity by ID."""
        entity = await self.get(id)
        if entity is None:
            return None
        for key, value in kwargs.items():
            setattr(entity, key, value)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: Any) -> bool:
        """Delete entity by ID."""
        entity = await self.get(id)
        if entity is None:
            return False
        await self.session.delete(entity)
        await self.session.flush()
        return True

    async def exists(self, **filters) -> bool:
        """Check if entity exists."""
        from sqlalchemy import select, exists
        stmt = select(exists().where(*[
            getattr(self.model, k) == v for k, v in filters.items()
        ]))
        result = await self.session.execute(stmt)
        return result.scalar_one()


def get_repository(model: Type[T]) -> type[BaseRepository]:
    """Factory for creating repository classes."""
    class ModelRepository(BaseRepository):
        def __init__(self, session: AsyncSession) -> None:
            super().__init__(session, model)

    return ModelRepository