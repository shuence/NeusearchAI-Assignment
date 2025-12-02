"""Validation middleware for request validation and sanitization."""
import asyncio
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import get_logger
from app.services.email_service import send_request_error_notification

logger = get_logger("validation_middleware")


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and rate limiting preparation."""
    
    # Paths that should skip validation
    SKIP_PATHS = ["/api/health", "/api/docs", "/docs", "/openapi.json"]
    
    # Maximum request body size (10MB)
    MAX_BODY_SIZE = 10 * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next):
        """Process request through validation middleware."""
        
        # Skip validation for health checks and docs
        if any(request.url.path.startswith(path) for path in self.SKIP_PATHS):
            return await call_next(request)
            
        # Add request ID for tracing (if not present)
        if "X-Request-ID" not in request.headers:
            import uuid
            request.state.request_id = str(uuid.uuid4())
        else:
            request.state.request_id = request.headers["X-Request-ID"]
        
        try:
            response = await call_next(request)
            return response
        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {e} from {request.client.host}")
            return JSONResponse(
                status_code=400,
                content={"detail": str(e), "request_id": request.state.request_id}
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in middleware: {e}", exc_info=True)
            # Send email notification in background
            asyncio.create_task(send_request_error_notification(
                error=e,
                path=request.url.path,
                method=request.method,
                request_id=getattr(request.state, "request_id", None),
                client_host=request.client.host if request.client else None
            ))
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with error handling."""
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                f"Unhandled exception: {e}",
                exc_info=True,
                extra={"path": request.url.path, "method": request.method}
            )
            
            # Send email notification in background
            asyncio.create_task(send_request_error_notification(
                error=e,
                path=request.url.path,
                method=request.method,
                request_id=getattr(request.state, "request_id", None),
                client_host=request.client.host if request.client else None
            ))
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "An internal server error occurred. Please try again later.",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )

