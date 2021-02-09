from injector import provider, singleton
from redis import Redis, ConnectionPool
from flask.config import Config
from ._helpers import FytdlModule


class RedisModule(FytdlModule):
    @provider
    @singleton
    def provide_redis_pool(self, config: Config) -> ConnectionPool:
        return ConnectionPool(config["REDIS_URL"], db=config["REDIS_DATABASE"])

    @provider
    def provide_redis(self, pool: ConnectionPool) -> Redis:
        return Redis(connection_pool=pool)
