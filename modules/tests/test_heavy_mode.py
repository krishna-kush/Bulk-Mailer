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
# Description: Test script to demonstrate the difference between medium and heavy mode
#              class name obfuscation
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.html_obfuscator import HTMLObfuscator
import re

def test_class_name_obfuscation():
    """Test the difference between medium and heavy mode class obfuscation."""
    print("Testing Class Name Obfuscation: Medium vs Heavy Mode")
    print("=" * 70)
    
    # Sample HTML with multiple CSS classes
    sample_html = '''
    <style>
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
        }
        .header-section {
            padding: 20px;
            text-align: center;
        }
        .content-area {
            font-size: 16px;
            line-height: 1.6;
        }
        .call-to-action {
            background: #333;
            color: white;
            padding: 12px 24px;
        }
    </style>
    <body>
        <div class="email-container">
            <div class="header-section">
                <h1>Welcome!</h1>
            </div>
            <div class="content-area">
                <p>This is our message content.</p>
                <a href="#" class="call-to-action">Click Here</a>
            </div>
        </div>
    </body>
    '''
    
    print("ORIGINAL CLASS NAMES:")
    original_classes = extract_classes(sample_html)
    print(f"  {', '.join(sorted(original_classes))}")
    
    # Test MEDIUM mode
    print(f"\n🟡 MEDIUM MODE (Class + Suffix):")
    print("-" * 40)
    
    obfuscator_medium = HTMLObfuscator()
    medium_result = obfuscator_medium.obfuscate_html(sample_html, 'medium')
    medium_classes = extract_classes(medium_result)
    
    print("Class mappings:")
    for original in sorted(original_classes):
        for medium in medium_classes:
            if medium.startswith(original + '-'):
                print(f"  {original} → {medium}")
                break
    
    # Test HEAVY mode
    print(f"\n🔴 HEAVY MODE (Completely Random):")
    print("-" * 40)
    
    obfuscator_heavy = HTMLObfuscator()
    heavy_result = obfuscator_heavy.obfuscate_html(sample_html, 'heavy')
    heavy_classes = extract_classes(heavy_result)
    
    print("Class mappings:")
    # For heavy mode, we need to track the mappings differently since they're completely random
    # Let's show the before/after CSS sections
    original_css_classes = extract_css_classes(sample_html)
    heavy_css_classes = extract_css_classes(heavy_result)
    
    for i, (orig, heavy) in enumerate(zip(sorted(original_css_classes), sorted(heavy_css_classes))):
        print(f"  {orig} → {heavy}")
    
    # Show sample CSS transformation
    print(f"\n📋 CSS TRANSFORMATION EXAMPLES:")
    print("-" * 50)
    
    print("ORIGINAL CSS:")
    css_lines = extract_css_sample(sample_html)
    for line in css_lines[:3]:  # Show first 3 CSS rules
        print(f"  {line}")
    
    print(f"\nMEDIUM MODE CSS:")
    medium_css_lines = extract_css_sample(medium_result)
    for line in medium_css_lines[:3]:
        print(f"  {line}")
    
    print(f"\nHEAVY MODE CSS:")
    heavy_css_lines = extract_css_sample(heavy_result)
    for line in heavy_css_lines[:3]:
        print(f"  {line}")
    
    # Show HTML transformation
    print(f"\n🏷️ HTML CLASS USAGE EXAMPLES:")
    print("-" * 50)
    
    original_html_sample = '<div class="email-container">'
    medium_html_sample = extract_html_sample(medium_result, 'email-container')
    heavy_html_sample = extract_html_sample(heavy_result, 'email-container')
    
    print(f"ORIGINAL: {original_html_sample}")
    print(f"MEDIUM:   {medium_html_sample}")
    print(f"HEAVY:    {heavy_html_sample}")
    
    # Analysis
    print(f"\n📊 ANALYSIS:")
    print("-" * 30)
    print(f"Original classes: {len(original_classes)}")
    print(f"Medium classes: {len(medium_classes)}")
    print(f"Heavy classes: {len(heavy_classes)}")
    
    # Check if heavy mode classes are truly random
    heavy_random_score = calculate_randomness_score(heavy_classes, original_classes)
    print(f"Heavy mode randomness: {heavy_random_score:.1%}")
    
    print(f"\n✅ BENEFITS OF HEAVY MODE:")
    print("  • Completely unrecognizable class names")
    print("  • Maximum anti-spam protection")
    print("  • No pattern detection possible")
    print("  • Each email gets unique CSS structure")

def extract_classes(html):
    """Extract all class names from HTML."""
    classes = set()
    
    # From CSS definitions
    css_matches = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)', html)
    classes.update(css_matches)
    
    # From HTML class attributes
    html_matches = re.findall(r'class="([^"]+)"', html)
    for match in html_matches:
        classes.update(match.split())
    
    return classes

def extract_css_classes(html):
    """Extract class names from CSS definitions only."""
    css_matches = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{', html)
    return css_matches

def extract_css_sample(html):
    """Extract sample CSS rules."""
    css_rules = re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{[^}]*\}', html)
    return css_rules

def extract_html_sample(html, original_class_prefix):
    """Extract HTML sample with class usage."""
    # Find any div with a class that might be the transformed version
    pattern = r'<div class="([^"]*)"[^>]*>'
    matches = re.findall(pattern, html)
    if matches:
        return f'<div class="{matches[0]}">'
    return '<div class="unknown">'

def calculate_randomness_score(heavy_classes, original_classes):
    """Calculate how random the heavy mode classes are."""
    if not heavy_classes or not original_classes:
        return 0.0
    
    # Check how many heavy classes have no resemblance to original
    random_count = 0
    for heavy_class in heavy_classes:
        is_random = True
        for original_class in original_classes:
            # If heavy class contains any part of original class, it's not fully random
            if any(part in heavy_class.lower() for part in original_class.lower().split('-')):
                is_random = False
                break
        if is_random:
            random_count += 1
    
    return random_count / len(heavy_classes)

if __name__ == "__main__":
    test_class_name_obfuscation()
    
    print("\n" + "=" * 70)
    print("🎯 RECOMMENDATION:")
    print("Use HEAVY mode when maximum anti-spam protection is needed")
    print("and you've tested email client compatibility thoroughly!")
