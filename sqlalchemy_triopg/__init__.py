from sqlalchemy.dialects import registry as _registry

_registry.register("triopg", "sqlalchemy_triopg.triopg", "TrioPGDialect")
