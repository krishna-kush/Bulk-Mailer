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

import os
import sys
from typing import Dict, Any, Tuple

# Import mailer modules using relative imports
try:
    from ....mailer.email_personalizer import EmailPersonalizer
    from ....mailer.template_randomizer import TemplateRandomizer
except ImportError:
    # Fallback import method
    import importlib.util

    # Get the mailer directory
    current_dir = os.path.dirname(__file__)
    mailer_dir = os.path.abspath(os.path.join(current_dir, '..', '..', '..', 'mailer'))

    # Import EmailPersonalizer
    spec = importlib.util.spec_from_file_location("email_personalizer",
                                                  os.path.join(mailer_dir, "email_personalizer.py"))
    email_personalizer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(email_personalizer_module)
    EmailPersonalizer = email_personalizer_module.EmailPersonalizer

    # Import TemplateRandomizer
    spec = importlib.util.spec_from_file_location("template_randomizer",
                                                  os.path.join(mailer_dir, "template_randomizer.py"))
    template_randomizer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(template_randomizer_module)
    TemplateRandomizer = template_randomizer_module.TemplateRandomizer

class EmailContentProcessor:
    """Processes email content with all configuration settings applied."""
    
    def __init__(self, config: Dict[str, Any], email_personalization: Dict[str, Any], 
                 email_content: Dict[str, Any], logger, base_dir: str = "."):
        """
        Initialize email content processor.
        
        Args:
            config: Provider-specific configuration
            email_personalization: Email personalization settings
            email_content: Email content settings
            logger: Logger instance
            base_dir: Base directory for template files
        """
        self.config = config
        self.email_personalization = email_personalization
        self.email_content = email_content
        self.logger = logger
        self.base_dir = base_dir

        # Debug: Log personalization configuration
        self.logger.info(f"🔍 EMAIL_PERSONALIZATION CONFIG: {email_personalization}")

        # Initialize email personalizer
        self.email_personalizer = EmailPersonalizer(
            config_settings=email_personalization,
            base_dir=base_dir,
            logger=logger
        )
        
        # Initialize template randomizer
        self.template_randomizer = TemplateRandomizer(logger=logger)
    
    def process_email_content(self, recipient_email: str) -> Tuple[str, str, str]:
        """
        Process complete email content with all configuration settings.
        
        Args:
            recipient_email: Recipient email address
            
        Returns:
            Tuple of (subject, body_content, content_type)
        """
        try:
            # Step 1: Load raw content from config and templates
            raw_subject = self.email_content.get('subject', 'Default Subject')
            content_type = self.email_content.get('content_type', 'html')
            
            # Load body content from template file
            raw_body_content = self._load_body_template(content_type)
            
            self.logger.debug(f"Raw subject: {raw_subject}")
            self.logger.debug(f"Raw body length: {len(raw_body_content)} characters")
            
            # Step 2: Process manual randomization if enabled
            processed_subject = self._process_manual_randomization(raw_subject)
            processed_body = self._process_manual_randomization(raw_body_content)
            
            self.logger.debug(f"After randomization - Subject: {processed_subject}")
            self.logger.debug(f"After randomization - Body length: {len(processed_body)} characters")
            
            # Step 3: Apply personalization if enabled
            personalization_enabled = self.email_personalization.get('enable_personalization', False)
            self.logger.info(f"🔍 PERSONALIZATION DEBUG: enabled={personalization_enabled}")

            if personalization_enabled:
                # Create recipient data
                recipient_data = {'email': recipient_email}
                self.logger.info(f"🔍 PERSONALIZATION DEBUG: recipient_data={recipient_data}")

                # Debug: Show content BEFORE personalization
                self.logger.info(f"🔍 BEFORE personalization - Subject: '{processed_subject}'")
                self.logger.info(f"🔍 BEFORE personalization - Body preview: '{processed_body[:100]}...'")

                # Apply personalization
                processed_subject = self.email_personalizer.personalize_email(
                    processed_subject, recipient_data
                )
                processed_body = self.email_personalizer.personalize_email(
                    processed_body, recipient_data
                )

                # Debug: Show content AFTER personalization
                self.logger.info(f"🔍 AFTER personalization - Subject: '{processed_subject}'")
                self.logger.info(f"🔍 AFTER personalization - Body preview: '{processed_body[:100]}...'")
                self.logger.info("✅ Applied email personalization")
            else:
                self.logger.warning("❌ Personalization is DISABLED - content will show raw template syntax")
            
            # Step 4: Apply HTML obfuscation if enabled and content is HTML
            if (content_type.lower() == 'html' and 
                self.email_personalization.get('enable_html_obfuscation', False)):
                
                processed_body = self.email_personalizer._apply_html_obfuscation(processed_body)
                self.logger.debug("Applied HTML obfuscation")
            
            self.logger.info(f"Email content processed successfully for {recipient_email}")
            return processed_subject, processed_body, content_type
            
        except Exception as e:
            self.logger.error(f"Failed to process email content: {e}")
            # Return raw content as fallback
            return (
                self.email_content.get('subject', 'Default Subject'),
                self._load_body_template(self.email_content.get('content_type', 'html')),
                self.email_content.get('content_type', 'html')
            )
    
    def _load_body_template(self, content_type: str) -> str:
        """
        Load body template from file.
        
        Args:
            content_type: Content type (html or plain)
            
        Returns:
            Template content
        """
        try:
            # Determine template file based on content type
            if content_type.lower() == 'html':
                body_file = self.email_content.get('body_html_file', 'templates/html/i_bet.main.html')
            else:
                body_file = self.email_content.get('body_text_file', 'templates/text/i_bet.main.txt')
            
            # Read template file
            body_file_path = os.path.join(self.base_dir, body_file)
            if os.path.exists(body_file_path):
                with open(body_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.logger.debug(f"Loaded template from: {body_file}")
                return content
            else:
                self.logger.warning(f"Template file not found: {body_file_path}")
                return f"Default {content_type} email content with manual randomization features."
                
        except Exception as e:
            self.logger.error(f"Failed to load body template: {e}")
            return f"Default {content_type} email content."
    
    def _process_manual_randomization(self, content: str) -> str:
        """
        Process manual randomization syntax in content.
        
        Args:
            content: Content with randomization syntax
            
        Returns:
            Processed content with randomization applied
        """
        try:
            # Check if manual randomization is enabled
            randomization_enabled = self.email_personalization.get('enable_manual_randomization', True)
            
            if not randomization_enabled:
                self.logger.debug("Manual randomization disabled")
                return content
            
            # Process randomization syntax
            processed_content = self.template_randomizer.process_template(content)
            
            # Log randomization changes
            original_patterns = len(self.template_randomizer.randomization_pattern.findall(content))
            remaining_patterns = len(self.template_randomizer.randomization_pattern.findall(processed_content))
            changes = original_patterns - remaining_patterns
            
            if changes > 0:
                self.logger.debug(f"Processed {changes} manual randomization patterns")
            
            return processed_content
            
        except Exception as e:
            self.logger.error(f"Failed to process manual randomization: {e}")
            return content
    
    def preview_randomization_variations(self, content: str, count: int = 3) -> list:
        """
        Preview multiple randomization variations of content.
        
        Args:
            content: Content with randomization syntax
            count: Number of variations to generate
            
        Returns:
            List of content variations
        """
        try:
            if not self.email_personalization.get('enable_manual_randomization', True):
                return [content] * count
            
            variations = []
            for _ in range(count):
                variation = self.template_randomizer.process_template(content)
                variations.append(variation)
            
            return variations
            
        except Exception as e:
            self.logger.error(f"Failed to generate randomization variations: {e}")
            return [content] * count
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """
        Get summary of processing settings.
        
        Returns:
            Dictionary with processing settings summary
        """
        return {
            "manual_randomization_enabled": self.email_personalization.get('enable_manual_randomization', True),
            "personalization_enabled": self.email_personalization.get('enable_personalization', False),
            "html_obfuscation_enabled": self.email_personalization.get('enable_html_obfuscation', False),
            "html_obfuscation_intensity": self.email_personalization.get('html_obfuscation_intensity', 'medium'),
            "content_type": self.email_content.get('content_type', 'html'),
            "body_html_file": self.email_content.get('body_html_file', 'Not specified'),
            "body_text_file": self.email_content.get('body_text_file', 'Not specified')
        }
