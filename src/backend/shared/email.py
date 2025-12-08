"""
📧 EMAIL SERVICE
================

🎯 PURPOSE:
Send transactional emails using Brevo (Sendinblue) API.

✅ BEST PRACTICES:
1. Use transactional email service (not SMTP) for reliability
2. Use templates for consistent branding
3. Handle errors gracefully with retries if needed
"""

import httpx

from backend.shared.config import settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str | None = None,
) -> bool:
    """
    Send an email using Brevo API.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body
        text_content: Plain text body (optional)
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.BREVO_API_KEY:
        logger.warning("Brevo API key not configured, skipping email")
        return False
    
    payload = {
        "sender": {
            "name": settings.BREVO_SENDER_NAME,
            "email": settings.BREVO_SENDER_EMAIL,
        },
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    
    if text_content:
        payload["textContent"] = text_content
    
    headers = {
        "api-key": settings.BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BREVO_API_URL,
                json=payload,
                headers=headers,
                timeout=10.0,
            )
            
            if response.status_code in (200, 201):
                logger.info("Email sent successfully", to=to_email, subject=subject)
                return True
            else:
                logger.error(
                    "Failed to send email",
                    status_code=response.status_code,
                    response=response.text,
                )
                return False
    except Exception as e:
        logger.error("Email sending error", error=str(e))
        return False


async def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Send OTP verification email.
    
    Args:
        to_email: Recipient email address
        otp_code: The OTP code to send
        
    Returns:
        True if sent successfully
    """
    subject = f"Your BazaarHub Verification Code: {otp_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 500px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .logo {{ text-align: center; font-size: 28px; font-weight: bold; color: #6366F1; margin-bottom: 30px; }}
            .otp-code {{ text-align: center; font-size: 36px; font-weight: bold; color: #1e293b; letter-spacing: 8px; background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .message {{ color: #64748b; line-height: 1.6; text-align: center; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; color: #94a3b8; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🛒 BazaarHub</div>
            <p class="message">Your verification code is:</p>
            <div class="otp-code">{otp_code}</div>
            <p class="message">
                This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.<br>
                If you didn't request this code, please ignore this email.
            </p>
            <div class="footer">
                &copy; 2024 BazaarHub. All rights reserved.
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    BazaarHub Verification Code
    
    Your verification code is: {otp_code}
    
    This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.
    If you didn't request this code, please ignore this email.
    """
    
    return await send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )
