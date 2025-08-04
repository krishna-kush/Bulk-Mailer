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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mailer_dir = os.path.join(current_dir, '..', '..', '..', '..', 'mailer')
    
    # Load email_personalizer module
    personalizer_path = os.path.join(mailer_dir, 'email_personalizer.py')
    spec = importlib.util.spec_from_file_location("email_personalizer", personalizer_path)
    personalizer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(personalizer_module)
    EmailPersonalizer = personalizer_module.EmailPersonalizer
    
    # Load template_randomizer module
    randomizer_path = os.path.join(mailer_dir, 'template_randomizer.py')
    spec = importlib.util.spec_from_file_location("template_randomizer", randomizer_path)
    randomizer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(randomizer_module)
    TemplateRandomizer = randomizer_module.TemplateRandomizer

class EmailContentProcessor:
    """Processes email content with personalization and randomization for Yahoo Mail."""
    
    def __init__(self, email_personalization: Dict[str, Any], email_content: Dict[str, Any], logger):
        """
        Initialize email content processor.
        
        Args:
            email_personalization: Email personalization settings
            email_content: Email content settings
            logger: Logger instance
        """
        self.logger = logger
        self.email_personalization = email_personalization
        self.email_content = email_content
        
        # Initialize personalizer and randomizer
        try:
            # Create a mock config loader for the personalizer
            class MockConfigLoader:
                def get_section(self, section_name, default=None):
                    if section_name == 'EMAIL_PERSONALIZATION':
                        return email_personalization
                    elif section_name == 'EMAIL_CONTENT':
                        return email_content
                    return default or {}
            
            mock_config = MockConfigLoader()
            self.personalizer = EmailPersonalizer(mock_config, logger)
            self.randomizer = TemplateRandomizer(logger)
            
            self.logger.debug("Email content processor initialized for Yahoo Mail")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize email content processor: {e}")
            self.personalizer = None
            self.randomizer = None
    
    def process_email_content(self, subject: str, body_content: str, 
                            recipient_email: str, recipient_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Process email content with personalization and randomization.
        
        Args:
            subject: Email subject template
            body_content: Email body template
            recipient_email: Recipient email address
            recipient_data: Additional recipient data
            
        Returns:
            Tuple of (processed_subject, processed_body)
        """
        try:
            self.logger.info("🔍 PERSONALIZATION DEBUG: enabled=True")
            self.logger.info(f"🔍 PERSONALIZATION DEBUG: recipient_data={recipient_data}")
            
            # Add email to recipient data
            full_recipient_data = {'email': recipient_email}
            full_recipient_data.update(recipient_data)
            
            self.logger.info(f"🔍 BEFORE personalization - Subject: '{subject}'")
            self.logger.info(f"🔍 BEFORE personalization - Body preview: '{body_content[:100]}...'")
            
            processed_subject = subject
            processed_body = body_content
            
            # Apply personalization if available
            if self.personalizer:
                processed_subject = self.personalizer.personalize_content(subject, full_recipient_data)
                processed_body = self.personalizer.personalize_content(body_content, full_recipient_data)
                self.logger.info("✅ Applied email personalization")
            
            # Apply manual randomization if available
            if self.randomizer:
                processed_subject = self.randomizer.process_manual_randomization(processed_subject)
                processed_body = self.randomizer.process_manual_randomization(processed_body)
                self.logger.info("✅ Applied manual randomization")
            
            self.logger.info(f"🔍 AFTER personalization - Subject: '{processed_subject}'")
            self.logger.info(f"🔍 AFTER personalization - Body preview: '{processed_body[:100]}...'")
            
            self.logger.info(f"Email content processed successfully for {recipient_email}")
            
            return processed_subject, processed_body
            
        except Exception as e:
            self.logger.error(f"Error processing email content: {e}")
            return subject, body_content
