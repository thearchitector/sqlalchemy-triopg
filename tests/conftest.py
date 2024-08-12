import os

import pytest
import trio_asyncio
from sqlalchemy.dialects import registry
from sqlalchemy.ext.asyncio import create_async_engine

registry.register("triopg", "sqlalchemy_triopg.triopg", "TrioPGDialect")

POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")


@pytest.fixture
async def setup_engine():
    engine = None

    async def _(meta, from_scratch=True):
        nonlocal engine
        engine = create_async_engine(
            f"triopg://postgres:password@{POSTGRES_HOST}/postgres", echo=False
        )

        if from_scratch:
            async with engine.begin() as conn:
                await conn.run_sync(meta.drop_all)
                await conn.run_sync(meta.create_all)

        return engine

    async with trio_asyncio.open_loop():
        try:
            yield _
        finally:
            await engine.dispose()
