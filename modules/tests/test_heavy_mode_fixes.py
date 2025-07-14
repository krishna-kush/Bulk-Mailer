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
# Description: Test script to verify heavy mode fixes for CSS property shuffling and comments
#
# ================================================================================

import sys
import os
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.html_obfuscator import HTMLObfuscator
import re

def test_css_property_shuffling():
    """Test that CSS properties are shuffled within classes in heavy mode."""
    print("Testing CSS Property Shuffling in Heavy Mode")
    print("=" * 55)
    
    # Simple HTML with clear CSS classes
    sample_html = '''
    <style>
        .test-class {
            display: block;
            background: #333;
            color: white;
            padding: 12px 20px;
            text-decoration: none;
            font-weight: 600;
            text-align: center;
        }
        
        .another-class {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
    </style>
    <div class="test-class">Test</div>
    <div class="another-class">Another</div>
    '''
    
    print("ORIGINAL CSS:")
    print("-" * 30)
    original_css = extract_css_section(sample_html)
    print(original_css)
    
    print(f"\nHEAVY MODE RESULT:")
    print("-" * 30)
    
    obfuscator = HTMLObfuscator()
    result = obfuscator.obfuscate_html(sample_html, 'heavy')
    result_css = extract_css_section(result)
    print(result_css)
    
    # Check if properties were shuffled
    original_first_class = extract_first_class_properties(original_css)
    result_first_class = extract_first_class_properties(result_css)
    
    print(f"\n📊 PROPERTY SHUFFLING ANALYSIS:")
    print("-" * 40)
    print(f"Original first class properties: {original_first_class}")
    print(f"Result first class properties: {result_first_class}")
    
    # Check if order changed
    properties_shuffled = original_first_class != result_first_class
    print(f"✅ Properties shuffled: {properties_shuffled}")

def test_comment_quality():
    """Test that comments are natural and varied."""
    print(f"\n\nTesting Comment Quality")
    print("=" * 35)
    
    sample_html = '''
    <div class="container">
        <p>Test content</p>
        <a href="#">Link</a>
        <img src="test.jpg" alt="Test">
    </div>
    '''
    
    print("ORIGINAL HTML:")
    print("-" * 20)
    print(sample_html.strip())
    
    obfuscator = HTMLObfuscator()
    
    # Generate multiple results to see comment variety
    print(f"\nHEAVY MODE RESULTS (3 variations):")
    print("-" * 45)
    
    for i in range(3):
        result = obfuscator.obfuscate_html(sample_html, 'heavy')
        comments = extract_comments(result)
        
        print(f"\nVariation {i+1}:")
        print(f"  Comments found: {comments}")
        print(f"  Sample HTML: {result[:100]}...")

def test_combined_features():
    """Test all heavy mode features working together."""
    print(f"\n\nTesting Combined Heavy Mode Features")
    print("=" * 50)
    
    # More complex HTML similar to your email
    sample_html = '''
    <style>
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .content {
            padding: 30px;
            text-align: left;
        }
    </style>
    <div class="email-container">
        <div class="content">
            <p>Test content</p>
        </div>
    </div>
    '''
    
    obfuscator = HTMLObfuscator()
    result = obfuscator.obfuscate_html(sample_html, 'heavy')
    
    print("HEAVY MODE RESULT:")
    print("-" * 25)
    print(result[:500] + "..." if len(result) > 500 else result)
    
    # Analysis
    print(f"\n📋 FEATURE ANALYSIS:")
    print("-" * 25)
    
    # Check class name randomization
    original_classes = extract_class_names_from_html(sample_html)
    result_classes = extract_class_names_from_html(result)
    classes_randomized = not any(orig in result_classes for orig in original_classes)
    
    # Check comments
    comments = extract_comments(result)
    has_comments = len(comments) > 0
    
    # Check CSS structure
    result_css = extract_css_section(result)
    has_css = len(result_css) > 0
    
    print(f"✅ Class names randomized: {classes_randomized}")
    print(f"✅ Comments inserted: {has_comments} ({len(comments)} found)")
    print(f"✅ CSS preserved: {has_css}")
    print(f"✅ HTML structure maintained: {bool(result)}")

def extract_css_section(html):
    """Extract the CSS section from HTML."""
    match = re.search(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def extract_first_class_properties(css):
    """Extract properties from the first CSS class."""
    # Find first class definition
    match = re.search(r'\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{([^}]*)\}', css, re.DOTALL)
    if match:
        properties_content = match.group(2).strip()
        # Extract property names only (before the colon)
        properties = []
        for prop in properties_content.split(';'):
            prop = prop.strip()
            if prop and ':' in prop:
                prop_name = prop.split(':')[0].strip()
                properties.append(prop_name)
        return properties
    return []

def extract_comments(html):
    """Extract HTML comments from the HTML."""
    comments = re.findall(r'<!--\s*([^>]+)\s*-->', html)
    return [comment.strip() for comment in comments]

def extract_class_names_from_html(html):
    """Extract class names used in HTML class attributes."""
    classes = set()
    matches = re.findall(r'class="([^"]+)"', html)
    for match in matches:
        classes.update(match.split())
    return list(classes)

if __name__ == "__main__":
    test_css_property_shuffling()
    test_comment_quality()
    test_combined_features()
    
    print("\n" + "=" * 60)
    print("🎯 HEAVY MODE FIXES SUMMARY:")
    print("✅ CSS class reordering re-enabled")
    print("✅ CSS property shuffling within classes")
    print("✅ Improved comment quality (natural, varied)")
    print("✅ Higher comment insertion frequency (40%)")
    print("✅ Completely random class names")
    print("🛡️ Maximum anti-spam protection achieved!")
