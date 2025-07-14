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
# Description: Test script to process template and validate HTML output
#
# ================================================================================

import sys
import os
import re
from html.parser import HTMLParser
# Add the parent directory to the path to import modules
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from modules.mailer.template_randomizer import TemplateRandomizer
from modules.mailer.html_obfuscator import HTMLObfuscator

class HTMLValidator(HTMLParser):
    """Custom HTML parser to validate structure."""
    
    def __init__(self):
        super().__init__()
        self.tag_stack = []
        self.errors = []
        self.warnings = []
        
    def handle_starttag(self, tag, attrs):
        # Self-closing tags don't need to be tracked
        if tag not in ['img', 'br', 'hr', 'meta', 'link', 'input']:
            self.tag_stack.append(tag)
    
    def handle_endtag(self, tag):
        if tag in ['img', 'br', 'hr', 'meta', 'link', 'input']:
            return
            
        if not self.tag_stack:
            self.errors.append(f"Unexpected closing tag: </{tag}>")
        elif self.tag_stack[-1] != tag:
            self.errors.append(f"Mismatched tags: expected </{self.tag_stack[-1]}>, got </{tag}>")
        else:
            self.tag_stack.pop()
    
    def get_validation_result(self):
        if self.tag_stack:
            for tag in self.tag_stack:
                self.errors.append(f"Unclosed tag: <{tag}>")
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings
        }

def test_template_processing():
    """Test the complete template processing pipeline."""
    print("🧪 TESTING TEMPLATE PROCESSING PIPELINE")
    print("=" * 60)
    
    # Load the template
    template_path = "/home/kay/work/scrape/mailer/templates/email_templates/email_template_i_bet.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            original_template = f.read()
    except FileNotFoundError:
        print(f"❌ Template file not found: {template_path}")
        return False
    
    print("📄 ORIGINAL TEMPLATE LOADED")
    print("-" * 40)
    print(f"Template size: {len(original_template)} characters")
    
    # Count randomization patterns
    randomization_patterns = re.findall(r'\{[^}]+\}', original_template)
    print(f"Randomization patterns found: {len(randomization_patterns)}")
    
    # Step 1: Process randomization
    print(f"\n🎲 STEP 1: PROCESSING RANDOMIZATION")
    print("-" * 40)
    
    randomizer = TemplateRandomizer()
    randomized_html = randomizer.process_template(original_template)
    
    # Check if randomization was processed
    remaining_patterns = re.findall(r'\{[^}]+\}', randomized_html)
    randomization_success = len(remaining_patterns) == 0
    
    print(f"✅ Randomization processed: {randomization_success}")
    if not randomization_success:
        print(f"⚠️  Remaining unprocessed patterns: {len(remaining_patterns)}")
        for pattern in remaining_patterns[:5]:  # Show first 5
            print(f"   {pattern}")
    
    # Step 2: Apply HTML obfuscation
    print(f"\n🔒 STEP 2: APPLYING HTML OBFUSCATION")
    print("-" * 40)
    
    obfuscator = HTMLObfuscator()
    final_html = obfuscator.obfuscate_html(randomized_html, 'heavy')
    
    print(f"✅ HTML obfuscation applied")
    print(f"Final HTML size: {len(final_html)} characters")
    
    # Step 3: Validate HTML structure
    print(f"\n🔍 STEP 3: VALIDATING HTML STRUCTURE")
    print("-" * 40)
    
    validator = HTMLValidator()
    try:
        validator.feed(final_html)
        validation_result = validator.get_validation_result()
        
        if validation_result['valid']:
            print("✅ HTML structure is valid")
        else:
            print("❌ HTML structure has errors:")
            for error in validation_result['errors']:
                print(f"   • {error}")
    except Exception as e:
        print(f"❌ HTML parsing failed: {e}")
        validation_result = {'valid': False, 'errors': [str(e)]}
    
    # Step 4: Check for specific issues
    print(f"\n🔎 STEP 4: CHECKING FOR SPECIFIC ISSUES")
    print("-" * 40)
    
    issues = check_specific_issues(final_html)
    
    for issue_type, result in issues.items():
        status = "✅" if result['passed'] else "❌"
        print(f"{status} {issue_type}: {result['message']}")
    
    # Step 5: Save processed HTML for inspection
    output_path = "/home/kay/work/scrape/mailer/modules/tests/processed_email_output.html"
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f"\n💾 PROCESSED HTML SAVED TO: {output_path}")
    except Exception as e:
        print(f"\n❌ Failed to save processed HTML: {e}")
    
    # Step 6: Generate summary
    print(f"\n📊 PROCESSING SUMMARY")
    print("=" * 40)
    
    all_passed = (
        randomization_success and 
        validation_result['valid'] and 
        all(issues[key]['passed'] for key in issues)
    )
    
    print(f"Overall result: {'✅ PASS' if all_passed else '❌ FAIL'}")
    print(f"Randomization: {'✅' if randomization_success else '❌'}")
    print(f"HTML validity: {'✅' if validation_result['valid'] else '❌'}")
    print(f"Specific checks: {'✅' if all(issues[key]['passed'] for key in issues) else '❌'}")
    
    return all_passed

