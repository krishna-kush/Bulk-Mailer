#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Test script to verify the integration fix for anti-spam features
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.email_composer import EmailComposer
import logging

def test_integration_fix():
    """Test that anti-spam features work even when personalization is disabled."""
    print("Testing Integration Fix for Anti-Spam Features...")
    print("=" * 60)
    
    # Setup logger
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Test configuration - personalization disabled, anti-spam enabled
    personalization_config = {
        "enable_personalization": False
    }
    
    anti_spam_config = {
        "enable_html_obfuscation": True,
        "html_obfuscation_intensity": "medium",
        "enable_manual_randomization": True
    }
    
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    
    # Create EmailComposer with anti-spam config
    email_composer = EmailComposer(logger, personalization_config, base_dir, anti_spam_config)
    
    # Test template with randomization syntax
    test_template = '''
    <html>
    <body>
        <p>{Hey|Hello|Hi} There!</p>
        <p>I {bet|think|believe} you {have never|haven't} seen a resume like this before.</p>
        <p>{Let's talk|Get in touch|Connect with me}!</p>
    </body>
    </html>
    '''
    
    print("Original template:")
    print(test_template.strip())
    
    print(f"\nTesting with personalizer: {email_composer.personalizer is not None}")
    
    if email_composer.personalizer:
        print("\n✓ Personalizer created successfully")
        
        # Test randomization
        print("\nGenerating 3 variations:")
        print("-" * 40)
        
        for i in range(3):
            recipient = {'email': f'test{i}@example.com'}
            processed = email_composer.personalizer.personalize_email(test_template, recipient)
            
            # Extract text content for cleaner display
            import re
            text_lines = []
            for line in processed.split('\n'):
                line = line.strip()
                if line and not line.startswith('<') and not line.startswith('</'):
                    # Remove HTML tags from content lines
                    clean_line = re.sub(r'<[^>]+>', '', line).strip()
                    if clean_line:
                        text_lines.append(clean_line)
            
            print(f"\nVariation {i+1}:")
            for line in text_lines:
                print(f"  {line}")
        
        # Test configuration access
        print(f"\nConfiguration check:")
        print(f"  Manual randomization enabled: {email_composer.personalizer.config.get('enable_manual_randomization', False)}")
        print(f"  HTML obfuscation enabled: {email_composer.personalizer.config.get('enable_html_obfuscation', False)}")
        print(f"  Obfuscation intensity: {email_composer.personalizer.config.get('html_obfuscation_intensity', 'none')}")
        
    else:
        print("✗ Personalizer not created - this is the problem!")
        print("Anti-spam features will not work without personalizer")
    
    print("\n" + "=" * 60)
    if email_composer.personalizer:
        print("✅ Integration fix successful!")
        print("Anti-spam features are working even with personalization disabled")
    else:
        print("❌ Integration fix failed!")
        print("Need to debug EmailComposer initialization")

if __name__ == "__main__":
    test_integration_fix()
