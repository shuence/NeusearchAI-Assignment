"""Health controller for handling health check requests."""
from datetime import datetime
from app.services.health_service import HealthService
from app.schemas.health import HealthResponse
from app.constants import STATUS_ALIVE, STATUS_READY


class HealthController:
    """Controller for health check endpoints."""
    
    def __init__(self):
        """Initialize health controller with service."""
        self.health_service = HealthService()
    
    async def get_health(self) -> HealthResponse:
        """Get detailed health check information."""
        return self.health_service.get_health_response()
    
    async def get_liveness(self) -> HealthResponse:
        """Get liveness probe response."""
        return HealthResponse(status=STATUS_ALIVE)
    
    async def get_readiness(self) -> HealthResponse:
        """Get readiness probe response."""
        return HealthResponse(status=STATUS_READY)