def check_specific_issues(html):
    """Check for specific issues that commonly occur."""
    issues = {}
    
    # Check 1: Multiple images
    img_count = len(re.findall(r'<img[^>]*>', html))
    issues['Image count'] = {
        'passed': img_count == 1,
        'message': f"Found {img_count} images (should be 1)"
    }
    
    # Check 2: Unprocessed randomization syntax
    unprocessed = re.findall(r'\{[^}]+\}', html)
    issues['Randomization processing'] = {
        'passed': len(unprocessed) == 0,
        'message': f"Found {len(unprocessed)} unprocessed patterns"
    }
    
    # Check 3: Invalid CSS values
    invalid_css = []
    if 'text-align: middle' in html:
        invalid_css.append('text-align: middle')
    if 'font-weight: semi-bold' in html:
        invalid_css.append('font-weight: semi-bold')
    
    issues['CSS validity'] = {
        'passed': len(invalid_css) == 0,
        'message': f"Invalid CSS: {invalid_css}" if invalid_css else "All CSS values valid"
    }
    
    # Check 4: Missing spaces in text
    spacing_issues = []
    if 'Heythere' in html or 'Hifriend' in html or 'Hellofriend' in html:
        spacing_issues.append('Missing spaces in greeting')
    
    issues['Text spacing'] = {
        'passed': len(spacing_issues) == 0,
        'message': f"Spacing issues: {spacing_issues}" if spacing_issues else "Text spacing correct"
    }
    
    # Check 5: Title spacing
    title_match = re.search(r'<title>(.*?)</title>', html)
    title_has_spacing_issue = False
    if title_match:
        title = title_match.group(1)
        if 'ThisBefore' in title or 'ThisEver' in title:
            title_has_spacing_issue = True
    
    issues['Title spacing'] = {
        'passed': not title_has_spacing_issue,
        'message': "Title spacing issue detected" if title_has_spacing_issue else "Title spacing correct"
    }
    
    return issues

def show_processed_html_preview(html, max_lines=20):
    """Show a preview of the processed HTML."""
    print(f"\n📋 PROCESSED HTML PREVIEW (first {max_lines} lines):")
    print("-" * 50)
    
    lines = html.split('\n')
    for i, line in enumerate(lines[:max_lines], 1):
        print(f"{i:2d}: {line}")
    
    if len(lines) > max_lines:
        print(f"... ({len(lines) - max_lines} more lines)")

if __name__ == "__main__":
    success = test_template_processing()
    
    # Load and show preview of processed HTML
    try:
        with open("/home/kay/work/scrape/mailer/modules/tests/processed_email_output.html", 'r') as f:
            processed_html = f.read()
        show_processed_html_preview(processed_html)
    except FileNotFoundError:
        print("\n⚠️  Processed HTML file not found for preview")
    
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '⚠️  SOME TESTS FAILED!'}")
    print("Check the processed_email_output.html file for the final result.")
