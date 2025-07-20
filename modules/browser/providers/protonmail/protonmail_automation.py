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
from .authentication import ProtonMailAuthentication
from .email_composer import ProtonMailEmailComposer
from .email_content_processor import EmailContentProcessor

class ProtonMailAutomation:
    """Main ProtonMail automation class that coordinates authentication and email composition."""

    def __init__(self, config: Dict[str, Any], logger, base_dir: str = "",
                 email_personalization: Dict[str, Any] = None, email_content: Dict[str, Any] = None):
        """
        Initialize ProtonMail automation with configuration.

        Args:
            config: Provider-specific configuration
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
        self.html_capture = HTMLCapture(base_dir, logger) if (base_dir and html_capture_enabled) else None

        # Initialize authentication and email composition modules
        self.auth = ProtonMailAuthentication(config, logger, self.html_capture)
        self.composer = ProtonMailEmailComposer(config, logger, self.html_capture)

        # Initialize email content processor if settings provided
        if email_personalization and email_content:
            self.content_processor = EmailContentProcessor(
                config, email_personalization, email_content, logger, base_dir
            )
        else:
            self.content_processor = None
    
    def authenticate_with_fallback(self, page: Page, email: str, password: str = "") -> bool:
        """
        Attempt authentication with fallback from cookies to password.
        
        Args:
            page: Playwright page instance
            email: Email address for login
            password: Password for fallback authentication
            
        Returns:
            bool: True if authentication successful
        """
        return self.auth.authenticate_with_fallback(page, email, password)
    
    def navigate_to_mail(self, page: Page) -> bool:
        """
        Navigate to ProtonMail and verify login status.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if successfully navigated and logged in
        """
        return self.auth.navigate_to_mail(page)
    
    def login_with_password(self, page: Page, email: str, password: str) -> bool:
        """
        Perform password-based login to ProtonMail.

        Args:
            page: Playwright page instance
            email: Email address
            password: Password

        Returns:
            bool: True if login successful
        """
        return self.auth.login_with_password(page, email, password)

    def _is_already_logged_in(self, page: Page) -> bool:
        """
        Check if user is already logged in to ProtonMail.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if already logged in
        """
        try:
            # Use the same selectors as authentication system
            compose_selectors = [
                '[data-testid="sidebar:compose"]',
                'button[title*="compose"]',
                'button[title*="Compose"]',
                '.compose-button',
                '[aria-label*="compose"]'
            ]

            # Try each compose button selector
            for selector in compose_selectors:
                try:
                    page.wait_for_selector(selector, timeout=2000)
                    self.logger.debug(f"Found compose button: {selector}")
                    return True
                except:
                    continue

            # If no compose button found, not logged in
            return False

        except Exception as e:
            self.logger.debug(f"Login check failed: {e}")
            return False
    
    def compose_and_send_email_with_processing(self, page: Page, recipient_email: str,
                                             email: str = "", password: str = "") -> bool:
        """
        Complete email composition and sending workflow with full content processing.

        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            email: Sender email for authentication
            password: Password for fallback authentication

        Returns:
            bool: True if email sent successfully
        """
        try:
            # Check if already logged in first (avoid unnecessary re-authentication)
            if not self._is_already_logged_in(page):
                # Only authenticate if not already logged in
                if not self.authenticate_with_fallback(page, email, password):
                    return False
            else:
                self.logger.debug("Already logged in, skipping authentication")

            # Process email content with all configuration settings
            if self.content_processor:
                subject, body_content, content_type = self.content_processor.process_email_content(recipient_email)
                self.logger.info(f"Email content processed with all settings applied")
                self.logger.debug(f"Processed subject: {subject}")
                self.logger.debug(f"Content type: {content_type}")
                self.logger.debug(f"Body length: {len(body_content)} characters")
            else:
                # Fallback to basic content
                subject = "Default Subject"
                body_content = "Default email content"
                content_type = "html"
                self.logger.warning("No content processor available, using default content")

            # Compose and send email
            return self.composer.compose_and_send_email(page, recipient_email, subject, body_content, content_type)

        except Exception as e:
            self.logger.error(f"Failed to compose and send email with processing: {e}")

            # Capture error state
            if self.html_capture:
                self.html_capture.capture_html(page, "email_send_error",
                                             f"Error during email sending: {str(e)}")
            return False

    def compose_and_send_email(self, page: Page, recipient_email: str, subject: str,
                              body_content: str, content_type: str = "html",
                              email: str = "", password: str = "") -> bool:
        """
        Complete email composition and sending workflow with fallback authentication.
        
        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            content_type: Content type (html or plain)
            email: Sender email for authentication
            password: Password for fallback authentication
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Check if already logged in first (avoid unnecessary re-authentication)
            if not self._is_already_logged_in(page):
                # Only authenticate if not already logged in
                if not self.authenticate_with_fallback(page, email, password):
                    return False
            else:
                self.logger.debug("Already logged in, skipping authentication")
            
            # Compose and send email
            return self.composer.compose_and_send_email(page, recipient_email, subject, body_content, content_type)
            
        except Exception as e:
            self.logger.error(f"Failed to compose and send email: {e}")
            
            # Capture error state
            if self.html_capture:
                self.html_capture.capture_html(page, "email_send_error", 
                                             f"Error during email sending: {str(e)}")
            return False
    
    def open_compose(self, page: Page) -> bool:
        """
        Open the email compose window.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if compose window opened successfully
        """
        return self.composer.open_compose(page)
    
    def fill_recipient(self, page: Page, recipient_email: str) -> bool:
        """
        Fill the recipient email field.
        
        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            
        Returns:
            bool: True if recipient filled successfully
        """
        return self.composer.fill_recipient(page, recipient_email)
    
    def fill_subject(self, page: Page, subject: str) -> bool:
        """
        Fill the email subject field.
        
        Args:
            page: Playwright page instance
            subject: Email subject
            
        Returns:
            bool: True if subject filled successfully
        """
        return self.composer.fill_subject(page, subject)
    
    def fill_body(self, page: Page, body_content: str, content_type: str = "html") -> bool:
        """
        Fill the email body content.
        
        Args:
            page: Playwright page instance
            body_content: Email body content
            content_type: Content type (html or plain)
            
        Returns:
            bool: True if body filled successfully
        """
        return self.composer.fill_body(page, body_content, content_type)
    
    def send_email(self, page: Page) -> bool:
        """
        Send the composed email.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if email sent successfully
        """
        return self.composer.send_email(page)

    def validate_login(self, page: Page) -> bool:
        """
        Validate if the user is logged in to ProtonMail.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if logged in successfully
        """
        try:
            # Use the same logic as navigate_to_mail to check login status
            return self.auth.navigate_to_mail(page)
        except Exception as e:
            self.logger.error(f"Error validating login: {e}")
            return False
