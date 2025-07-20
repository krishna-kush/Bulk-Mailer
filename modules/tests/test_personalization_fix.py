#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Email Personalization Fix Test
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Test email template personalization with recipient_name fallback
#              to "There" when no recipient name is provided.
#
# License: MIT License
# Created: 2025
#
# ================================================================================

import os
import sys

# Add modules to path - go up two levels to reach mailer root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.core.utils import extract_name_from_email
from modules.mailer.email_personalizer import EmailPersonalizer
from modules.logger.logger import AppLogger
from config.config_loader import ConfigLoader

def test_name_extraction():
    """Test name extraction from various email formats."""
    
    print("=" * 60)
    print("🧪 EMAIL NAME EXTRACTION TEST")
    print("=" * 60)
    
    test_emails = [
        "rahulsinghrajput6090@gmail.com",
        "john.doe@company.com", 
        "info@company.com",
        "support@techcorp.com",
        "alice@example.org",
        "contact@business.co.uk",
        "mary.jane@university.edu",
        "admin@startup.io"
    ]
    
    print("Testing extract_name_from_email function:")
    print("-" * 40)
    
    for email in test_emails:
        name_with_company = extract_name_from_email(email, no_company=False)
        name_without_company = extract_name_from_email(email, no_company=True)
        
        print(f"📧 {email}")
        print(f"   With company: '{name_with_company}'")
        print(f"   Without company (fallback): '{name_without_company}'")
        print()

def test_template_personalization():
    """Test template personalization with recipient_name fallback."""
    
    print("=" * 60)
    print("📝 TEMPLATE PERSONALIZATION TEST")
    print("=" * 60)
    
    try:
        # Setup - base_dir should point to mailer root, not tests directory
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        config = ConfigLoader(base_dir)
        
        # Get personalization settings
        personalization_settings = config.get_email_personalization_settings()

        # Create logger
        app_logger = AppLogger(base_dir, config_path=config.config_path)
        logger = app_logger.get_logger()

        # Create personalizer
        personalizer = EmailPersonalizer(personalization_settings, base_dir, logger)
        
        # Test template content
        template_content = "{Hey|Hello|Hi} {{recipient_name}}, this is a test email!"
        
        # Test recipients
        test_recipients = [
            {"email": "rahulsinghrajput6090@gmail.com"},
            {"email": "john.doe@company.com"},
            {"email": "info@business.com"},
            {"email": "support@techcorp.com"},
            {"email": "alice@example.org"},
            {"email": "contact@startup.io"}
        ]
        
        print("Testing template personalization:")
        print("-" * 40)
        
        for recipient in test_recipients:
            personalized = personalizer.personalize_email(template_content, recipient)
            print(f"📧 {recipient['email']}")
            print(f"   Personalized: {personalized}")
            print()
            
    except Exception as e:
        print(f"❌ Error in template personalization test: {e}")

def test_actual_template():
    """Test with the actual email template."""
    
    print("=" * 60)
    print("📄 ACTUAL TEMPLATE TEST")
    print("=" * 60)
    
    try:
        # Setup - base_dir should point to mailer root, not tests directory
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        config = ConfigLoader(base_dir)
        
        # Get personalization settings
        personalization_settings = config.get_email_personalization_settings()

        # Create logger
        app_logger = AppLogger(base_dir, config_path=config.config_path)
        logger = app_logger.get_logger()

        # Create personalizer
        personalizer = EmailPersonalizer(personalization_settings, base_dir, logger)
        
        # Load actual template
        template_path = os.path.join(base_dir, "templates", "text", "i_bet.main.txt")
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            print("Loaded template content:")
            print("-" * 40)
            print(template_content[:200] + "..." if len(template_content) > 200 else template_content)
            print()
            
            # Test with email-only recipient
            test_recipient = {"email": "rahulsinghrajput6090@gmail.com"}
            
            print("Testing with email-only recipient:")
            print("-" * 40)
            print(f"📧 Recipient: {test_recipient['email']}")
            
            personalized = personalizer.personalize_email(template_content, test_recipient)
            
            print("📝 Personalized result:")
            print(personalized[:300] + "..." if len(personalized) > 300 else personalized)
            
            # Check if {{recipient_name}} was replaced
            if "{{recipient_name}}" in personalized:
                print("❌ ERROR: {{recipient_name}} was not replaced!")
            else:
                print("✅ SUCCESS: {{recipient_name}} was replaced")
                
        else:
            print(f"❌ Template file not found: {template_path}")
            
    except Exception as e:
        print(f"❌ Error in actual template test: {e}")

def main():
    """Main function."""
    print("BULK_MAILER - Email Personalization Fix Test")
    print("Testing recipient_name fallback to 'There' for email-only recipients")
    print()
    
    test_name_extraction()
    test_template_personalization()
    test_actual_template()
    
    print("=" * 60)
    print("🎯 PERSONALIZATION TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
