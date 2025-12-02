"""Email notification service using Resend SMTP."""
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import aiosmtplib
import html
from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("email_service")


async def send_error_notification(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    error_type: str = "Backend Error"
) -> bool:
    """
    Send error notification email via Resend SMTP.
    
    This function is used by ALL email notifications (startup errors, request errors, etc.)
    and sends HTML emails with a black and white designer template.
    
    Args:
        error: The exception that occurred
        context: Optional context information (path, method, request_id, etc.)
        error_type: Type of error (e.g., "Backend Error", "Startup Error")
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Email notifications are optional - log why they're skipped for debugging
    if not settings.ENABLE_EMAIL_NOTIFICATIONS:
        logger.debug("Email notifications are disabled (ENABLE_EMAIL_NOTIFICATIONS=false)")
        return False
    
    if not settings.RESEND_API_KEY:
        logger.warning("Email notifications skipped: RESEND_API_KEY not set in .env")
        return False
    
    # Check if email addresses are configured
    if not settings.EMAIL_FROM or not settings.EMAIL_TO:
        logger.warning(f"Email notifications skipped: EMAIL_FROM or EMAIL_TO not set. FROM={settings.EMAIL_FROM}, TO={settings.EMAIL_TO}")
        return False
    
    try:
        # Format error message
        error_message = str(error)
        # Get traceback - format_exc() only works in exception context, so we'll format it manually
        try:
            import sys
            error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        except Exception:
            # Fallback if traceback formatting fails
            error_traceback = f"Traceback unavailable: {type(error).__name__}: {error_message}"
        
        # Build context information
        context_info = ""
        if context:
            context_info = "\n\nContext Information:\n"
            for key, value in context.items():
                context_info += f"  - {key}: {value}\n"
        
        # Build email subject
        subject = f"[{settings.APP_NAME}] {error_type}: {error_message[:100]}"
        
        # Escape HTML entities
        error_type_escaped = html.escape(error_type)
        error_message_escaped = html.escape(error_message)
        error_traceback_escaped = html.escape(error_traceback)
        app_name_escaped = html.escape(settings.APP_NAME)
        
        # Build context HTML
        context_html = ""
        if context:
            context_html = "<div style='margin-top: 24px; padding-top: 24px; border-top: 1px solid #e0e0e0;'>"
            context_html += "<h3 style='color: #000; font-size: 14px; font-weight: 600; margin: 0 0 16px 0; text-transform: uppercase; letter-spacing: 0.5px;'>Context Information</h3>"
            context_html += "<table style='width: 100%; border-collapse: collapse;'>"
            for key, value in context.items():
                key_escaped = html.escape(str(key))
                value_escaped = html.escape(str(value))
                context_html += f"""
                <tr style='border-bottom: 1px solid #f0f0f0;'>
                    <td style='padding: 8px 0; color: #666; font-size: 12px; font-weight: 500; width: 140px;'>{key_escaped}:</td>
                    <td style='padding: 8px 0; color: #000; font-size: 12px; font-family: monospace;'>{value_escaped}</td>
                </tr>
                """
            context_html += "</table></div>"
        
        # Build HTML email body with black and white designer style
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{error_type_escaped}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #ffffff; color: #000000;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <!-- Header -->
        <div style="background-color: #000000; padding: 32px 40px; text-align: center;">
            <h1 style="color: #ffffff; font-size: 24px; font-weight: 700; margin: 0; letter-spacing: 1px; text-transform: uppercase;">{error_type_escaped}</h1>
        </div>
        
        <!-- Main Content -->
        <div style="padding: 40px; background-color: #ffffff;">
            <!-- App Info -->
            <div style="margin-bottom: 32px; padding-bottom: 24px; border-bottom: 2px solid #000000;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span style="color: #666; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Application :</span>
                    <span style="color: #000; font-size: 11px; font-weight: 500;">{app_name_escaped} v{settings.APP_VERSION}</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span style="color: #666; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Environment :</span>
                    <span style="color: #000; font-size: 11px; font-weight: 500; text-transform: uppercase;">{html.escape(settings.ENVIRONMENT)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #666; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Timestamp :</span>
                    <span style="color: #000; font-size: 11px; font-weight: 500; font-family: monospace;">{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</span>
                </div>
            </div>
            
            <!-- Error Details -->
            <div style="margin-bottom: 32px;">
                <h2 style="color: #000; font-size: 14px; font-weight: 600; margin: 0 0 16px 0; text-transform: uppercase; letter-spacing: 0.5px;">Error Details</h2>
                <div style="background-color: #f8f8f8; border-left: 3px solid #000000; padding: 16px; margin-bottom: 16px;">
                    <p style="color: #000; font-size: 13px; line-height: 1.6; margin: 0; font-weight: 500;">{error_message_escaped}</p>
                </div>
            </div>
            
            <!-- Traceback -->
            <div style="margin-bottom: 32px;">
                <h2 style="color: #000; font-size: 14px; font-weight: 600; margin: 0 0 16px 0; text-transform: uppercase; letter-spacing: 0.5px;">Full Traceback</h2>
                <div style="background-color: #000000; color: #ffffff; padding: 20px; overflow-x: auto;">
                    <pre style="color: #ffffff; font-size: 11px; line-height: 1.6; margin: 0; font-family: 'Monaco', 'Menlo', 'Courier New', monospace; white-space: pre-wrap; word-wrap: break-word;">{error_traceback_escaped}</pre>
                </div>
            </div>
            
            <!-- Context Information -->
            {context_html}
            
            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 24px; border-top: 1px solid #e0e0e0; text-align: center;">
                <p style="color: #666; font-size: 11px; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Automated Error Notification</p>
                <p style="color: #999; font-size: 10px; margin: 8px 0 0 0;">{app_name_escaped}</p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        # Create email message
        message = MIMEMultipart()
        message["From"] = settings.EMAIL_FROM
        message["To"] = settings.EMAIL_TO
        message["Subject"] = subject
        
        # Add only HTML version
        message.attach(MIMEText(html_body, "html"))
        
        # Send email via SMTP
        # For port 465, use implicit TLS (SSL)
        # For ports 587, 25, 2587, use STARTTLS (explicit TLS upgrade)
        use_tls = settings.SMTP_PORT == 465
        
        smtp_client = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=use_tls,
        )
        
        try:
            await smtp_client.connect()
            logger.debug(f"Connected to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            
            # Use STARTTLS for ports 587, 25, 2587 (explicit TLS upgrade)
            # Don't use STARTTLS for port 465 (already using implicit TLS)
            if settings.SMTP_PORT in [587, 25, 2587] and not use_tls:
                try:
                    logger.debug("Upgrading connection to TLS using STARTTLS")
                    await smtp_client.starttls()
                    logger.debug("STARTTLS successful")
                except Exception as tls_error:
                    # If connection is already using TLS, that's fine - continue
                    error_msg = str(tls_error).lower()
                    if "already using tls" in error_msg or "already encrypted" in error_msg:
                        logger.debug("Connection already using TLS, skipping STARTTLS")
                    else:
                        # Re-raise if it's a different error
                        logger.warning(f"STARTTLS error: {tls_error}")
                        raise
            
            # Authenticate
            logger.debug(f"Attempting SMTP login to {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            await smtp_client.login(settings.SMTP_USERNAME, settings.RESEND_API_KEY)
            logger.debug("SMTP authentication successful")
            
            # Send email
            logger.debug(f"Sending email from {settings.EMAIL_FROM} to {settings.EMAIL_TO}")
            await smtp_client.send_message(message)
            
            logger.info(f"Error notification email sent successfully to {settings.EMAIL_TO}")
            return True
        finally:
            # Always close connection
            try:
                await smtp_client.quit()
            except Exception:
                pass  # Ignore errors during quit
            
    except Exception as e:
        logger.error(
            f"Failed to send error notification email: {e}",
            exc_info=True,
            extra={
                "smtp_host": settings.SMTP_HOST,
                "smtp_port": settings.SMTP_PORT,
                "email_from": settings.EMAIL_FROM,
                "email_to": settings.EMAIL_TO,
                "has_api_key": bool(settings.RESEND_API_KEY)
            }
        )
        return False


async def send_startup_error_notification(
    error: Exception,
    component: str = "Unknown"
) -> bool:
    """
    Send startup error notification.
    
    Args:
        error: The exception that occurred during startup
        component: The component that failed (e.g., "Database", "Redis", "Scheduler")
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    context = {
        "component": component,
        "phase": "startup",
    }
    return await send_error_notification(
        error=error,
        context=context,
        error_type=f"Startup Error - {component}"
    )


async def send_request_error_notification(
    error: Exception,
    path: str,
    method: str,
    request_id: Optional[str] = None,
    client_host: Optional[str] = None
) -> bool:
    """
    Send request error notification.
    
    Args:
        error: The exception that occurred
        path: Request path
        method: HTTP method
        request_id: Optional request ID for tracing
        client_host: Optional client host/IP
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    context = {
        "path": path,
        "method": method,
        "phase": "request_handling",
    }
    
    if request_id:
        context["request_id"] = request_id
    if client_host:
        context["client_host"] = client_host
    
    return await send_error_notification(
        error=error,
        context=context,
        error_type="Request Error"
    )
