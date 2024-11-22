from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import Column, Result, Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import Base, Database
from utils.decorators import handle_orm_error
from utils.shortcuts import get_object_or_404

TModel = TypeVar("TModel", bound=Base)
TSchema = TypeVar("TSchema", bound=BaseModel)


class IRepo(ABC, Generic[TModel]):
    @abstractmethod
    def all_as_select(self) -> Select[TModel]: ...
    @abstractmethod
    async def all(self, *, session: AsyncSession) -> Result[TModel]: ...
    @abstractmethod
    async def get_by_id(
        self,
        id_: int,
        *,
        for_update: bool = False,
        session: AsyncSession,
    ) -> TModel: ...
    @abstractmethod
    async def get_by_ids(
        self,
        ids: List[int],
        *,
        for_update: bool = False,
        session: AsyncSession,
    ) -> Select[TModel]: ...
    @abstractmethod
    async def get_by_field(
        self,
        field: str,
        value: Any,
        *,
        for_update: bool = False,
        session: AsyncSession,
    ) -> TModel: ...
    @abstractmethod
    async def exists_by_field(
        self,
        field: str,
        value: Any,
        *,
        session: AsyncSession,
    ) -> bool: ...
    @abstractmethod
    async def create(
        self,
        entry: TSchema,
        *,
        session: AsyncSession,
    ) -> TModel: ...
    @abstractmethod
    async def update(
        self,
        instance: TModel,
        values: Dict,
        *,
        session: AsyncSession,
    ) -> None: ...
    @abstractmethod
    async def multi_update(
        self,
        ids: List[int],
        *,
        values: Dict[str, Any],
        session: AsyncSession,
    ) -> None: ...
    @abstractmethod
    async def delete(
        self,
        instance: TModel,
        *,
        session: AsyncSession,
    ) -> None: ...
    @abstractmethod
    async def delete_by_field(
        self,
        field: str,
        value: Any,
        *,
        session: AsyncSession,
    ) -> None: ...


class Repo(IRepo[TModel]):
    def __init__(self, db: Database, model_class: Type[TModel], pk_field: str) -> None:
        self.session_factory = db.session
        self.model_class = model_class
        self.pk_field = pk_field

        assert hasattr(self.model_class, self.pk_field), "Wrong pk_field"

    @property
    def pk(self) -> Column:
        return getattr(self.model_class, self.pk_field)

    def all_as_select(self) -> Select[TModel]:
        return select(self.model_class)

    @handle_orm_error
    async def all(self, *, session: AsyncSession) -> Result[TModel]:
        return await session.execute(self.all_as_select())

    @handle_orm_error
    async def get_by_id(
        self,
        id_: int,
        *,
        for_update: bool = False,
        session: AsyncSession,
    ) -> TModel:
        qs = self.all_as_select().filter(self.pk == id_)
        if for_update:
            qs = qs.with_for_update()
        result = await session.execute(qs)
        first = result.first()
        return get_object_or_404(first[0] if first else None)

    @handle_orm_error
    async def get_by_ids(
        self,
        ids: List[int],
        *,
        for_update: bool = False,
        session: AsyncSession,
    ) -> Select[TModel]:
        qs = self.all_as_select().filter(self.pk.in_(ids))
        if for_update:
            qs = qs.with_for_update()
        result = await session.execute(qs)
        first = result.first()
        return get_object_or_404(first[0] if first else None)

    @handle_orm_error
    async def get_by_field(
        self,
        field: str,
        value: Any,
        *,
        for_update: bool = False,
        session: AsyncSession,
    ) -> TModel:
        qs = self.all_as_select().filter(getattr(self.model_class, field) == value)
        if for_update:
            qs = qs.with_for_update()
        result = await session.execute(qs)
        first = result.first()
        return get_object_or_404(first[0] if first else None)

    @handle_orm_error
    async def exists_by_field(
        self, field: str, value: Any, *, session: AsyncSession
    ) -> bool:
        qs = (
            self.all_as_select()
            .filter(getattr(self.model_class, field) == value)
            .limit(1)
        )
        result = await session.execute(qs)
        return result.first() is not None

    @handle_orm_error
    async def create(
        self,
        entry: TSchema,
        *,
        session: AsyncSession,
    ) -> TModel:
        instance = self.model_class(**entry.model_dump())
        session.add(instance)
        await session.flush([instance])
        await session.refresh(instance)
        return instance

    @handle_orm_error
    async def update(
        self,
        instance: TModel,
        values: Dict,
        *,
        session: AsyncSession,
    ) -> None:
        await session.execute(
            update(self.model_class)
            .filter(self.pk == getattr(instance, self.pk_field))
            .values(**values)
        )

    @handle_orm_error
    async def multi_update(
        self,
        ids: List[int],
        *,
        values: Dict[str, Any],
        session: AsyncSession,
    ) -> None:
        await session.execute(
            update(self.model_class).filter(self.pk.in_(ids)).values(**values)
        )

    @handle_orm_error
    async def delete(
        self,
        instance: TModel,
        *,
        session: AsyncSession,
    ) -> None:
        await session.execute(
            delete(self.model_class).filter(self.pk == getattr(instance, self.pk_field))
        )

    @handle_orm_error
    async def delete_by_field(
        self,
        field: str,
        value: Any,
        *,
        session: AsyncSession,
    ) -> None:
        await session.execute(
            delete(self.model_class).filter(getattr(self.model_class, field) == value)
        )
