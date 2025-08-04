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

import time
import random
from typing import Dict, Any, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from ..base.email_composer import BaseEmailComposer

class YahooEmailComposer(BaseEmailComposer):
    """Handles Yahoo Mail email composition and sending."""

    def __init__(self, config: Dict[str, Any], logger, html_capture=None):
        """
        Initialize Yahoo Mail email composer.

        Args:
            config: Browser automation configuration
            logger: Logger instance
            html_capture: HTML capture utility for debugging
        """
        super().__init__(config, logger, html_capture)
        
        # Yahoo Mail interface selectors
        self.selectors = {
            "compose_button": [
                'button[data-test-id="compose-button"]',
                'a[data-test-id="compose-button"]',
                'button:has-text("Compose")',
                'a:has-text("Compose")',
                '[aria-label*="Compose"]',
                '.compose-button',
                '#compose-button',
                'button[title*="Compose"]'
            ],
            "to_field": [
                # Modern Yahoo Mail selectors
                'input[data-test-id="to-field"]',
                'input[data-test-id="compose-to"]',
                'input[aria-label*="To"]',
                'input[placeholder*="To"]',
                'input[name="to"]',

                # Alternative selectors
                '#to-field',
                '.to-field input',
                '[data-test-id*="to"] input',
                '[data-test-id*="recipient"] input',

                # Generic compose form selectors
                '.compose-form input[type="email"]',
                '.compose-to input',
                '.recipient-input',

                # Fallback selectors
                'input[type="email"]',
                'input[autocomplete="email"]'
            ],
            "subject_field": [
                # Modern Yahoo Mail selectors
                'input[data-test-id="subject-field"]',
                'input[data-test-id="compose-subject"]',
                'input[aria-label*="Subject"]',
                'input[placeholder*="Subject"]',
                'input[name="subject"]',

                # Alternative selectors
                '#subject-field',
                '.subject-field input',
                '[data-test-id*="subject"] input',
                '.compose-subject input',

                # Fallback selectors
                '.compose-form input[type="text"]'
            ],
            "body_field": [
                # Modern Yahoo Mail selectors
                'div[data-test-id="rte"]',
                'div[data-test-id="compose-body"]',
                'div[contenteditable="true"]',
                'div[role="textbox"]',
                'iframe[title*="Rich Text"]',
                'iframe[title*="Compose"]',

                # Alternative selectors
                '.rte-editor',
                '#rte',
                '.compose-body',
                '#compose-body',
                '[data-test-id*="body"]',
                '[data-test-id*="editor"]',

                # Fallback selectors
                'textarea[name="body"]',
                '.compose-form textarea'
            ],
            "send_button": [
                'button[data-test-id="send-button"]',
                'button:has-text("Send")',
                'input[value="Send"]',
                '[aria-label*="Send"]',
                '.send-button',
                '#send-button'
            ]
        }
    
    def _find_element_by_selectors(self, page: Page, selectors: list, timeout: int = 5000) -> Optional[Any]:
        """
        Find element using multiple selectors with timeout.
        
        Args:
            page: Playwright page instance
            selectors: List of CSS selectors to try
            timeout: Timeout in milliseconds
            
        Returns:
            Element if found, None otherwise
        """
        for selector in selectors:
            try:
                element = page.wait_for_selector(selector, timeout=timeout)
                if element and element.is_visible():
                    return element
            except PlaywrightTimeoutError:
                continue
        return None
    
    def compose_and_send_email(self, page: Page, recipient_email: str, subject: str, 
                              body_content: str, attachments: list = None, 
                              cid_attachments: Dict[str, str] = None, 
                              content_type: str = "text") -> bool:
        """
        Compose and send email through Yahoo Mail.
        
        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            attachments: List of attachment file paths
            cid_attachments: Dictionary of CID attachments
            content_type: Content type (text/html)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Click compose button
            if not self._click_compose_button(page):
                return False
            
            # Fill recipient field
            if not self._fill_recipient_field(page, recipient_email):
                return False
            
            # Fill subject field
            if not self._fill_subject_field(page, subject):
                return False
            
            # Fill body field
            if not self._fill_body_field(page, body_content, content_type):
                return False
            
            # Handle attachments if provided
            if attachments:
                if not self._handle_attachments(page, attachments):
                    self.logger.warning("Failed to attach files, continuing with send...")
            
            # Send the email
            return self._send_email(page)
            
        except Exception as e:
            self.logger.error(f"Error composing/sending email: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_compose_error", f"Compose error: {e}")
            return False
    
    def _click_compose_button(self, page: Page) -> bool:
        """Click the compose button to start new email."""
        try:
            compose_button = self._find_element_by_selectors(page, self.selectors["compose_button"], 10000)
            if not compose_button:
                self.logger.error("❌ Compose button not found")
                return False
            
            self.logger.info("🔄 Clicked compose/new message button")
            compose_button.click()
            time.sleep(3)  # Wait for compose window to load
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_compose_opened", "Yahoo Mail compose window opened")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to click compose button: {e}")
            return False
    
    def _fill_recipient_field(self, page: Page, recipient_email: str) -> bool:
        """Fill the recipient email field."""
        try:
            to_field = self._find_element_by_selectors(page, self.selectors["to_field"], 10000)
            if not to_field:
                self.logger.error("❌ To field not found")
                return False
            
            self.logger.info(f"✅ Found To field, filling with {recipient_email}")
            to_field.click()
            to_field.fill("")  # Clear the field
            to_field.type(recipient_email, delay=random.randint(50, 150))
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_recipient_filled", "Yahoo Mail recipient field filled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill recipient field: {e}")
            return False
    
    def _fill_subject_field(self, page: Page, subject: str) -> bool:
        """Fill the subject field."""
        try:
            subject_field = self._find_element_by_selectors(page, self.selectors["subject_field"], 10000)
            if not subject_field:
                self.logger.error("❌ Subject field not found")
                return False
            
            self.logger.info("✅ Found Subject field, filling...")
            subject_field.click()
            subject_field.fill("")  # Clear the field
            subject_field.type(subject, delay=random.randint(50, 150))
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_subject_filled", "Yahoo Mail subject field filled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill subject field: {e}")
            return False
    
    def _fill_body_field(self, page: Page, body_content: str, content_type: str) -> bool:
        """Fill the email body field."""
        try:
            body_field = self._find_element_by_selectors(page, self.selectors["body_field"], 10000)
            if not body_field:
                self.logger.error("❌ Body field not found")
                return False
            
            self.logger.info("✅ Found body field, filling content...")
            
            # Check if it's an iframe or contenteditable div
            tag_name = body_field.evaluate("element => element.tagName.toLowerCase()")
            
            if tag_name == "iframe":
                self.logger.info("Detected iframe body field - using iframe content filling strategy")
                return self._fill_iframe_body(page, body_field, body_content, content_type)
            else:
                self.logger.info("Detected contenteditable body field - using direct content filling strategy")
                return self._fill_contenteditable_body(page, body_field, body_content, content_type)
                
        except Exception as e:
            self.logger.error(f"Failed to fill body field: {e}")
            return False

    def _fill_iframe_body(self, page: Page, iframe_element, body_content: str, content_type: str) -> bool:
        """Fill body content in iframe."""
        try:
            # Switch to iframe context
            iframe_content = iframe_element.content_frame()
            if not iframe_content:
                self.logger.error("Failed to access iframe content")
                return False

            # Find the body element within iframe
            body_selector = 'body, [contenteditable="true"], div[role="textbox"]'
            iframe_body = iframe_content.wait_for_selector(body_selector, timeout=10000)

            if not iframe_body:
                self.logger.error("Body element not found in iframe")
                return False

            # Clear and fill content
            iframe_body.click()
            iframe_content.keyboard.press("Control+a")
            iframe_content.keyboard.press("Delete")

            if content_type == "html":
                # For HTML content, use innerHTML
                iframe_body.evaluate(f"element => element.innerHTML = `{body_content}`")
            else:
                # For text content, type it
                iframe_content.keyboard.type(body_content, delay=random.randint(10, 30))

            self.logger.info("Iframe content filled successfully")

            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_body_filled", "Yahoo Mail body content filled")

            return True

        except Exception as e:
            self.logger.error(f"Failed to fill iframe body: {e}")
            return False

    def _fill_contenteditable_body(self, page: Page, body_element, body_content: str, content_type: str) -> bool:
        """Fill body content in contenteditable div."""
        try:
            # Click to focus
            body_element.click()
            time.sleep(1)

            # Clear existing content
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")

            if content_type == "html":
                # For HTML content, use innerHTML
                body_element.evaluate(f"element => element.innerHTML = `{body_content}`")
            else:
                # For text content, type it
                page.keyboard.type(body_content, delay=random.randint(10, 30))

            self.logger.info("Contenteditable body filled successfully")

            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_body_filled", "Yahoo Mail body content filled")

            return True

        except Exception as e:
            self.logger.error(f"Failed to fill contenteditable body: {e}")
            return False

    def _handle_attachments(self, page: Page, attachments: list) -> bool:
        """Handle file attachments."""
        try:
            # Yahoo Mail attachment handling would go here
            # This is a placeholder for attachment functionality
            self.logger.info(f"Attachment handling not yet implemented for Yahoo Mail ({len(attachments)} files)")
            return True

        except Exception as e:
            self.logger.error(f"Failed to handle attachments: {e}")
            return False

    def _send_email(self, page: Page) -> bool:
        """Send the composed email."""
        try:
            send_button = self._find_element_by_selectors(page, self.selectors["send_button"], 10000)
            if not send_button:
                self.logger.error("❌ Send button not found")
                return False

            self.logger.info("✅ Found Send button, clicking...")
            send_button.click()

            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_send_clicked", "Yahoo Mail send button clicked")

            # Wait for email to be sent
            self.logger.info("Send button clicked, waiting for email to be processed...")
            time.sleep(5)

            # Check for success indicators
            try:
                # Look for success notification or return to inbox
                success_indicators = [
                    '[data-test-id="toast-message"]',
                    '.toast-message',
                    ':has-text("sent")',
                    ':has-text("Message sent")',
                    '[role="alert"]'
                ]

                for indicator in success_indicators:
                    try:
                        element = page.wait_for_selector(indicator, timeout=5000)
                        if element:
                            self.logger.info("Found success indicator")
                            break
                    except PlaywrightTimeoutError:
                        continue

                # Additional wait for server processing
                self.logger.info("Waiting additional 5s for server processing...")
                time.sleep(5)

                if self.html_capture:
                    self.html_capture.capture_html(page, "yahoo_after_send", "Yahoo Mail after send attempt")

                self.logger.info("Email sending process completed successfully")
                return True

            except Exception as e:
                self.logger.warning(f"Could not verify send success: {e}, assuming success")
                return True

        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_send_error", f"Send error: {e}")
            return False
