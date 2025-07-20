# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Unified email sender that can switch between SMTP and browser
#              automation modes based on configuration settings.
#
# Components: - Mode Detection and Switching
#             - SMTP Email Sending
#             - Browser Automation Email Sending
#             - Unified Interface for Both Modes
#             - Error Handling and Fallback
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

from typing import Dict, Any, Optional, List
from .email_sender import EmailSender
from ..browser.browser_email_sender import BrowserEmailSender

class UnifiedEmailSender:
    """Unified email sender that supports both SMTP and browser automation modes."""

    def __init__(self, smtp_configs: Dict[str, Any], browser_config: Dict[str, Any],
                 providers_config: Dict[str, Any], sending_mode: str, logger, email_composer=None, base_dir: str = "."):
        """
        Initialize unified email sender.

        Args:
            smtp_configs: SMTP configuration dictionary
            browser_config: Browser automation configuration
            providers_config: Provider-specific configurations
            sending_mode: Sending mode ('smtp' or 'browser')
            logger: Logger instance
            email_composer: Email composer instance
            base_dir: Base directory for HTML captures and logs
        """
        self.smtp_configs = smtp_configs
        self.browser_config = browser_config
        self.providers_config = providers_config
        self.sending_mode = sending_mode.lower()
        self.logger = logger
        self.email_composer = email_composer
        self.base_dir = base_dir
        
        # Initialize senders based on mode
        self.smtp_sender = None
        self.browser_sender = None
        
        self._initialize_senders()
    
    def _initialize_senders(self):
        """Initialize appropriate senders based on sending mode."""
        try:
            if self.sending_mode == "smtp":
                self.logger.info("Initializing SMTP email sender...")
                self.smtp_sender = EmailSender(self.smtp_configs, self.logger, self.email_composer)
                self.logger.info("SMTP email sender initialized successfully")
                
            elif self.sending_mode == "browser":
                self.logger.info("Initializing browser automation email sender...")
                
                # Check if browser automation is enabled
                if not self.browser_config.get("enable_browser_automation", True):
                    self.logger.warning("Browser automation is disabled in config, falling back to SMTP mode")
                    self.sending_mode = "smtp"
                    self.smtp_sender = EmailSender(self.smtp_configs, self.logger, self.email_composer)
                    return
                
                # Get email settings for browser automation
                import sys
                import os
                sys.path.insert(0, os.path.join(self.base_dir))
                from config.config_loader import ConfigLoader
                config_loader = ConfigLoader(self.base_dir)
                email_personalization = config_loader.get_email_personalization_settings()
                email_content = config_loader.get_email_content_settings()

                self.browser_sender = BrowserEmailSender(
                    self.browser_config,
                    self.providers_config,
                    self.logger,
                    self.base_dir,
                    email_personalization,
                    email_content
                )
                
                # Start browser
                if not self.browser_sender.start_browser():
                    self.logger.error("Failed to start browser, falling back to SMTP mode")
                    self.sending_mode = "smtp"
                    self.smtp_sender = EmailSender(self.smtp_configs, self.logger, self.email_composer)
                    return
                
                self.logger.info("Browser automation email sender initialized successfully")
                
            else:
                self.logger.error(f"Invalid sending mode: {self.sending_mode}. Defaulting to SMTP.")
                self.sending_mode = "smtp"
                self.smtp_sender = EmailSender(self.smtp_configs, self.logger, self.email_composer)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize email senders: {e}")
            # Fallback to SMTP mode
            self.sending_mode = "smtp"
            self.smtp_sender = EmailSender(self.smtp_configs, self.logger, self.email_composer)
    
    def send_email(self, sender_email: str, sender_password: str, recipient_email: str, 
                   subject: str, body_content: str, attachments: Optional[List[str]] = None, 
                   cid_attachments: Optional[Dict[str, str]] = None, smtp_id: str = "default", 
                   content_type: str = "html", sender_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send email using the configured sending mode.
        
        Args:
            sender_email: Sender email address
            sender_password: Sender password (SMTP mode only)
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            attachments: List of attachment file paths
            cid_attachments: CID attachments dictionary
            smtp_id: SMTP configuration ID (SMTP mode only)
            content_type: Content type (html or plain)
            sender_info: Complete sender information dictionary (browser mode)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if self.sending_mode == "smtp":
                return self._send_via_smtp(
                    sender_email, sender_password, recipient_email, subject, 
                    body_content, attachments, cid_attachments, smtp_id, content_type
                )
            elif self.sending_mode == "browser":
                return self._send_via_browser(
                    sender_info or {"email": sender_email}, recipient_email, subject, 
                    body_content, attachments, cid_attachments, content_type
                )
            else:
                self.logger.error(f"Invalid sending mode: {self.sending_mode}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send email from {sender_email} to {recipient_email}: {e}")
            return False
    
    def _send_via_smtp(self, sender_email: str, sender_password: str, recipient_email: str, 
                       subject: str, body_content: str, attachments: Optional[List[str]], 
                       cid_attachments: Optional[Dict[str, str]], smtp_id: str, 
                       content_type: str) -> bool:
        """Send email via SMTP."""
        if not self.smtp_sender:
            self.logger.error("SMTP sender not initialized")
            return False
        
        return self.smtp_sender.send_email(
            sender_email, sender_password, recipient_email, subject, body_content,
            attachments, cid_attachments, smtp_id, content_type
        )
    
    def _send_via_browser(self, sender_info: Dict[str, Any], recipient_email: str, 
                          subject: str, body_content: str, attachments: Optional[List[str]], 
                          cid_attachments: Optional[Dict[str, str]], content_type: str) -> bool:
        """Send email via browser automation."""
        if not self.browser_sender:
            self.logger.error("Browser sender not initialized")
            return False
        
        return self.browser_sender.send_email(
            sender_info, recipient_email, subject, body_content, 
            attachments, cid_attachments, content_type
        )
    
    def prepare_sender(self, sender_info: Dict[str, Any]) -> bool:
        """
        Prepare sender for email sending (browser mode only).
        
        Args:
            sender_info: Sender configuration dictionary
            
        Returns:
            bool: True if sender is ready
        """
        if self.sending_mode == "browser" and self.browser_sender:
            return self.browser_sender.prepare_sender(sender_info)
        return True  # SMTP mode doesn't need preparation
    
    def validate_sender_configuration(self, sender_info: Dict[str, Any]) -> bool:
        """
        Validate sender configuration for current mode.
        
        Args:
            sender_info: Sender configuration dictionary
            
        Returns:
            bool: True if configuration is valid
        """
        try:
            email = sender_info.get("email")
            if not email:
                self.logger.error("Sender email is required")
                return False
            
            if self.sending_mode == "smtp":
                # Validate SMTP configuration
                password = sender_info.get("password")
                smtp_id = sender_info.get("smtp_id", "default")
                
                if not password:
                    self.logger.error(f"Password required for SMTP mode: {email}")
                    return False
                
                if smtp_id not in self.smtp_configs:
                    self.logger.error(f"SMTP configuration '{smtp_id}' not found for {email}")
                    return False
                
                return True
                
            elif self.sending_mode == "browser":
                # Validate browser automation configuration
                provider = sender_info.get("provider")
                cookie_file = sender_info.get("cookie_file")
                
                if not provider:
                    self.logger.error(f"Provider required for browser mode: {email}")
                    return False
                
                # Cookie file is optional - password authentication can be used as fallback
                if not cookie_file:
                    password = sender_info.get('password', '')
                    if not password:
                        self.logger.error(f"Either cookie file or password required for browser mode: {email}")
                        return False
                    self.logger.debug(f"No cookie file for {email}, will use password authentication")
                
                if not self.browser_sender.is_provider_supported(provider):
                    self.logger.error(f"Provider '{provider}' not supported for {email}")
                    return False
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating sender configuration: {e}")
            return False
    
    def get_sending_mode(self) -> str:
        """Get current sending mode."""
        return self.sending_mode
    
    def get_supported_providers(self) -> List[str]:
        """Get list of supported providers (browser mode only)."""
        if self.browser_sender:
            return self.browser_sender.get_supported_providers()
        return []
    
    def cleanup_sender(self, sender_email: str):
        """Clean up resources for specific sender."""
        if self.sending_mode == "browser" and self.browser_sender:
            self.browser_sender.cleanup_sender(sender_email)
    
    def close(self):
        """Clean up all resources."""
        try:
            if self.browser_sender:
                self.browser_sender.close()
                self.browser_sender = None
            
            # SMTP sender doesn't need explicit cleanup
            self.smtp_sender = None
            
            self.logger.info("Unified email sender closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing unified email sender: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get email sender statistics."""
        stats = {
            "sending_mode": self.sending_mode,
            "smtp_initialized": self.smtp_sender is not None,
            "browser_initialized": self.browser_sender is not None
        }
        
        if self.browser_sender:
            stats.update(self.browser_sender.get_stats())
        
        return stats
