"""Performance metrics middleware for request timing and monitoring."""
import time
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import get_logger

logger = get_logger("metrics_middleware")

# In-memory metrics storage (in production, use Redis or a proper metrics system)
_metrics: Dict[str, Any] = {
    "request_count": 0,
    "total_response_time": 0.0,
    "endpoint_times": {},
    "status_codes": {},
    "errors": 0,
}


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request metrics and performance."""
    
    async def dispatch(self, request: Request, call_next):
        """Track request metrics."""
        start_time = time.time()
        _metrics["request_count"] += 1
        
        # Track endpoint
        endpoint = request.url.path
        if endpoint not in _metrics["endpoint_times"]:
            _metrics["endpoint_times"][endpoint] = {
                "count": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
            }
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            _metrics["total_response_time"] += response_time
            
            # Track endpoint metrics
            endpoint_metrics = _metrics["endpoint_times"][endpoint]
            endpoint_metrics["count"] += 1
            endpoint_metrics["total_time"] += response_time
            endpoint_metrics["avg_time"] = endpoint_metrics["total_time"] / endpoint_metrics["count"]
            
            # Track status codes
            status_code = response.status_code
            status_group = f"{status_code // 100}xx"
            _metrics["status_codes"][status_group] = _metrics["status_codes"].get(status_group, 0) + 1
            
            # Track errors
            if status_code >= 400:
                _metrics["errors"] += 1
            
            # Add response time header
            response.headers["X-Response-Time"] = f"{response_time:.4f}s"
            
            return response
            
        except Exception as e:
            _metrics["errors"] += 1
            logger.error(f"Error in request: {e}")
            raise


def get_metrics() -> Dict[str, Any]:
    """Get current metrics."""
    request_count = _metrics["request_count"]
    avg_response_time = (
        _metrics["total_response_time"] / request_count
        if request_count > 0
        else 0.0
    )
    
    # Get top endpoints by request count
    top_endpoints = sorted(
        _metrics["endpoint_times"].items(),
        key=lambda x: x[1]["count"],
        reverse=True
    )[:10]
    
    return {
        "total_requests": request_count,
        "total_errors": _metrics["errors"],
        "average_response_time_seconds": round(avg_response_time, 4),
        "status_codes": _metrics["status_codes"],
        "top_endpoints": [
            {
                "endpoint": endpoint,
                "count": metrics["count"],
                "avg_time_seconds": round(metrics["avg_time"], 4),
                "total_time_seconds": round(metrics["total_time"], 2),
            }
            for endpoint, metrics in top_endpoints
        ],
    }


def reset_metrics():
    """Reset metrics (useful for testing)."""
    global _metrics
    _metrics = {
        "request_count": 0,
        "total_response_time": 0.0,
        "endpoint_times": {},
        "status_codes": {},
        "errors": 0,
    }

