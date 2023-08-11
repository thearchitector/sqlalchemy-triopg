# sqlalchemy-triopg

A thin Trio-backed wrapper for SQLAlchemy's asyncpg PostgreSQL driver.

This wrapper is named after the existing raw asyncpg wrapper [triopg](https://github.com/python-trio/triopg), but does not actually use it.

## Usage

SQLAlchemy is able to automatically discover the dialect available through this package as soon as you install it.

When creating your engine, just pass the `triopg` driver like so:

```python
engine = create_async_engine(
    "postgresql+triopg://postgres:password@db/postgres"
)
```

### Environment

This package uses the [trio-asyncio](https://trio-asyncio.readthedocs.io/en/latest/index.html) package to provide a compatibility layer with asyncio; it is what enables the "wrapping" in favor of just a re-implementation. However it also means that your program needs to ensure the Trio event loop is running, either via manually calling your program with `trio_asyncio.run` or by wrapping your coroutine definition in `trio_asyncio.open_loop`.

For many projects like web apps, where you likely do not have direct access to starting the ASGI server (aside from creating a custom worker class), you should be able to bind an async context manager to the lifecycle of the application and make use of `trio_asyncio.open_loop`. Both [BlackSheep](https://www.neoteroi.dev/blacksheep/application/#using-the-lifespan-decorator) and [FastAPI](https://fastapi.tiangolo.com/advanced/events/#lifespan) let you do this in some shape or form:

```python
app = Application()

@app.lifespan
async def trio_asyncio_loop():
    async with trio_asyncio.open_loop() as loop:
        yield
```

If a generator isn't available to you to use, but you have control over a startup / shutdown events, you can manually enter and exit the manager. This is hacky and error prone though, so its really a "if you have no other options" solution:

```python
app = Application()
trio_loop = trio_asyncio.open_loop()

@app.on_start
async def start_loop(application: Application) -> None:
    await trio_loop.__aenter__()

@app.after_start
async def stop_loop(application: Application) -> None:
    # or collect the exce and stack trace and feed them in properly
    await trio_loop.__aexit__(None, None, None)
```
