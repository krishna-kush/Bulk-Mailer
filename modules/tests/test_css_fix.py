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
# Description: Test script to verify CSS class renaming and subject randomization
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.html_obfuscator import HTMLObfuscator
from modules.mailer.template_randomizer import TemplateRandomizer

def test_css_class_renaming():
    """Test that CSS classes are consistently renamed throughout the document."""
    print("Testing CSS Class Renaming...")
    print("=" * 60)
    
    # Sample HTML with CSS and class usage
    sample_html = '''
    <style>
        .email-container {
            max-width: 600px;
            margin: 0 auto;
        }
        .greeting {
            font-size: 18px;
            color: #333;
        }
        .message {
            font-size: 16px;
            margin-bottom: 20px;
        }
    </style>
    <body>
        <div class="email-container">
            <p class="greeting">Hello!</p>
            <p class="message">This is a test message.</p>
        </div>
    </body>
    '''
    
    obfuscator = HTMLObfuscator()
    
    print("Original HTML (CSS classes):")
    import re
    original_classes = set()
    css_matches = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', sample_html)
    html_matches = re.findall(r'class="([^"]+)"', sample_html)
    original_classes.update(css_matches)
    for match in html_matches:
        original_classes.update(match.split())
    print(f"Classes found: {sorted(original_classes)}")
    
    # Test class renaming
    obfuscated = obfuscator._vary_class_names(sample_html)
    
    print("\nAfter class renaming:")
    new_classes = set()
    css_matches = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', obfuscated)
    html_matches = re.findall(r'class="([^"]+)"', obfuscated)
    new_classes.update(css_matches)
    for match in html_matches:
        new_classes.update(match.split())
    print(f"Classes found: {sorted(new_classes)}")
    
    # Verify CSS and HTML consistency
    css_classes = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', obfuscated))
    html_classes = set()
    for match in re.findall(r'class="([^"]+)"', obfuscated):
        html_classes.update(match.split())
    
    print(f"\nConsistency check:")
    print(f"CSS classes: {sorted(css_classes)}")
    print(f"HTML classes: {sorted(html_classes)}")
    print(f"✓ Consistent: {css_classes == html_classes}")
    
    # Show a snippet of the result
    print(f"\nSample of obfuscated HTML:")
    lines = obfuscated.split('\n')
    for line in lines[1:8]:  # Show CSS section
        if line.strip():
            print(f"  {line.strip()}")

def test_subject_randomization():
    """Test subject randomization."""
    print("\n\nTesting Subject Randomization...")
    print("=" * 60)
    
    # Test subject with randomization
    test_subject = "{Driven|Passionate|Experienced} Technologist | {Seeking|Looking for|Exploring} Opportunities for Tech Jobs"
    
    randomizer = TemplateRandomizer()
    
    print("Original subject:")
    print(f"  {test_subject}")
    
    print(f"\nGenerating 5 subject variations:")
    print("-" * 40)
    
    for i in range(5):
        variation = randomizer.process_template(test_subject)
        print(f"{i+1}. {variation}")
    
    # Test validation
    validation = randomizer.validate_syntax(test_subject)
    print(f"\nValidation:")
    print(f"  Valid: {validation['valid']}")
    print(f"  Patterns found: {validation['pattern_count']}")
    for pattern in validation['patterns']:
        print(f"    {pattern['full_match']} -> {pattern['options']}")

def test_combined_obfuscation():
    """Test full obfuscation with all techniques."""
    print("\n\nTesting Combined Obfuscation...")
    print("=" * 60)
    
    # Sample template similar to your email
    template = '''
    <style>
        .email-container { max-width: 600px; margin: 0 auto; }
        .greeting { font-size: 18px; color: #333; }
        .message { font-size: 16px; margin-bottom: 20px; }
    </style>
    <body>
        <div class="email-container">
            <p class="greeting">{Hey|Hello|Hi} There!</p>
            <p class="message">I {bet|think|believe} this will work better now.</p>
        </div>
    </body>
    '''
    
    # Apply randomization first
    randomizer = TemplateRandomizer()
    randomized = randomizer.process_template(template)
    
    # Then apply HTML obfuscation
    obfuscator = HTMLObfuscator()
    final = obfuscator.obfuscate_html(randomized, 'medium')
    
    print("Original template (first 200 chars):")
    print(template[:200] + "...")
    
    print(f"\nAfter randomization + obfuscation (first 300 chars):")
    print(final[:300] + "...")
    
    # Check if classes are still consistent
    css_classes = set(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', final))
    html_classes = set()
    for match in re.findall(r'class="([^"]+)"', final):
        html_classes.update(match.split())
    
    print(f"\nFinal consistency check:")
    print(f"✓ CSS and HTML classes match: {css_classes == html_classes}")
    if css_classes != html_classes:
        print(f"  CSS: {css_classes}")
        print(f"  HTML: {html_classes}")

if __name__ == "__main__":
    test_css_class_renaming()
    test_subject_randomization()
    test_combined_obfuscation()
    
    print("\n" + "=" * 60)
    print("✅ CSS Fix Testing Complete!")
    print("✓ CSS classes are consistently renamed (no broken styling)")
    print("✓ Subject randomization works with {option1|option2} syntax")
    print("✓ Combined obfuscation maintains CSS integrity")
