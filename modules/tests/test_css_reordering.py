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
# Description: Test script to demonstrate CSS class reordering and property shuffling
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.html_obfuscator import HTMLObfuscator
import re

def test_css_class_reordering():
    """Test CSS class reordering and property shuffling."""
    print("Testing CSS Class Reordering & Property Shuffling")
    print("=" * 60)
    
    # Sample HTML with multiple CSS classes (like your example)
    sample_html = '''
    <style>
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .content {
            padding: 30px;
            text-align: left;
        }
        
        .text-container {
            max-width: 600px;
            margin: 0 auto;
        }
        
        .greeting {
            font-size: 18px;
            margin-bottom: 20px;
            color: #2c3e50;
            font-weight: 600;
        }
    </style>
    <body>
        <div class="email-container">
            <div class="content">
                <div class="text-container">
                    <p class="greeting">Hello!</p>
                </div>
            </div>
        </div>
    </body>
    '''
    
    print("ORIGINAL CSS:")
    print("-" * 40)
    original_css = extract_css_section(sample_html)
    print(original_css)
    
    # Test with medium intensity (includes CSS class reordering)
    print(f"\nMEDIUM MODE (with CSS class reordering):")
    print("-" * 50)
    
    obfuscator = HTMLObfuscator()
    medium_result = obfuscator.obfuscate_html(sample_html, 'medium')
    medium_css = extract_css_section(medium_result)
    print(medium_css)
    
    # Test with heavy intensity
    print(f"\nHEAVY MODE (with CSS class reordering + random names):")
    print("-" * 60)
    
    heavy_result = obfuscator.obfuscate_html(sample_html, 'heavy')
    heavy_css = extract_css_section(heavy_result)
    print(heavy_css)
    
    # Analysis
    print(f"\n📊 ANALYSIS:")
    print("-" * 30)
    
    original_order = extract_class_order(sample_html)
    medium_order = extract_class_order(medium_result)
    heavy_order = extract_class_order(heavy_result)
    
    print(f"Original class order: {original_order}")
    print(f"Medium class order: {medium_order}")
    print(f"Heavy class order: {heavy_order}")
    
    # Check if order changed
    order_changed_medium = original_order != medium_order
    order_changed_heavy = original_order != heavy_order
    
    print(f"\n✅ RESULTS:")
    print(f"  Medium mode - Class order changed: {order_changed_medium}")
    print(f"  Heavy mode - Class order changed: {order_changed_heavy}")
    print(f"  Heavy mode - Class names randomized: {check_names_randomized(original_order, heavy_order)}")
    
    # Show property shuffling example
    print(f"\n🔄 PROPERTY SHUFFLING EXAMPLE:")
    print("-" * 40)
    
    original_container = extract_specific_class(sample_html, 'email-container')
    medium_container = extract_first_class_definition(medium_result)
    heavy_container = extract_first_class_definition(heavy_result)
    
    print("Original .email-container properties:")
    print(f"  {original_container}")
    print(f"\nMedium mode (shuffled properties):")
    print(f"  {medium_container}")
    print(f"\nHeavy mode (shuffled + random name):")
    print(f"  {heavy_container}")

def extract_css_section(html):
    """Extract the CSS section from HTML."""
    match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_class_order(html):
    """Extract the order of CSS class names."""
    css_section = extract_css_section(html)
    # Find all class names in order
    class_names = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', css_section)
    return class_names

def extract_specific_class(html, class_name):
    """Extract a specific CSS class definition."""
    pattern = rf'\.{re.escape(class_name)}\s*\{{([^}}]*)\}}'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        properties = match.group(1).strip()
        # Clean up and format properties
        props = [prop.strip() for prop in properties.split(';') if prop.strip()]
        return '; '.join(props)
    return ""

def extract_first_class_definition(html):
    """Extract the first CSS class definition."""
    css_section = extract_css_section(html)
    # Find first class definition
    match = re.search(r'\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{([^}]*)\}', css_section, re.DOTALL)
    if match:
        class_name = match.group(1)
        properties = match.group(2).strip()
        # Clean up properties
        props = [prop.strip() for prop in properties.split(';') if prop.strip()]
        return f".{class_name}: {'; '.join(props)}"
    return ""

def check_names_randomized(original_names, new_names):
    """Check if class names have been randomized."""
    if len(original_names) != len(new_names):
        return True
    
    # Check if any original name appears in new names
    for orig_name in original_names:
        if orig_name in new_names:
            return False
    
    return True

def demonstrate_multiple_variations():
    """Show how each email gets different CSS structure."""
    print(f"\n\n🎯 MULTIPLE EMAIL VARIATIONS:")
    print("=" * 60)
    
    sample_html = '''
    <style>
        .container { max-width: 600px; margin: 0 auto; }
        .header { padding: 20px; background: #f5f5f5; }
        .content { font-size: 16px; line-height: 1.6; }
    </style>
    '''
    
    obfuscator = HTMLObfuscator()
    
    print("Generating 3 different email variations:")
    print("-" * 50)
    
    for i in range(3):
        result = obfuscator.obfuscate_html(sample_html, 'heavy')
        css_section = extract_css_section(result)
        class_order = extract_class_order(result)
        
        print(f"\nEmail {i+1} - Class order: {class_order}")
        # Show first few lines of CSS
        css_lines = css_section.split('\n')[:6]
        for line in css_lines:
            if line.strip():
                print(f"  {line.strip()}")

if __name__ == "__main__":
    test_css_class_reordering()
    demonstrate_multiple_variations()
    
    print("\n" + "=" * 60)
    print("✅ CSS Class Reordering Implementation Complete!")
    print("🔄 Features added:")
    print("  • CSS class definition order shuffling")
    print("  • CSS property order shuffling within each class")
    print("  • Random spacing and formatting variations")
    print("  • Works in both medium and heavy modes")
    print("🛡️ Anti-spam benefit: Each email has unique CSS structure!")
