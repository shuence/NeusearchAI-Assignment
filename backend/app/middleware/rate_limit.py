"""Rate limiting middleware for API endpoints."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.utils.logger import get_logger

logger = get_logger("rate_limit_middleware")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations for different endpoints
RATE_LIMITS = {
    "default": "100/minute",  # General endpoints
    "chat": "10/minute",  # Chat endpoint - more restrictive
    "scrape": "5/hour",  # Scraping endpoint - very restrictive
    "products": "60/minute",  # Product listing - moderate
}


def get_rate_limit_for_path(path: str) -> str:
    """Get appropriate rate limit for a given path."""
    if "/chat" in path:
        return RATE_LIMITS["chat"]
    elif "/scrape" in path:
        return RATE_LIMITS["scrape"]
    elif "/products" in path:
        return RATE_LIMITS["products"]
    return RATE_LIMITS["default"]


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors."""
    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)} on {request.url.path}"
    )
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.retry_after,
            "request_id": getattr(request.state, "request_id", None),
        },
        headers={"Retry-After": str(exc.retry_after)},
    )

