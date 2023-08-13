# sqlalchemy-triopg

![PyPI - Downloads](https://raster.shields.io/pypi/dw/sqlalchemy-triopg?style=flat-square)
![GitHub](https://raster.shields.io/github/license/thearchitector/sqlalchemy-triopg?style=flat-square)
[![Buy a tree](https://raster.shields.io/badge/Treeware-%F0%9F%8C%B3-lightgreen?style=flat-square)](https://ecologi.com/eliasgabriel?r=6128126916bfab8bd051026c)

A thin Trio-backed wrapper for SQLAlchemy's asyncpg PostgreSQL driver.

This wrapper is named after the existing raw asyncpg wrapper [triopg](https://github.com/python-trio/triopg), but does not actually use it. If you want to use asyncpg directly, use that package instead.

```sh
$ pdm add sqlalchemy-triopg
# or
$ pip install --user sqlalchemy-triopg
```

## Usage

SQLAlchemy is able to automatically discover the dialect available through this package as soon as you install it. When creating your engine, just pass the `triopg` driver like so:

```python
engine = create_async_engine("triopg://postgres:password@db/postgres")
```

### Requisites

This package uses the [trio-asyncio](https://trio-asyncio.readthedocs.io/en/latest/index.html) package to provide a compatibility layer with asyncio; it is what enables the "wrapping" in favor of just a re-implementation. However it also means that your program needs to ensure the Trio event loop is running, either via manually calling your program with `trio_asyncio.run` or by wrapping your main coroutine definition in `trio_asyncio.open_loop`.

For many projects like web apps, the terminal command for starting the application does not let you change how to start the ASGI server. Aside from creating a custom worker class and specifying it (like a custom Hypercorn or Gunicorn worker), you'll need to create a bootstrapping script where you can manually call `trio_asyncio.run` to your server's API.

This is because, unfortunately, binding an async context manager to the lifecycle of your application (a feature supported by both [BlackSheep](https://www.neoteroi.dev/blacksheep/application/#using-the-lifespan-decorator) and [FastAPI](https://fastapi.tiangolo.com/advanced/events/#lifespan)) in which you call `trio_asyncio.open_loop` doesn't seem to work.

Using [Hypercorn's API](https://pgjones.gitlab.io/hypercorn/how_to_guides/api_usage.html#api-usage), an example `boot.py` script could look like this:

```python
#!/bin/python

import trio_asyncio
from hypercorn.config import Config
from hypercorn.trio import serve

from application import app

if __name__ == "__main__":
    trio_asyncio.run(serve, app, Config.from_toml("application.toml"))
```

### Considerations

This package uses trio-asyncio, and you'll need to take that into account if you're combining Trio and existing asyncio tooling. If those tools do not use a bridge library like [anyio](https://anyio.readthedocs.io/en/stable/index.html), it's very likely that you'll need to extend them the coroutines by wrapping them in `trio_asyncio.aio_as_trio` (or using it as a decorator on your own coroutine functions).

This is an [intentional anti-feature of trio-asyncio](https://trio-asyncio.readthedocs.io/en/latest/principles.html).

## License

This package makes use of SQLAlchemy and Trio-Asyncio, both of which are licensed under MIT.

This package is licensed under the [BSD 3-Clause Clear License](LICENSE).

This package is [Treeware](https://treeware.earth). If you use it in production, consider [**buying the world a tree**](https://ecologi.com/eliasgabriel?r=6128126916bfab8bd051026c) to thank me for my work. By contributing to my forest, you’ll be creating employment for local families and restoring wildlife habitats.
