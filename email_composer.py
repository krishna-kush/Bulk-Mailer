
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

class EmailComposer:
    """Composes email messages, including HTML content and attachments."""

    def __init__(self, logger):
        self.logger = logger

    def compose_email(self, sender_email, recipient_email, subject, body_html_content, attachment_paths=None):
        """Composes a MIMEMultipart message with HTML body and optional attachments."""
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body_html_content, "html"))

        if attachment_paths:
            for attachment_path in attachment_paths:
                if not os.path.exists(attachment_path):
                    self.logger.warning(f"Attachment file not found: {attachment_path}")
                    continue
                try:
                    with open(attachment_path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                    part["Content-Disposition"] = f"attachment; filename=\"{os.path.basename(attachment_path)}\""
                    msg.attach(part)
                    self.logger.debug(f"Attached file: {os.path.basename(attachment_path)}")
                except Exception as e:
                    self.logger.error(f"Error attaching file {attachment_path}: {e}")
        return msg


