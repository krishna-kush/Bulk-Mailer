
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

import smtplib
from .email_composer import EmailComposer

class EmailSender:
    """Handles the actual sending of emails via SMTP."""

    def __init__(self, smtp_configs, logger, email_composer=None):
        self.smtp_configs = smtp_configs
        self.logger = logger
        self.email_composer = email_composer or EmailComposer(logger)

    def send_email(self, sender_email, sender_password, recipient_email, subject, body_html,
                  attachments=None, cid_attachments=None, smtp_id="default"):
        """Sends a single email using the specified SMTP configuration."""
        try:
            # Get SMTP settings for this sender
            smtp_settings = self.smtp_configs.get(smtp_id, self.smtp_configs.get("default"))
            if not smtp_settings:
                self.logger.error(f"SMTP configuration '{smtp_id}' not found")
                return False
            
            # Use EmailComposer for better CID attachment support
            msg = self.email_composer.compose_email(
                sender_email=sender_email,
                recipient_email=recipient_email,
                subject=subject,
                body_html_content=body_html,
                attachment_paths=attachments,
                cid_attachments=cid_attachments
            )

            with smtplib.SMTP(smtp_settings["host"], smtp_settings["port"]) as server:
                if smtp_settings["use_tls"]:
                    server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            self.logger.debug(f"Email sent from {sender_email} to {recipient_email} using SMTP '{smtp_id}'")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email from {sender_email} to {recipient_email} using SMTP '{smtp_id}': {e}")
            return False

