
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

class EmailSender:
    """Handles the actual sending of emails via SMTP."""

    def __init__(self, smtp_configs, logger):
        self.smtp_configs = smtp_configs
        self.logger = logger

    def _create_message(self, sender_email, recipient_email, subject, body_html, attachments=None):
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body_html, "html"))

        if attachments:
            for attachment_path in attachments:
                try:
                    with open(attachment_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                    part["Content-Disposition"] = f"attachment; filename=\"{os.path.basename(attachment_path)}\""

                    msg.attach(part)
                except Exception as e:
                    self.logger.error(f"Could not attach file {attachment_path}: {e}")
        return msg

    def send_email(self, sender_email, sender_password, recipient_email, subject, body_html, attachments=None, smtp_id="default"):
        """Sends a single email using the specified SMTP configuration."""
        try:
            # Get SMTP settings for this sender
            smtp_settings = self.smtp_configs.get(smtp_id, self.smtp_configs.get("default"))
            if not smtp_settings:
                self.logger.error(f"SMTP configuration '{smtp_id}' not found")
                return False
            
            msg = self._create_message(sender_email, recipient_email, subject, body_html, attachments)

            with smtplib.SMTP(smtp_settings["host"], smtp_settings["port"]) as server:
                if smtp_settings["use_tls"]:
                    server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            self.logger.info(f"Email sent from {sender_email} to {recipient_email} using SMTP '{smtp_id}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email from {sender_email} to {recipient_email} using SMTP '{smtp_id}': {e}")
            return False


