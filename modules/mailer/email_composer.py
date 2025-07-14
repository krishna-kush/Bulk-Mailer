
# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Enterprise-grade email campaign management system designed for
#              professional bulk email campaigns with advanced queue management,
#              intelligent rate limiting, and robust error handling.
#
# Components: - Multi-Provider SMTP Management (Gmail, Outlook, Yahoo, Custom)
#             - Intelligent Queue Management & Load Balancing
#             - Advanced Rate Limiting & Throttling Control
#             - Professional HTML Template System with Personalization
#             - Retry Mechanisms with Exponential Backoff
#             - Real-time Monitoring & Comprehensive Logging
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from .email_personalizer import EmailPersonalizer

class EmailComposer:
    """Composes email messages, including HTML content and attachments."""

    def __init__(self, logger, personalization_config=None, base_dir=None, anti_spam_config=None):
        self.logger = logger
        self.personalizer = None

        # Initialize personalizer if config provided or anti-spam features enabled
        if (personalization_config and base_dir) or (anti_spam_config and base_dir):
            # Merge personalization and anti-spam configs
            combined_config = {}
            if personalization_config:
                combined_config.update(personalization_config)
            if anti_spam_config:
                combined_config.update(anti_spam_config)

            if combined_config and base_dir:
                self.personalizer = EmailPersonalizer(combined_config, base_dir, logger)

    def compose_email(self, sender_email, recipient_email, subject, body_html_content,
                     attachment_paths=None, cid_attachments=None):
        """
        Composes a MIMEMultipart message with HTML body and optional attachments.

        Args:
            sender_email: Sender's email address
            recipient_email: Recipient's email address
            subject: Email subject
            body_html_content: HTML content of the email
            attachment_paths: List of file paths for regular attachments
            cid_attachments: Dict of CID attachments {content_id: file_path}
        """
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body_html_content, "html"))

        # Add regular attachments
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

        # Add CID attachments (inline attachments)
        if cid_attachments:
            for content_id, file_path in cid_attachments.items():
                if not os.path.exists(file_path):
                    self.logger.warning(f"CID attachment file not found: {file_path}")
                    continue
                try:
                    with open(file_path, "rb") as f:
                        # Determine MIME type based on file extension
                        file_ext = os.path.splitext(file_path)[1].lower()
                        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                            from email.mime.image import MIMEImage
                            part = MIMEImage(f.read())
                        else:
                            # For non-image files, use MIMEApplication
                            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))

                        # Set Content-ID header for CID reference
                        part.add_header('Content-ID', f'<{content_id}>')
                        part.add_header('Content-Disposition', 'inline', filename=os.path.basename(file_path))
                        msg.attach(part)

                        self.logger.debug(f"Added CID attachment: {content_id} -> {file_path}")

                except Exception as e:
                    self.logger.error(f"Error attaching CID file {file_path}: {e}")

        return msg

    def compose_personalized_email(self, sender_email, recipient_data, subject,
                                  body_html_template, attachment_paths=None,
                                  cid_attachments=None, template_filename=None):
        """
        Composes a personalized email message using the personalization system.

        Args:
            sender_email: Sender's email address
            recipient_data: Dictionary containing recipient information
            subject: Email subject (can contain placeholders)
            body_html_template: HTML template content
            attachment_paths: List of attachment file paths
            cid_attachments: Dict of CID attachments {content_id: file_path}
            template_filename: Optional template filename for Jinja2

        Returns:
            MIMEMultipart message object
        """
        recipient_email = recipient_data.get('email', '')

        # Personalize the email content
        if self.personalizer:
            try:
                # Personalize HTML body
                personalized_body = self.personalizer.personalize_email(
                    body_html_template, recipient_data, template_filename
                )

                # Personalize subject if it contains placeholders
                personalized_subject = self.personalizer.personalize_email(
                    subject, recipient_data
                )

                self.logger.debug(f"Personalized email for {recipient_email}")

            except Exception as e:
                self.logger.warning(f"Personalization failed for {recipient_email}: {e}")
                # Fallback to original content
                personalized_body = body_html_template
                personalized_subject = subject
        else:
            # No personalizer available, use original content
            personalized_body = body_html_template
            personalized_subject = subject
            self.logger.debug("No personalizer available, using original content")

        # Compose the email with personalized content
        return self.compose_email(
            sender_email=sender_email,
            recipient_email=recipient_email,
            subject=personalized_subject,
            body_html_content=personalized_body,
            attachment_paths=attachment_paths,
            cid_attachments=cid_attachments
        )

    def validate_template(self, template_content):
        """Validate email template and return analysis."""
        if self.personalizer:
            return self.personalizer.validate_template(template_content)
        else:
            return {
                'has_jinja2_syntax': False,
                'jinja2_available': False,
                'placeholders_found': [],
                'undefined_variables': [],
                'legacy_placeholders': []
            }


