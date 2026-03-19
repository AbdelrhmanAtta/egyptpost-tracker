import smtplib
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    reciverEmail = os.getenv("RECIVER_EMAIL")
    
    if not email or not password or not reciverEmail:
        print("Error: All environment variables (EMAIL, PASSWORD, RECIVER_EMAIL) must be set in .env file")
        return
    
    try:
        port = 465  # For SSL
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(email, password)
            print("Login successful!")
            # Email logic goes here!!
            server.sendmail(email ,reciverEmail, "dang")
    
    except smtplib.SMTPAuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Make sure you're using an app-specific password, not your regular Gmail password")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
