"""Health router for health check endpoints."""
from fastapi import APIRouter
from app.controller.health_controller import HealthController
from app.schemas.health import HealthResponse
from app.middleware.metrics import get_metrics

router = APIRouter()
controller = HealthController()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Detailed health check endpoint.
    Returns comprehensive system health information.
    """
    return await controller.get_health()


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """
    Liveness probe endpoint.
    Used by Kubernetes and other orchestration tools.
    """
    return await controller.get_liveness()


@router.get("/health/ready", response_model=HealthResponse)
async def readiness() -> HealthResponse:
    """
    Readiness probe endpoint.
    Used by Kubernetes and other orchestration tools.
    """
    return await controller.get_readiness()


@router.get("/metrics")
async def get_performance_metrics() -> dict:
    """
    Get performance metrics for monitoring.
    
    Returns:
        Dictionary with request metrics, response times, and endpoint statistics
    """
    return get_metrics()

