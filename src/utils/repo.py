from abc import ABC, abstractmethod
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Type, TypeVar

from _typeshed import DataclassInstance
from sqlalchemy import Column, Result, Select, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.db import Base
from utils.decorators import handle_orm_error
from utils.shortcuts import get_object_or_404

T = TypeVar("T", bound=Base)
if TYPE_CHECKING:
    D = TypeVar("D", bound=DataclassInstance)
else:
    D = TypeVar("D")


class IRepo(ABC, Generic[T]):
    @abstractmethod
    def all_as_select(self) -> Select[T]: ...

    @abstractmethod
    async def all(self, session: AsyncSession) -> Result[T]: ...

    @abstractmethod
    async def get_by_id(
        self, session: AsyncSession, id_: int, *, for_update: bool = False
    ) -> T: ...

    @abstractmethod
    async def get_by_ids(
        self, session: AsyncSession, ids: List[int], *, for_update: bool = False
    ) -> Select[T]: ...

    @abstractmethod
    async def get_by_field(
        self, session: AsyncSession, field: str, value: Any, *, for_update: bool = False
    ) -> T: ...

    @abstractmethod
    async def create(self, session: AsyncSession, entry: D) -> T: ...

    @abstractmethod
    async def update(
        self, session: AsyncSession, instance: T, values: Dict
    ) -> None: ...

    @abstractmethod
    async def multi_update(
        self, session: AsyncSession, ids: List[int], *, values: Dict[str, Any]
    ) -> None: ...

    @abstractmethod
    async def delete(self, session: AsyncSession, instance: T) -> None: ...

    @abstractmethod
    async def delete_by_field(
        self, session: AsyncSession, field: str, value: Any
    ) -> None: ...


class Repo(IRepo[T]):
    def __init__(self, model_class: Type[T], pk_field: str) -> None:
        self.model_class = model_class
        self.pk_field = pk_field

        assert hasattr(self.model_class, self.pk_field), "Wrong pk_field"

    @property
    def pk(self) -> Column:
        return getattr(self.model_class, self.pk_field)

    def all_as_select(self) -> Select[T]:
        return select(self.model_class)

    @handle_orm_error
    async def all(self, session: AsyncSession) -> Result[T]:
        return await session.execute(self.all_as_select())

    @handle_orm_error
    async def get_by_id(
        self, session: AsyncSession, id_: int, *, for_update: bool = False
    ) -> T:
        qs = self.all_as_select().filter(self.pk == id_)
        if for_update:
            qs = qs.with_for_update()
        result = await session.execute(qs)
        return get_object_or_404(result.first())

    @handle_orm_error
    async def get_by_ids(
        self, session: AsyncSession, ids: List[int], *, for_update: bool = False
    ) -> Select[T]:
        qs = self.all_as_select().filter(self.pk.in_(ids))
        if for_update:
            qs = qs.with_for_update()
        result = await session.execute(qs)
        return get_object_or_404(result.first())

    @handle_orm_error
    async def get_by_field(
        self, session: AsyncSession, field: str, value: Any, *, for_update: bool = False
    ) -> T:
        qs = self.all_as_select().filter(getattr(self.model_class, field) == value)
        if for_update:
            qs = qs.with_for_update()
        result = await session.execute(qs)
        return get_object_or_404(result.first())

    @handle_orm_error
    async def create(self, session: AsyncSession, entry: D) -> T:
        instance = self.model_class(**asdict(entry))
        session.add(instance)
        await session.flush([instance])
        await session.refresh(instance)
        return instance

    @handle_orm_error
    async def update(self, session: AsyncSession, instance: T, values: Dict) -> None:
        await session.execute(
            update(self.model_class)
            .filter(self.pk == getattr(instance, self.pk_field))
            .values(**values)
        )

    @handle_orm_error
    async def multi_update(
        self, session: AsyncSession, ids: List[int], *, values: Dict[str, Any]
    ) -> None:
        await session.execute(
            update(self.model_class).filter(self.pk.in_(ids)).values(**values)
        )

    @handle_orm_error
    async def delete(self, session: AsyncSession, instance: T) -> None:
        await session.execute(
            delete(self.model_class).filter(self.pk == getattr(instance, self.pk_field))
        )

    @handle_orm_error
    async def delete_by_field(
        self, session: AsyncSession, field: str, value: Any
    ) -> None:
        await session.execute(
            delete(self.model_class).filter(getattr(self.model_class, field) == value)
        )
