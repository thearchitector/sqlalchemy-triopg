import datetime
from typing import List

import pytest
import trio
from sqlalchemy import Column, ForeignKey, MetaData, String, Table, func, select
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    selectinload,
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class B(Base):
    __tablename__ = "b"
    id: Mapped[int] = mapped_column(primary_key=True)
    a_id: Mapped[int] = mapped_column(ForeignKey("a.id"))
    data: Mapped[str]


class A(Base):
    __tablename__ = "a"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[str]
    create_date: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    bs: Mapped[List[B]] = relationship()


async def test_core(setup_engine):
    # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-core

    meta = MetaData()
    t1 = Table("t1", meta, Column("name", String(50), primary_key=True))

    engine = await setup_engine(meta)

    async with engine.begin() as conn:
        await conn.execute(
            t1.insert(), [{"name": "some name 1"}, {"name": "some name 2"}]
        )

    async with engine.connect() as conn:
        result = await conn.execute(select(t1).where(t1.c.name == "some name 1"))

        assert result.fetchall() == [("some name 1",)]


async def test_orm(setup_engine):
    # https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#synopsis-orm

    engine = await setup_engine(Base.metadata)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            session.add_all(
                [
                    A(bs=[B(data="a1b1"), B(data="a1b2")], data="a1"),
                    A(bs=[], data="a2"),
                    A(bs=[B(data="a3b1"), B(data="a3b2")], data="a3"),
                ]
            )

    async with async_session() as session:
        stmt = select(A).options(selectinload(A.bs))
        result = await session.execute(stmt)

        for i, a in enumerate(result.scalars(), start=1):
            assert a.data == f"a{i}"
            assert a.create_date

            for j, b1 in enumerate(a.bs, start=1):
                assert b1.data == f"a{i}b{j}"

        result = await session.execute(select(A).order_by(A.id).limit(1))
        a1 = result.scalars().one()
        a1.data = "new data"
        await session.commit()

        assert a1.data == "new data"

        for j, b in enumerate(await a1.awaitable_attrs.bs, start=1):
            assert b.data == f"a1b{j}"


@pytest.mark.parametrize("isolated", (True, False), ids=("isolated", "persisted"))
async def test_concurrency(setup_engine, isolated):
    engine = await setup_engine(Base.metadata, from_scratch=isolated)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async def _load():
        async with async_session() as session:
            stmt = select(B)
            return (await session.scalars(stmt)).all()

    async with trio.open_nursery() as nursery:
        nursery.start_soon(_load)
        nursery.start_soon(_load)
        nursery.start_soon(_load)
