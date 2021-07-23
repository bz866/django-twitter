import redis
from twitter import settings


class RedisClient:
    """
    Build connection between Redis and Django
    """
    conn = None

    @classmethod
    def get_connection(cls):
        # Singleton alike connection initialization
        # assure Django calls one single global connection for Redis
        if cls.conn is not None:
            return cls.conn
        cls.conn = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
        )
        return cls.conn

    @classmethod
    def clear(cls):
        if not settings.TESTING:
            raise Exception(
                'You can not flush Redis in a production environment.'
            )
        conn = cls.get_connection()
        conn.flushdb()
