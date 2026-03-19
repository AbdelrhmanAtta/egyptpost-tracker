import smtplib
import ssl
import os
import logging
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MailConfigError(Exception):
    """Raised when environment variables are missing."""
    pass

class MailAuthError(Exception):
    """Raised when SMTP login fails."""
    pass

class MailDeliveryError(Exception):
    """Raised when the connection or sending process fails."""
    pass

def send_order_update_email(order_data: dict):
    """
    Sends a secure SMTP email based on a dictionary input.
    """

    # Extract data from .env
    sender_email = os.getenv("EMAIL")
    sender_password = os.getenv("PASSWORD")
    
    # Extract data from the dictionary
    order_id = order_data.get("order_id", "Unknown ID")
    status = order_data.get("last_status", "Update Unavailable")
    timestamp = order_data.get("last_update", "N/A")
    original_receiver_email = order_data.get("email")
    if original_receiver_email and "@" in original_receiver_email:
        user_part, domain_part = original_receiver_email.split("@")
        receiver_email = f"{user_part}+tracker@{domain_part}"
    else:
        receiver_email = original_receiver_email

    # Validate Configuration
    if not all([sender_email, sender_password, receiver_email]):
        error_text = f"Configuration Failure: EMAIL={bool(sender_email)}, PASSWORD={bool(sender_password)}, RECIPIENT={bool(receiver_email)}"
        logger.error(error_text)
        raise MailConfigError(error_text)

    # Build the Email Message
    msg = EmailMessage()
    msg['Subject'] = f"Egypt Post Update: {order_id}"
    msg['From'] = f"Tracking System <{sender_email}>"
    msg['To'] = receiver_email
    
    body = (
        f"Egypt Post Status Notification\n"
        f"{'='*30}\n"
        f"Tracking ID: {order_id}\n"
        f"Current Status: {status.upper()}\n"
        f"Update Time: {timestamp}\n"
        f"{'='*30}\n"
        f"This is an automated system message."
    )
    msg.set_content(body)

    # Secure SMTP Logic
    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            logger.info(f"Notification sent successfully for {order_id} to {receiver_email}")
            return True

    except smtplib.SMTPAuthenticationError as e:
        logger.critical(f"Authentication Failed for {sender_email}: {e}")
        raise MailAuthError("Invalid SMTP credentials or App Password.") from e
    
    except Exception as e:
        logger.error(f"Mail Delivery Failure: {e}")
        raise MailDeliveryError(f"SMTP connection or transmission error: {e}") from e
