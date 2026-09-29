"""
email_service.py — Production Email Infrastructure for TeleMed AI Platform.

Handles email dispatch for verification, password resets, appointment confirmations,
and analysis report availability. Supports SMTP configuration with a graceful console/logger fallback.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

logger = logging.getLogger("web_platform.services.email")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@telemed.ai")


class EmailService:
    """Service wrapper for sending platform transactional emails."""

    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.sender_email = SENDER_EMAIL

    def send_email(self, recipient_email: str, subject: str, body_html: str, body_text: Optional[str] = None) -> bool:
        """Send transactional email via SMTP with fallback logger dispatch."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TeleMed AI Platform <{self.sender_email}>"
        msg["To"] = recipient_email

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        if self.smtp_user and self.smtp_password:
            try:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.sender_email, [recipient_email], msg.as_string())
                server.quit()
                logger.info(f"Email successfully dispatched to {recipient_email} via SMTP ({subject})")
                return True
            except Exception as e:
                logger.error(f"SMTP email dispatch failed for {recipient_email}: {e}")
                return False
        else:
            logger.info(f"[DEVELOPMENT LOGGED EMAIL] To: {recipient_email} | Subject: '{subject}'")
            return True

    def send_verification_email(self, recipient_email: str, verification_token: str) -> bool:
        """Send email verification link."""
        subject = "TeleMed AI — Email Address Verification"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #0284c7;">Welcome to TeleMed AI Platform</h2>
            <p>Please click the button below to verify your email address and activate your clinical account:</p>
            <p style="margin: 20px 0;">
                <a href="http://localhost:3000/verify-email?token={verification_token}" 
                   style="background-color: #0284c7; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                   Verify My Email Account
                </a>
            </p>
            <p style="font-size: 12px; color: #666;">Verification Token: {verification_token}</p>
        </div>
        """
        return self.send_email(recipient_email, subject, body_html)

    def send_password_reset_email(self, recipient_email: str, reset_token: str) -> bool:
        """Send password reset token."""
        subject = "TeleMed AI — Password Reset Request"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #0284c7;">Password Reset Security Request</h2>
            <p>You requested a password reset for your TeleMed AI account. Click below to proceed:</p>
            <p style="margin: 20px 0;">
                <a href="http://localhost:3000/reset-password?token={reset_token}" 
                   style="background-color: #0284c7; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                   Reset Account Password
                </a>
            </p>
            <p style="font-size: 12px; color: #666;">Reset Token: {reset_token}</p>
        </div>
        """
        return self.send_email(recipient_email, subject, body_html)

    def send_appointment_confirmation(self, recipient_email: str, appointment_details: Dict[str, Any]) -> bool:
        """Send appointment booking confirmation."""
        subject = f"TeleMed AI — Appointment Confirmed ({appointment_details.get('appointment_date', 'Scheduled')})"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #10b981;">Consultation Appointment Confirmed</h2>
            <p>Your telemedicine consultation appointment has been scheduled:</p>
            <ul>
                <li><strong>Doctor:</strong> {appointment_details.get('doctor_name', 'Attending Physician')}</li>
                <li><strong>Specialization:</strong> {appointment_details.get('specialization', 'General')}</li>
                <li><strong>Date & Time:</strong> {appointment_details.get('appointment_date', 'Scheduled')}</li>
            </ul>
        </div>
        """
        return self.send_email(recipient_email, subject, body_html)

    def send_report_ready_notification(self, recipient_email: str, record_id: str) -> bool:
        """Send report ready notification."""
        subject = "TeleMed AI — Multimodal Analysis Report Ready"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #0284c7;">Your Multimodal AI Report is Ready</h2>
            <p>Your disease risk analysis report and TreeSHAP explainability attributions have been generated:</p>
            <p style="margin: 20px 0;">
                <a href="http://localhost:3000/report?id={record_id}" 
                   style="background-color: #0284c7; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                   View Clinical Report
                </a>
            </p>
        </div>
        """
        return self.send_email(recipient_email, subject, body_html)


email_service = EmailService()
