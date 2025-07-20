# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush/Bulk-Mailer
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Browser-based email sender that replaces SMTP functionality.
#              Uses Playwright automation to send emails through web interfaces.
#
# Components: - Browser Instance Management
#             - Provider-Specific Automation
#             - Error Handling and Recovery
#             - Concurrent Browser Processing
#             - Cookie Validation and Management
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

import os
import time
from typing import Dict, Any, Optional, List
from .browser_handler import BrowserHandler
from .providers.protonmail import ProtonMailAutomation

class BrowserEmailSender:
    """Handles email sending through browser automation instead of SMTP."""
    
    def __init__(self, browser_config: Dict[str, Any], providers_config: Dict[str, Any], logger, base_dir: str = ".",
                 email_personalization: Dict[str, Any] = None, email_content: Dict[str, Any] = None):
        """
        Initialize browser email sender.

        Args:
            browser_config: Browser automation configuration
            providers_config: Provider-specific configurations
            logger: Logger instance
            base_dir: Base directory for HTML captures and logs
            email_personalization: Email personalization settings
            email_content: Email content settings
        """
        self.browser_config = browser_config
        self.providers_config = providers_config
        self.logger = logger
        self.base_dir = base_dir
        self.email_personalization = email_personalization
        self.email_content = email_content
        self.browser_handler = None
        self.provider_automations = {}
        self.active_contexts = {}  # Track active browser contexts by email
        
        # Initialize provider automations
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize provider-specific automation modules."""
        try:
            # Get base directory for HTML captures
            base_dir = getattr(self, 'base_dir', '.')

            # Initialize ProtonMail automation
            if self.providers_config.get("protonmail", {}).get("enabled", True):
                self.provider_automations["protonmail"] = ProtonMailAutomation(
                    self.providers_config["protonmail"],
                    self.logger,
                    base_dir,
                    self.email_personalization,
                    self.email_content
                )
                self.logger.info("ProtonMail automation initialized")
            
            # TODO: Add other providers (Gmail, Outlook, etc.) when implemented
            # if self.providers_config.get("gmail", {}).get("enabled", False):
            #     self.provider_automations["gmail"] = GmailAutomation(...)
            
            self.logger.info(f"Initialized {len(self.provider_automations)} provider automations")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize provider automations: {e}")
    
    def start_browser(self) -> bool:
        """
        Start browser handler and launch browser instance.
        
        Returns:
            bool: True if successful
        """
        try:
            if self.browser_handler is None:
                self.browser_handler = BrowserHandler(self.browser_config, self.logger)
            
            if not self.browser_handler.launch_browser():
                return False
            
            self.logger.info("Browser email sender started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start browser email sender: {e}")
            return False
    
    def validate_sender_cookies(self, sender_info: Dict[str, Any]) -> bool:
        """
        Validate that sender has valid cookies for browser automation.
        
        Args:
            sender_info: Sender configuration dictionary
            
        Returns:
            bool: True if cookies are valid
        """
        try:
            email = sender_info.get("email")
            cookie_file = sender_info.get("cookie_file")
            provider = sender_info.get("provider", "").lower()
            
            if not email or not cookie_file or not provider:
                self.logger.error(f"Missing browser automation configuration for {email}")
                return False
            
            if not os.path.exists(cookie_file):
                self.logger.error(f"Cookie file not found for {email}: {cookie_file}")
                return False
            
            if provider not in self.provider_automations:
                self.logger.error(f"Provider '{provider}' not supported for {email}")
                return False
            
            # Create context and validate login
            context = self.browser_handler.create_context_with_cookies(email, cookie_file)
            if not context:
                return False
            
            # Create page and validate login
            page = self.browser_handler.create_page(email)
            if not page:
                self.browser_handler.close_context(email)
                return False
            
            # Use provider-specific validation
            automation = self.provider_automations[provider]
            is_valid = automation.validate_login(page)

            if is_valid:
                self.logger.info(f"Cookies validated successfully for {email}")
                # Keep context open for future use
                self.active_contexts[email] = True
                page.close()  # Close page but keep context
                return True
            else:
                # For ProtonMail with fallback authentication, allow preparation to succeed
                # even if cookie validation fails, as long as we have password
                password = sender_info.get('password', '')
                if provider == 'protonmail' and password:
                    self.logger.warning(f"Cookie validation failed for {email}, but password available for fallback")
                    page.close()
                    # Keep context for later use with password authentication
                    self.active_contexts[email] = True
                    return True
                else:
                    self.logger.error(f"Cookie validation failed for {email} and no fallback available")
                    page.close()
                    self.browser_handler.close_context(email)
                    return False
            
        except Exception as e:
            self.logger.error(f"Error validating cookies for {email}: {e}")
            return False
    
    def send_email(self, sender_info: Dict[str, Any], recipient_email: str, subject: str, 
                   body_content: str, attachments: Optional[List[str]] = None, 
                   cid_attachments: Optional[Dict[str, str]] = None, 
                   content_type: str = "html") -> bool:
        """
        Send email using browser automation.
        
        Args:
            sender_info: Sender configuration dictionary
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            attachments: List of attachment file paths (not supported in browser mode)
            cid_attachments: CID attachments dictionary (not supported in browser mode)
            content_type: Content type (html or plain)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            sender_email = sender_info.get("email")
            provider = sender_info.get("provider", "").lower()
            
            self.logger.info(f"Sending email from {sender_email} to {recipient_email} via browser automation")
            
            # Check if browser is ready
            if not self.browser_handler or not self.browser_handler.is_browser_ready():
                self.logger.error("Browser not ready for email sending")
                return False
            
            # Check if provider is supported
            if provider not in self.provider_automations:
                self.logger.error(f"Provider '{provider}' not supported")
                return False
            
            # Create page using thread-safe browser handler (reuse context for same sender)
            page = self.browser_handler.create_page(sender_email)
            if not page:
                self.logger.error(f"Failed to create page for {sender_email} in thread")
                return False
            
            try:
                # Log attachment warning if attachments are provided
                if attachments or cid_attachments:
                    self.logger.warning("Attachments are not supported in browser automation mode")
                
                # Use provider-specific automation to send email
                automation = self.provider_automations[provider]

                # Use content processing workflow if available
                if hasattr(automation, 'compose_and_send_email_with_processing') and automation.content_processor:
                    success = automation.compose_and_send_email_with_processing(
                        page, recipient_email, sender_email, sender_info.get('password', '')
                    )
                else:
                    # Fallback to basic workflow
                    success = automation.compose_and_send_email(
                        page, recipient_email, subject, body_content, content_type,
                        sender_email, sender_info.get('password', '')
                    )
                
                if success:
                    self.logger.info(f"✓ Email sent successfully from {sender_email} to {recipient_email}")
                else:
                    self.logger.error(f"✗ Failed to send email from {sender_email} to {recipient_email}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error during email sending: {e}")
                
                # Take screenshot for debugging if enabled
                if self.browser_config.get("screenshot_on_error", True):
                    self.browser_handler.take_screenshot(page, f"send_error_{sender_email.replace('@', '_at_')}.png")
                
                return False
            
            finally:
                # DON'T close the page - keep it open for session reuse
                # The page will be closed when the sender's queue is empty
                # or when cleanup_sender is called
                self.logger.debug(f"Keeping page open for session reuse with {sender_email}")
                pass
                    
        except Exception as e:
            self.logger.error(f"Failed to send email from {sender_email} to {recipient_email}: {e}")
            return False
    
    def prepare_sender(self, sender_info: Dict[str, Any]) -> bool:
        """
        Prepare sender for email sending (lightweight validation only).
        Actual browser context creation happens in worker threads.

        Args:
            sender_info: Sender configuration dictionary

        Returns:
            bool: True if sender is ready
        """
        try:
            sender_email = sender_info.get("email")

            # For threading compatibility, skip heavy validation during preparation
            # Just check if we have basic requirements (email, provider, etc.)
            if not sender_email:
                self.logger.error("Sender email is required")
                return False

            provider = sender_info.get("provider", "").lower()
            if provider not in self.provider_automations:
                self.logger.error(f"Provider '{provider}' not supported")
                return False

            # Check if cookie file exists (if specified)
            cookie_file = sender_info.get('cookie_file', '')
            if cookie_file and not os.path.exists(cookie_file):
                self.logger.warning(f"Cookie file not found: {cookie_file}, will use password authentication")

            # Mark as prepared (actual validation happens during email sending)
            self.active_contexts[sender_email] = True
            self.logger.debug(f"Sender {sender_email} prepared for browser automation")
            return True

        except Exception as e:
            self.logger.error(f"Failed to prepare sender {sender_info.get('email')}: {e}")
            return False
    
    def cleanup_sender(self, sender_email: str):
        """
        Clean up resources for specific sender.
        
        Args:
            sender_email: Email address of sender to clean up
        """
        try:
            if sender_email in self.active_contexts:
                self.browser_handler.close_context(sender_email)
                del self.active_contexts[sender_email]
                self.logger.debug(f"Cleaned up resources for {sender_email}")
        except Exception as e:
            self.logger.error(f"Error cleaning up sender {sender_email}: {e}")
    
    def get_supported_providers(self) -> List[str]:
        """
        Get list of supported email providers.
        
        Returns:
            List of supported provider names
        """
        return list(self.provider_automations.keys())
    
    def is_provider_supported(self, provider: str) -> bool:
        """
        Check if provider is supported.
        
        Args:
            provider: Provider name
            
        Returns:
            bool: True if supported
        """
        return provider.lower() in self.provider_automations
    
    def close(self):
        """Clean up all browser resources."""
        try:
            # Clear active contexts
            self.active_contexts.clear()
            
            # Close browser handler
            if self.browser_handler:
                self.browser_handler.close_browser()
                self.browser_handler = None
            
            self.logger.info("Browser email sender closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing browser email sender: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get browser email sender statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "browser_ready": self.browser_handler.is_browser_ready() if self.browser_handler else False,
            "active_contexts": len(self.active_contexts),
            "supported_providers": self.get_supported_providers(),
            "provider_count": len(self.provider_automations)
        }
