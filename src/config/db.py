import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger("orm")


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(db_url, future=True, echo=True)
        self._session_factory = async_scoped_session(
            async_sessionmaker(
                class_=AsyncSession,
                autocommit=False,
                autoflush=True,
                bind=self._engine,
            ),
            scopefunc=asyncio.current_task,
        )

    def create_database(self) -> None:
        Base.metadata.create_all(self._engine)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        session: AsyncSession = self._session_factory()
        try:
            print("YIELDING...")
            yield session
        except Exception as e:
            print("ROLLBACKING... ")
            await session.rollback()
            print("ERROR... ", str(e))
            logger.error(
                f"Session rollback because of exception - {str(e)}", exc_info=e
            )
            raise
        else:
            print("COMMITTING... ")
            try:
                await session.commit()
            except SQLAlchemyError as e:
                print("ERROR COMMITTING...", str(e))
                await session.rollback()
                logger.error(
                    f"Session rollback because of exception on commit - {str(e)}",
                    exc_info=e,
                )
        finally:
            print("CLOSING... ")
            await session.close()
