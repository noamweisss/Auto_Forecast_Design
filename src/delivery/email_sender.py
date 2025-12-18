"""
Email Sender - Send Forecast Images via SMTP

This module sends the generated forecast image via email using
Gmail SMTP with App Password authentication.

Configuration:
    All email settings are loaded from environment variables (.env file):
    - SMTP_SERVER: smtp.gmail.com
    - SMTP_PORT: 587 (TLS)
    - EMAIL_ADDRESS: sender Gmail address
    - EMAIL_PASSWORD: Gmail App Password (NOT regular password!)
    - RECIPIENT_EMAIL: recipient email address

Security Note:
    Never commit the .env file! It's in .gitignore.
    Generate App Passwords at: https://myaccount.google.com/apppasswords

Usage:
    from src.delivery.email_sender import send_forecast_email
    
    success = send_forecast_email("output/forecast_2024-12-18.jpg")
    if success:
        print("Email sent successfully!")
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from pathlib import Path
from datetime import date
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def send_forecast_email(
    image_path: str,
    recipient: Optional[str] = None,
    subject: Optional[str] = None
) -> bool:
    """
    Send the forecast image via email.
    
    Args:
        image_path: Path to the image file to attach (usually JPEG)
        recipient: Override recipient email (defaults to RECIPIENT_EMAIL env var)
        subject: Override email subject
        
    Returns:
        True if email sent successfully, False otherwise
        
    Raises:
        ValueError: If required environment variables are missing
        smtplib.SMTPException: If email sending fails
    """
    # TODO: Implement in Phase 5
    raise NotImplementedError("Will be implemented in Phase 5: Delivery")


def _create_email_message(
    sender: str,
    recipient: str,
    subject: str,
    body: str,
    image_path: Path
) -> MIMEMultipart:
    """
    Create an email message with an attached image.
    
    Args:
        sender: Sender email address
        recipient: Recipient email address
        subject: Email subject line
        body: Email body text
        image_path: Path to image file to attach
        
    Returns:
        MIMEMultipart email message ready to send
    """
    # TODO: Implement in Phase 5
    raise NotImplementedError("Will be implemented in Phase 5: Delivery")


def _get_default_subject() -> str:
    """
    Generate the default email subject with today's date.
    
    Returns:
        Subject string like "תחזית יומית - 18/12/2024"
    """
    today = date.today()
    return f"תחזית יומית - {today.strftime('%d/%m/%Y')}"


def _get_default_body() -> str:
    """
    Generate the default email body text.
    
    Returns:
        Simple body text in Hebrew
    """
    return """שלום,

מצורפת תחזית מזג האוויר היומית לפרסום ברשתות החברתיות.

בברכה,
מערכת התחזית האוטומטית
השירות המטאורולוגי הישראלי
"""


def validate_email_config() -> bool:
    """
    Check that all required email configuration is present.
    
    Returns:
        True if all config is valid, False otherwise
        
    Checks for:
        - SMTP_SERVER
        - SMTP_PORT
        - EMAIL_ADDRESS
        - EMAIL_PASSWORD
        - RECIPIENT_EMAIL
    """
    required_vars = [
        "SMTP_SERVER",
        "SMTP_PORT", 
        "EMAIL_ADDRESS",
        "EMAIL_PASSWORD",
        "RECIPIENT_EMAIL"
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        return False
    
    return True
