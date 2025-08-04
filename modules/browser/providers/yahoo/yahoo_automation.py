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

from typing import Dict, Any
from playwright.sync_api import Page
from ...html_capture import HTMLCapture
from .authentication import YahooAuthentication
from .email_composer import YahooEmailComposer
from .email_content_processor import EmailContentProcessor

class YahooAutomation:
    """Main Yahoo Mail automation class that coordinates authentication and email composition."""
    
    def __init__(self, config: Dict[str, Any], logger, base_dir: str = None, 
                 email_personalization: Dict[str, Any] = None, 
                 email_content: Dict[str, Any] = None):
        """
        Initialize Yahoo Mail automation.
        
        Args:
            config: Browser automation configuration
            logger: Logger instance
            base_dir: Base directory for HTML captures
            email_personalization: Email personalization settings
            email_content: Email content settings
        """
        self.config = config
        self.logger = logger
        self.base_dir = base_dir

        # Initialize HTML capture utility (only if enabled in config)
        html_capture_enabled = config.get('enable_html_capture', False)
        self.logger.debug(f"HTML capture enabled: {html_capture_enabled}, base_dir: {base_dir}")

        if base_dir and html_capture_enabled:
            try:
                self.html_capture = HTMLCapture(base_dir, logger)
                self.logger.info(f"HTML capture initialized successfully, directory: {self.html_capture.capture_dir}")
            except Exception as e:
                self.logger.error(f"Failed to initialize HTML capture: {e}")
                self.html_capture = None
        else:
            self.html_capture = None
            self.logger.debug(f"HTML capture not initialized - enabled: {html_capture_enabled}, base_dir: {base_dir}")

        # Initialize authentication and email composition modules
        self.auth = YahooAuthentication(config, logger, self.html_capture)
        self.composer = YahooEmailComposer(config, logger, self.html_capture)
        self.content_processor = EmailContentProcessor(
            email_personalization or {}, 
            email_content or {}, 
            logger
        )
        
        self.logger.info("Yahoo Mail automation initialized")
    
    def authenticate(self, page: Page, sender_email: str, sender_password: str) -> bool:
        """
        Authenticate with Yahoo Mail.

        Args:
            page: Playwright page instance
            sender_email: Email address
            sender_password: Password

        Returns:
            bool: True if authentication successful, "RETRY_FRESH_CONTEXT" if context needs refresh
        """
        try:
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_initial", "Yahoo Mail initial page load")

            result = self.auth.authenticate(page, sender_email, sender_password)

            # Handle special retry case
            if result == "RETRY_FRESH_CONTEXT":
                self.logger.warning("🔄 Authentication requires fresh browser context")
                return "RETRY_FRESH_CONTEXT"

            if result and self.html_capture:
                self.html_capture.capture_html(page, "yahoo_authenticated", "Yahoo Mail after successful authentication")

            return result

        except Exception as e:
            self.logger.error(f"Yahoo Mail authentication failed: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_auth_error", f"Yahoo Mail authentication error: {e}")
            return False
    
    def compose_and_send_email(self, page: Page, recipient_email: str, subject: str,
                              body_content: str, content_type: str = "text",
                              email: str = "", password: str = "") -> bool:
        """
        Complete email composition and sending workflow with fallback authentication.

        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            content_type: Content type (text/html)
            email: Sender email (for authentication)
            password: Sender password (for authentication)

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Authenticate if needed
            if email and password and not self.is_authenticated(page):
                auth_result = self.authenticate(page, email, password)
                if auth_result == "RETRY_FRESH_CONTEXT":
                    self.logger.warning("🔄 Authentication requires fresh browser context - returning retry signal")
                    return "RETRY_FRESH_CONTEXT"
                elif not auth_result:
                    return False

            # Send the email using the composer
            success = self.composer.compose_and_send_email(
                page, recipient_email, subject, body_content,
                None, None, content_type
            )

            if success:
                self.logger.info(f"Successfully sent email to {recipient_email}")
            else:
                self.logger.error(f"Failed to send email to {recipient_email}")

            return success

        except Exception as e:
            self.logger.error(f"Error in compose_and_send_email: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_compose_send_error", f"Compose and send error: {e}")
            return False

    def send_email(self, page: Page, recipient_email: str, subject: str,
                   body_content: str, attachments: list = None,
                   cid_attachments: Dict[str, str] = None,
                   content_type: str = "text",
                   recipient_data: Dict[str, Any] = None) -> bool:
        """
        Send email through Yahoo Mail.
        
        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            attachments: List of attachment file paths
            cid_attachments: Dictionary of CID attachments
            content_type: Content type (text/html)
            recipient_data: Additional recipient data for personalization
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Process email content with personalization and randomization
            processed_subject, processed_body = self.content_processor.process_email_content(
                subject, body_content, recipient_email, recipient_data or {}
            )
            
            self.logger.info("Email content processed with all settings applied")
            
            # Send the email using the composer
            success = self.composer.compose_and_send_email(
                page, recipient_email, processed_subject, processed_body,
                attachments, cid_attachments, content_type
            )
            
            if success:
                self.logger.info(f"Successfully sent email to {recipient_email}")
            else:
                self.logger.error(f"Failed to send email to {recipient_email}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error sending email through Yahoo Mail: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_send_error", f"Yahoo Mail send error: {e}")
            return False
    
    def is_authenticated(self, page: Page) -> bool:
        """
        Check if already authenticated with Yahoo Mail.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if authenticated
        """
        return self.auth.is_authenticated(page)
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "yahoo"
