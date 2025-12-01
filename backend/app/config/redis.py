"""Redis configuration and connection management."""
from redis import Redis
from typing import Optional
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("redis")

# Global Redis connection
_redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    """Get synchronous Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=settings.REDIS_DECODE_RESPONSES,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            _redis_client.ping()
            logger.info(f"Redis connection established: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    return _redis_client


async def close_redis():
    """Close Redis connections."""
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
            _redis_client = None
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}", exc_info=True)

