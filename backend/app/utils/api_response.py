"""Standard API response utilities for consistent API responses."""
import time
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper with metadata."""
    success: bool
    data: T
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    count: Optional[int] = None


class ApiErrorResponse(BaseModel):
    """Standard API error response."""
    success: bool = False
    detail: str
    status_code: int
    request_id: Optional[str] = None
    response_time_ms: Optional[float] = None


class ResponseTimer:
    """Context manager for tracking response time."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.response_time_ms: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.response_time_ms = (time.time() - self.start_time) * 1000
        return False
    
    def get_time_ms(self) -> float:
        """Get response time in milliseconds."""
        if self.response_time_ms is not None:
            return round(self.response_time_ms, 2)
        if self.start_time:
            return round((time.time() - self.start_time) * 1000, 2)
        return 0.0


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    response_time_ms: Optional[float] = None,
    count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standard success response.
    
    Args:
        data: The response data
        message: Optional success message
        response_time_ms: Response time in milliseconds
        count: Optional count of items (useful for list responses)
    
    Returns:
        Dictionary with standard response format
    """
    response: Dict[str, Any] = {
        "success": True,
        "data": data,
    }
    
    if message:
        response["message"] = message
    
    if response_time_ms is not None:
        response["response_time_ms"] = round(response_time_ms, 2)
    
    if count is not None:
        response["count"] = count
    
    return response


def create_error_response(
    detail: str,
    status_code: int = 500,
    request_id: Optional[str] = None,
    response_time_ms: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create a standard error response.
    
    Args:
        detail: Error message
        status_code: HTTP status code
        request_id: Optional request ID for tracing
        response_time_ms: Response time in milliseconds
    
    Returns:
        Dictionary with standard error format
    """
    response: Dict[str, Any] = {
        "success": False,
        "detail": detail,
        "status_code": status_code,
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if response_time_ms is not None:
        response["response_time_ms"] = round(response_time_ms, 2)
    
    return response


def add_response_time(response: Dict[str, Any], response_time_ms: float) -> Dict[str, Any]:
    """
    Add response time to an existing response dictionary.
    
    Args:
        response: Response dictionary
        response_time_ms: Response time in milliseconds
    
    Returns:
        Response dictionary with response_time_ms added
    """
    response["response_time_ms"] = round(response_time_ms, 2)
    return response


def wrap_list_response(
    items: List[Any],
    response_time_ms: Optional[float] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrap a list of items in a standard response format.
    
    Args:
        items: List of items to wrap
        response_time_ms: Response time in milliseconds
        message: Optional message
    
    Returns:
        Dictionary with standard list response format
    """
    response: Dict[str, Any] = {
        "items": items,
        "count": len(items),
    }
    
    if response_time_ms is not None:
        response["response_time_ms"] = round(response_time_ms, 2)
    
    if message:
        response["message"] = message
    
    return response

