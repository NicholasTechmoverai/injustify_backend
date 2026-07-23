import random
import os
import smtplib
import datetime as dl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

from utils.auth_securityDb import set_token,check_token_existency
from config import Config

Frontend_server = Config.FRONTEND_SERVER



# Load environment variables
load_dotenv()

EMAIL = os.getenv("EMAIL", "admin@injustify.com")
PASSWORD = os.getenv("EMAIL_PASSWORD", "secret_pass")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


async def generate_random_code(length=6):
    """
    Generates a random numeric code of the specified length.
    """
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


async def send_codes(email, custom_message=None, length=6):
    """
    Generates a verification code and sends it via email.

    Args:
        addr (str): Recipient's email address.
        custom_message (str): Custom message (optional). If not provided, a default message is used.
        length (int): Length of the generated random code. Default is 6.

    Raises:
        ValueError: If email credentials are missing or recipient email is invalid.
        smtplib.SMTPException: If an error occurs during email transmission.
    """
    if not EMAIL or not PASSWORD:
        raise ValueError("Email credentials are not set in the environment variables.")

    if not email or "@" not in email:
        raise ValueError("Invalid recipient email address.")
    

    if await check_token_existency(email):
        return {"success": False, "message": "A valid token already exists for the given email."}


    random_code = await generate_random_code(length)

    now = dl.datetime.now()
    default_message = (
        f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
        <h1 style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">Injustify</h1>
            <p>Dear user,</p>
            <p>Please use the following code to verify your email or reset password (<span style="font-style: italic; color: gray; font-size: 12px;">{email}</span>):</p>
            <p style="font-size: 24px; font-weight: bold; color: #000; border: 1px solid #ccc; padding: 10px; display: inline-block; background-color: #f9f9f9;">
                {random_code}
            </p>
            <p><i>(Manually copy the code above and paste it in the verification form.)</i></p>
            <p>This code will expire in 30 minutes. If you need a new code, please request one.</p>
            <p>Sent on {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <p>If you did not request this code, please ignore this email.</p>
        </body>
        </html>
        """
    )

    email_message = custom_message or default_message

    try:
        message = MIMEMultipart("alternative")
        message['From'] = EMAIL
        message['To'] = email
        message['Subject'] = "Verification Code"
        message.attach(MIMEText(email_message, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as connection:
            connection.starttls()
            connection.login(EMAIL, PASSWORD)
            connection.sendmail(EMAIL, email, message.as_string())

        message = (f"Verification code sent to {email}")
        return {"email":email,"codes": random_code,"success": True,"message": message}

    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise


async def send_verify_link(email, token = None):
    """
    Sends a verification link to the user's registered email address.
    """
    if not email or "@" not in email:
        raise ValueError("Invalid recipient email address.")
    
    token = await generate_random_code(6)

    
    if not token:
        raise ValueError("Invalid or missing token.")

    url = f"{Frontend_server}/verify/auth?email={email}&token={token}"
    
    now = dl.datetime.now()
    
    email_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.5; color: #333;">
        <h1 style="font-size: 24px; font-weight: bold; margin-bottom: 10px;">Injustify</h1>
        <p>Dear user,</p>
        <p>Please click the link below to verify your email:</p>
        <a href="{url}" style="font-size: 24px; font-weight: bold; color: #000; border: 1px solid #ccc; padding: 10px; display: inline-block; background-color: #f9f9f9;">
            Verify Email
        </a>
        <p>This link will expire in 10 min time. If you need a new code, please request one.</p>
        <p>Sent on {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p>If you did not request this code, please ignore this email.</p>
    </body>
    </html>
    """
    
    message = MIMEMultipart("alternative")
    message['From'] = EMAIL
    message['To'] = email
    message['Subject'] = "Verify your email address"
    message.attach(MIMEText(email_message, "html"))

    result= await set_token(email,token)
    if  result.get('success')== False:
        """
        check if the email has  a set token in db and the token re
        """
        return {'success': False,"message":result['message'] }


    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as connection:
            connection.starttls() 
            connection.login(EMAIL, PASSWORD) 
            connection.sendmail(EMAIL, email, message.as_string())  


        return {'success': True, 'message':result['message']}
        
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
        return False

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
