import smtplib
import ssl
import os
import logging
from email.message import EmailMessage

# This logger will inherit settings from your main program
logger = logging.getLogger(__name__)

def send_order_update_email(order_id: str, state: str, time: str):
    """
    Sends a secure SMTP email. 
    Designed to be called from other scripts.
    """
    # 1. Fetch Config (Better to do this inside the function for portability)
    sender_email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    receiver_email = os.getenv("RECIVER_EMAIL")

    if not all([sender_email, password, receiver_email]):
        raise ValueError("SMTP credentials missing from environment variables.")

    # 2. Build the Message Structure
    msg = EmailMessage()
    msg['Subject'] = f"Egypt Post Update: {order_id}"
    msg['From'] = f"Automation System <{sender_email}>"
    msg['To'] = receiver_email
    
    # Professional Body Layout
    content = (
        f"Order Update Received\n"
        f"{'='*30}\n"
        f"Order ID: {order_id}\n"
        f"New Status: {state.upper()}\n"
        f"Timestamp: {time}\n"
        f"{'='*30}\n"
        f"This is an automated notification."
    )
    msg.set_content(content)

    # 3. Execution with Strict Error Handling
    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.send_message(msg)
            return True # Success signal
            
    except smtplib.SMTPAuthenticationError:
        logger.error("Email Auth Failed: Check if App Password is correct.")
        raise # Passes the error to your main program
    except Exception as e:
        logger.error(f"Mail System Error: {e}")
        raise

if __name__ == "__main__":
    # 3. Pass the required data when calling the function
    send_order_update_email("EP12345", "In Transit", "14:30 PM")