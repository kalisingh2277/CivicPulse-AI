from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.core.config import get_settings

settings = get_settings()


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.redis_url)


_pool: ArqRedis | None = None


async def enqueue_process_complaint(complaint_id: str) -> None:
    global _pool
    if _pool is None:
        _pool = await create_pool(redis_settings())
    await _pool.enqueue_job("process_complaint", str(complaint_id))
