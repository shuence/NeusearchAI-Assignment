"""Health router for health check endpoints."""
from fastapi import APIRouter, HTTPException
from app.controller.health_controller import HealthController
from app.schemas.health import HealthResponse, ProtectedAccessRequest, ProtectedAccessResponse
from app.middleware.metrics import get_metrics
from app.services.email_service import send_error_notification
from app.config.settings import settings

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


@router.post("/health/test-email")
async def test_email_notification() -> dict:
    """
    Test endpoint to manually trigger an email notification.
    Useful for testing email configuration.
    
    Returns:
        Dictionary with test result and status
    """
    try:
        test_error = Exception("This is a test error notification from the health endpoint")
        result = await send_error_notification(
            error=test_error,
            context={
                "endpoint": "/api/health/test-email",
                "method": "POST",
                "purpose": "Email configuration test"
            },
            error_type="Test Email Notification"
        )
        
        if result:
            return {
                "success": True,
                "message": "Test email sent successfully. Check your inbox.",
                "email_to": "Check your .env EMAIL_TO setting"
            }
        else:
            return {
                "success": False,
                "message": "Email notification was not sent. Check logs and .env configuration.",
                "hints": [
                    "Ensure ENABLE_EMAIL_NOTIFICATIONS=true in .env",
                    "Ensure RESEND_API_KEY is set in .env",
                    "Ensure EMAIL_FROM and EMAIL_TO are set in .env",
                    "Check application logs for more details"
                ]
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing email notification: {str(e)}"
        )


@router.get("/health/test-error")
async def test_intentional_error():
    """
    Test endpoint that intentionally raises an exception to trigger error email notifications.
    This will be caught by the ErrorHandlingMiddleware and should send an email.
    
    WARNING: This endpoint will return a 500 error, but should trigger an email notification.
    """
    # Intentionally raise an exception to test error handling and email notifications
    raise Exception("Intentional test error to verify email notification system is working correctly. This is expected behavior for testing purposes.")


@router.post("/protected", response_model=ProtectedAccessResponse)
async def protected_access(request: ProtectedAccessRequest) -> ProtectedAccessResponse:
    """
    Protected endpoint to validate access code for status page.
    
    Returns:
        ProtectedAccessResponse with access_granted status
    """
    # Check if access code is configured
    if not settings.STATUS_ACCESS_CODE:
        raise HTTPException(
            status_code=503,
            detail="Status page access code is not configured. Please set STATUS_ACCESS_CODE in environment variables."
        )
    
    # Validate access code
    if request.code == settings.STATUS_ACCESS_CODE:
        return ProtectedAccessResponse(
            success=True,
            message="Access granted",
            access_granted=True
        )
    else:
        return ProtectedAccessResponse(
            success=False,
            message="Invalid access code",
            access_granted=False
        )

