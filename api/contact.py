import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
import re
from pydantic import BaseModel, Field, validator

from .database import save_contact_message

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/contact",
    tags=["contact"],
)

EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

class ContactForm(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Sender name")
    email: str = Field(..., description="Sender email address")
    message: str = Field(..., min_length=10, max_length=2000, description="Message content")

    @validator("email")
    def validate_email(cls, v):
        if not re.match(EMAIL_REGEX, v):
            raise ValueError("Invalid email format")
        return v

def send_smtp_email(to_email: str, subject: str, html_body: str):
    """Synchronous function to connect to SMTP server and send email."""
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_host, smtp_port, smtp_username, smtp_password]):
        logger.warning("SMTP email sending skipped: Credentials not fully configured in environment.")
        return

    try:
        port = int(smtp_port)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Everything PESU <{smtp_username}>"
        msg["To"] = to_email

        part = MIMEText(html_body, "html")
        msg.attach(part)

        # Connect based on Port (465 is typically SSL, 587/25 is TLS)
        if port == 465:
            with smtplib.SMTP_SSL(smtp_host, port, timeout=10) as server:
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_username, to_email, msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, port, timeout=10) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(smtp_username, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send SMTP email to {to_email}: {e}")

def create_admin_email_html(name: str, email: str, message: str) -> str:
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f6f6f4; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e3e3e0;">
            <div style="background-color: #D97706; padding: 24px; text-align: center; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.02em;">New Query: Everything PESU</h2>
            </div>
            <div style="padding: 24px; color: #1d1d1b; line-height: 1.6;">
                <p style="margin-top: 0;">You have received a new contact inquiry with the following details:</p>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr>
                        <td style="padding: 8px 0; font-weight: 600; color: #6b6b68; width: 80px;">Name:</td>
                        <td style="padding: 8px 0; color: #1d1d1b;">{name}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px 0; font-weight: 600; color: #6b6b68;">Email:</td>
                        <td style="padding: 8px 0; color: #1d1d1b;"><a href="mailto:{email}" style="color: #D97706; text-decoration: none;">{email}</a></td>
                    </tr>
                </table>
                <div style="background-color: #f6f6f4; border-radius: 12px; padding: 16px; border: 1px solid #e3e3e0; margin-top: 10px;">
                    <p style="margin: 0; font-weight: 600; color: #6b6b68; margin-bottom: 8px; font-size: 12px; uppercase tracking-wider;">Message:</p>
                    <p style="margin: 0; color: #1d1d1b; white-space: pre-wrap;">{message}</p>
                </div>
            </div>
            <div style="background-color: #fdfdfc; padding: 16px; text-align: center; border-top: 1px solid #e3e3e0; font-size: 12px; color: #a1a19e;">
                This message was logged and sent from the Everything PESU Dashboard.
            </div>
        </div>
    </body>
    </html>
    """

def create_user_email_html(name: str, message: str) -> str:
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f6f6f4; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #e3e3e0;">
            <div style="background-color: #D97706; padding: 24px; text-align: center; color: #ffffff;">
                <h2 style="margin: 0; font-size: 20px; font-weight: 600; letter-spacing: -0.02em;">We've received your inquiry!</h2>
            </div>
            <div style="padding: 24px; color: #1d1d1b; line-height: 1.6;">
                <p style="margin-top: 0; font-size: 15px;">Hi {name},</p>
                <p>Thank you for reaching out to us. We have received your query and will look into it as soon as possible.</p>
                <p>Here is a copy of the message you submitted for your reference:</p>
                <div style="background-color: #f6f6f4; border-radius: 12px; padding: 16px; border: 1px solid #e3e3e0; margin: 20px 0;">
                    <p style="margin: 0; color: #1d1d1b; white-space: pre-wrap;">{message}</p>
                </div>
                <p style="margin-bottom: 0;">Best regards,<br/><strong>Everything PESU Team</strong></p>
            </div>
            <div style="background-color: #fdfdfc; padding: 16px; text-align: center; border-top: 1px solid #e3e3e0; font-size: 12px; color: #a1a19e;">
                This is an automated response. Please do not reply directly to this email.
            </div>
        </div>
    </body>
    </html>
    """

@router.post("")
async def receive_contact_form(payload: ContactForm, background_tasks: BackgroundTasks):
    """Processes contact queries, logs to db, and triggers background email sends."""
    try:
        # 1. Log query in database
        await save_contact_message(
            name=payload.name,
            email=payload.email,
            message=payload.message
        )

        # 2. Check if SMTP configuration exists
        smtp_host = os.getenv("SMTP_HOST")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_to = os.getenv("SMTP_TO") or smtp_username

        if smtp_host and smtp_username:
            # Prepare emails
            admin_html = create_admin_email_html(payload.name, payload.email, payload.message)
            user_html = create_user_email_html(payload.name, payload.message)

            # Send email notifications in background thread
            background_tasks.add_task(
                send_smtp_email,
                to_email=smtp_to,
                subject=f"[Everything PESU Inquiry] {payload.name}",
                html_body=admin_html
            )
            background_tasks.add_task(
                send_smtp_email,
                to_email=payload.email,
                subject="[Copy] Your inquiry on Everything PESU",
                html_body=user_html
            )
            email_status = "sent"
        else:
            logger.warning("SMTP is not configured. Email confirmation will be simulated.")
            email_status = "simulated"

        return {
            "status": "success",
            "message": "Your message has been submitted successfully!",
            "email_status": email_status
        }
    except Exception as e:
        logger.error(f"Error handling contact submission: {e}")
        raise HTTPException(
            status_code=500,
            detail="There was an error saving your inquiry. Please try again later."
        )
