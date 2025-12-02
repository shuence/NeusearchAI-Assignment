"""Tests for email notification service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from email.mime.multipart import MIMEMultipart

from app.services.email_service import (
    send_error_notification,
    send_startup_error_notification,
    send_request_error_notification,
)


@pytest.fixture
def mock_settings():
    """Mock settings for email service tests."""
    with patch("app.services.email_service.settings") as mock_settings:
        mock_settings.ENABLE_EMAIL_NOTIFICATIONS = True
        mock_settings.RESEND_API_KEY = "test_api_key"
        mock_settings.EMAIL_FROM = "test@example.com"
        mock_settings.EMAIL_TO = "recipient@example.com"
        mock_settings.SMTP_HOST = "smtp.resend.com"
        mock_settings.SMTP_PORT = 587
        mock_settings.SMTP_USERNAME = "resend"
        mock_settings.APP_NAME = "Test App"
        mock_settings.ENVIRONMENT = "test"
        mock_settings.APP_VERSION = "1.0.0"
        yield mock_settings


@pytest.mark.asyncio
async def test_send_error_notification_disabled(mock_settings):
    """Test that email is not sent when notifications are disabled."""
    mock_settings.ENABLE_EMAIL_NOTIFICATIONS = False
    
    error = Exception("Test error")
    result = await send_error_notification(error)
    
    assert result is False


@pytest.mark.asyncio
async def test_send_error_notification_no_api_key(mock_settings):
    """Test that email is not sent when API key is missing."""
    mock_settings.RESEND_API_KEY = None
    
    error = Exception("Test error")
    result = await send_error_notification(error)
    
    assert result is False


@pytest.mark.asyncio
async def test_send_error_notification_no_email_from(mock_settings):
    """Test that email is not sent when EMAIL_FROM is missing."""
    mock_settings.EMAIL_FROM = None
    
    error = Exception("Test error")
    result = await send_error_notification(error)
    
    assert result is False


@pytest.mark.asyncio
async def test_send_error_notification_no_email_to(mock_settings):
    """Test that email is not sent when EMAIL_TO is missing."""
    mock_settings.EMAIL_TO = None
    
    error = Exception("Test error")
    result = await send_error_notification(error)
    
    assert result is False


@pytest.mark.asyncio
async def test_send_error_notification_success(mock_settings):
    """Test successful email sending."""
    # Mock SMTP client
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = Exception("Test error")
        context = {"path": "/test", "method": "GET"}
        
        result = await send_error_notification(error, context=context, error_type="Test Error")
        
        assert result is True
        mock_smtp.connect.assert_called_once()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("resend", "test_api_key")
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()


@pytest.mark.asyncio
async def test_send_error_notification_with_context(mock_settings):
    """Test email sending with context information."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = ValueError("Test validation error")
        context = {
            "path": "/api/test",
            "method": "POST",
            "request_id": "12345",
            "client_host": "127.0.0.1"
        }
        
        result = await send_error_notification(error, context=context)
        
        assert result is True
        # Verify message was sent
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        assert isinstance(message, MIMEMultipart)
        assert message["From"] == "test@example.com"
        assert message["To"] == "recipient@example.com"
        assert "Test validation error" in message["Subject"]


@pytest.mark.asyncio
async def test_send_error_notification_smtp_error(mock_settings):
    """Test handling of SMTP errors."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock(side_effect=Exception("SMTP connection failed"))
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = Exception("Test error")
        result = await send_error_notification(error)
        
        assert result is False


@pytest.mark.asyncio
async def test_send_error_notification_port_465_ssl(mock_settings):
    """Test email sending with port 465 (SSL)."""
    mock_settings.SMTP_PORT = 465
    
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp) as mock_smtp_class:
        error = Exception("Test error")
        result = await send_error_notification(error)
        
        assert result is True
        # Verify SMTP was initialized with use_tls=True for port 465
        mock_smtp_class.assert_called_once_with(
            hostname="smtp.resend.com",
            port=465,
            use_tls=True
        )
        # Should not call starttls for port 465
        mock_smtp.starttls.assert_not_called()


@pytest.mark.asyncio
async def test_send_startup_error_notification(mock_settings):
    """Test startup error notification."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = Exception("Database connection failed")
        result = await send_startup_error_notification(error, component="Database")
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        # Verify the message contains startup context
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        assert "Startup Error - Database" in message["Subject"]


@pytest.mark.asyncio
async def test_send_request_error_notification(mock_settings):
    """Test request error notification."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = Exception("Request processing failed")
        result = await send_request_error_notification(
            error=error,
            path="/api/chat",
            method="POST",
            request_id="req-123",
            client_host="192.168.1.1"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        # Verify the message contains request context
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        assert "Request Error" in message["Subject"]


@pytest.mark.asyncio
async def test_send_request_error_notification_minimal_context(mock_settings):
    """Test request error notification with minimal context."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = Exception("Test error")
        result = await send_request_error_notification(
            error=error,
            path="/api/test",
            method="GET"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_error_notification_quit_error_handled(mock_settings):
    """Test that errors during SMTP quit are handled gracefully."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock(side_effect=Exception("Quit failed"))
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = Exception("Test error")
        # Should still return True even if quit fails
        result = await send_error_notification(error)
        
        assert result is True


@pytest.mark.asyncio
async def test_send_error_notification_email_body_content(mock_settings):
    """Test that email body contains expected content."""
    mock_smtp = AsyncMock()
    mock_smtp.connect = AsyncMock()
    mock_smtp.starttls = AsyncMock()
    mock_smtp.login = AsyncMock()
    mock_smtp.send_message = AsyncMock()
    mock_smtp.quit = AsyncMock()
    
    with patch("app.services.email_service.aiosmtplib.SMTP", return_value=mock_smtp):
        error = ValueError("Test error message")
        context = {"component": "TestComponent"}
        
        result = await send_error_notification(error, context=context, error_type="Test Error")
        
        assert result is True
        
        # Get the message that was sent
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        
        # Verify email structure
        assert message["From"] == "test@example.com"
        assert message["To"] == "recipient@example.com"
        assert "Test Error" in message["Subject"]
        assert "[Test App]" in message["Subject"]
        
        # Verify body content (get payload)
        body = message.get_payload()[0].get_payload()
        assert "Test Error" in body
        assert "Test error message" in body
        assert "TestComponent" in body
        assert "test" in body  # Environment
        assert "Test App" in body
        assert "1.0.0" in body

