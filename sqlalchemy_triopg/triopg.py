import asyncio
from typing import Any, Awaitable, Type, TypeVar

import trio
import trio_asyncio  # type: ignore
from sqlalchemy.dialects.postgresql import asyncpg
from sqlalchemy.util import await_fallback, await_only

_T = TypeVar("_T")


class TrioPGConnection(asyncpg.AsyncAdapt_asyncpg_connection):
    """await utility override of an asyncpg connection."""

    @staticmethod
    def await_(aio_coroutine: Awaitable[_T]) -> _T:  # type: ignore[override]
        res: _T = await_only(trio_asyncio.aio_as_trio(aio_coroutine))
        return res

    @classmethod
    def factory(cls, dbapi: "TrioPGDBAPI", *arg: Any, **kw: Any) -> "TrioPGConnection":
        creator_fn = kw.pop("async_creator_fn", dbapi.asyncpg.connect)
        prepared_statement_cache_size: int = kw.pop(
            "prepared_statement_cache_size", 100
        )
        prepared_statement_name_func = kw.pop("prepared_statement_name_func", None)

        return cls(
            dbapi,
            cls.await_(creator_fn(*arg, **kw)),
            prepared_statement_cache_size=prepared_statement_cache_size,
            prepared_statement_name_func=prepared_statement_name_func,
        )


class TrioPGFallbackConnection(TrioPGConnection):
    """await utility override of an asyncpg fallback connection."""

    __slots__ = ()

    @staticmethod
    def await_(aio_coroutine: Awaitable[_T]) -> _T:  # type: ignore[override]
        res: _T = await_fallback(trio_asyncio.aio_as_trio(aio_coroutine))
        return res


class TrioPGDBAPI(asyncpg.AsyncAdapt_asyncpg_dbapi):
    """Provides a method for producing bridged connections."""

    def connect(self, *arg: Any, **kw: Any) -> TrioPGConnection:
        conn_proxy_cls: Type[TrioPGConnection] = (
            TrioPGFallbackConnection
            if kw.pop("async_fallback", False)
            else TrioPGConnection
        )

        return conn_proxy_cls.factory(self, *arg, **kw)


class TrioPGDialect(asyncpg.dialect):
    """The dialect driver for trio."""

    name: str = "triopg"
    driver: str = "asyncpg"
    supports_statement_cache: bool = True

    @classmethod
    def import_dbapi(cls) -> TrioPGDBAPI:  # type: ignore[override]
        """Use our subclassed dbapi."""
        return TrioPGDBAPI(__import__("asyncpg"))  # type: ignore[no-untyped-call]


# MONKEYPATCH SHIELDING


async def _shield(coro: Awaitable[_T]) -> _T:
    with trio.CancelScope(shield=True):
        return await coro


asyncio.create_task = lambda coro: coro  # type: ignore[assignment,misc]
asyncio.shield = _shield  # type: ignore[assignment]
