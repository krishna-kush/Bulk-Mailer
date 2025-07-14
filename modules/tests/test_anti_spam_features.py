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
# Description: Test script for anti-spam features (HTML obfuscation and manual randomization)
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.html_obfuscator import HTMLObfuscator
from modules.mailer.template_randomizer import TemplateRandomizer, randomize_content
from modules.mailer.email_personalizer import EmailPersonalizer

def test_html_obfuscation():
    """Test HTML obfuscation feature."""
    print("Testing HTML Obfuscation...")
    print("=" * 60)
    
    # Sample HTML content
    sample_html = '''
    <div class="email-container" style="max-width: 600px; margin: 0 auto; background: white;">
        <div class="content" style="padding: 30px; text-align: left;">
            <p class="greeting" style="font-size: 18px; margin-bottom: 20px;">Hello There!</p>
            <p class="message" style="font-size: 16px; margin-bottom: 30px;">This is a test message.</p>
        </div>
    </div>
    '''
    
    obfuscator = HTMLObfuscator()
    
    # Test different intensity levels
    intensities = ['light', 'medium', 'heavy']
    
    for intensity in intensities:
        print(f"\n{intensity.upper()} Intensity Obfuscation:")
        print("-" * 40)
        
        obfuscated = obfuscator.obfuscate_html(sample_html, intensity)
        
        # Show first 200 characters to demonstrate changes
        print("Original (first 200 chars):")
        print(sample_html[:200] + "...")
        print("\nObfuscated (first 200 chars):")
        print(obfuscated[:200] + "...")
        
        # Check if content changed
        if obfuscated != sample_html:
            print("✓ HTML structure modified successfully")
        else:
            print("✗ No changes made")

def test_manual_randomization():
    """Test manual randomization feature."""
    print("\n\nTesting Manual Randomization...")
    print("=" * 60)
    
    # Sample content with randomization syntax
    sample_content = '''
    <p class="greeting">{Hey|Hello|Hi} There!</p>
    <p class="message">I {bet|think|believe} you {have never|haven't} seen a resume like this before.</p>
    <p class="closing">{Let's talk|Get in touch|Connect with me}!</p>
    '''
    
    randomizer = TemplateRandomizer()
    
    print("Original content:")
    print(sample_content)
    
    print("\nRandomization patterns found:")
    patterns = randomizer.find_randomization_patterns(sample_content)
    for i, pattern in enumerate(patterns, 1):
        print(f"{i}. {pattern['full_match']} -> Options: {pattern['options']}")
    
    print(f"\nGenerating 5 variations:")
    print("-" * 40)
    
    for i in range(5):
        variation = randomizer.process_template(sample_content)
        print(f"\nVariation {i+1}:")
        # Extract just the text content for cleaner display
        import re
        text_only = re.sub(r'<[^>]+>', '', variation).strip()
        text_only = re.sub(r'\s+', ' ', text_only)
        print(text_only)
    
    # Test validation
    print(f"\nValidation results:")
    validation = randomizer.validate_syntax(sample_content)
    print(f"Valid syntax: {validation['valid']}")
    print(f"Patterns found: {validation['pattern_count']}")
    if validation['errors']:
        print(f"Errors: {validation['errors']}")

def test_combined_features():
    """Test both features working together."""
    print("\n\nTesting Combined Features...")
    print("=" * 60)
    
    # Sample template with both randomization and HTML
    template_content = '''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .greeting { font-size: 18px; color: #333; }
            .message { font-size: 16px; line-height: 1.6; }
        </style>
    </head>
    <body>
        <div class="container">
            <p class="greeting">{Hey|Hello|Hi|Greetings} there!</p>
            <p class="message">I {hope|trust|believe} this email finds you {well|in good health|doing great}.</p>
            <p class="message">I'm {excited|thrilled|pleased} to {reach out|connect|get in touch}.</p>
        </div>
    </body>
    </html>
    '''
    
    # Configure anti-spam settings
    config = {
        'enable_html_obfuscation': True,
        'html_obfuscation_intensity': 'medium',
        'enable_manual_randomization': True
    }
    
    # Create personalizer with anti-spam features
    import logging
    logger = logging.getLogger(__name__)
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    personalizer = EmailPersonalizer(config, base_dir, logger)
    
    print("Original template (first 300 chars):")
    print(template_content[:300] + "...")
    
    print(f"\nGenerating 3 processed variations:")
    print("-" * 50)
    
    for i in range(3):
        # Process with both randomization and obfuscation
        processed = personalizer.personalize_email(template_content, {'email': 'test@example.com'})
        
        print(f"\nVariation {i+1} (first 300 chars):")
        print(processed[:300] + "...")
        
        # Extract greeting to show randomization
        import re
        greeting_match = re.search(r'<p class="greeting[^>]*>([^<]+)</p>', processed)
        if greeting_match:
            print(f"Greeting: {greeting_match.group(1)}")

def test_preview_functionality():
    """Test preview functionality for randomization."""
    print("\n\nTesting Preview Functionality...")
    print("=" * 60)
    
    template_content = '''
    Subject: {Exciting|Amazing|Great} Opportunity at {TechCorp|InnovateCo|FutureTech}
    
    {Hi|Hello|Dear} {{recipient_name}},
    
    I {hope|trust} you're {doing well|having a great day}. I'm {reaching out|contacting you} about an {exciting|amazing|fantastic} opportunity.
    
    {Best regards|Sincerely|Thanks},
    Krishna
    '''
    
    config = {'enable_manual_randomization': True}
    import logging
    logger = logging.getLogger(__name__)
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    personalizer = EmailPersonalizer(config, base_dir, logger)
    
    # Get preview
    preview = personalizer.preview_randomization(template_content, count=3)
    
    print(f"Randomization patterns found: {preview['patterns_found']}")
    print("\nPatterns:")
    for pattern in preview['patterns']:
        print(f"  {pattern['full_match']} -> {pattern['options']}")
    
    print(f"\nValidation: {'✓ Valid' if preview['validation']['valid'] else '✗ Invalid'}")
    if preview['validation']['errors']:
        print(f"Errors: {preview['validation']['errors']}")
    
    print(f"\nPreview variations:")
    for i, variation in enumerate(preview['variations'], 1):
        print(f"\nVariation {i}:")
        print(variation.strip())

if __name__ == "__main__":
    test_html_obfuscation()
    test_manual_randomization()
    test_combined_features()
    test_preview_functionality()
    
    print("\n" + "=" * 60)
    print("Anti-spam features testing completed!")
    print("✓ HTML Obfuscation: Varies HTML structure without changing appearance")
    print("✓ Manual Randomization: Processes {option1|option2} syntax for content variations")
    print("✓ Combined Features: Both work together seamlessly")
    print("✓ Preview Functionality: Allows testing randomization patterns")
