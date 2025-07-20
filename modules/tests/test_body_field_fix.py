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
import time

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config_loader import ConfigLoader
from modules.logger.logger import AppLogger
from modules.browser.browser_handler import BrowserHandler
from modules.browser.providers.protonmail import ProtonMailAutomation

def test_body_field_selectors():
    """Test different body field selectors to find the working one."""
    
    print("=" * 60)
    print("🔧 BODY FIELD SELECTOR FIX TEST")
    print("=" * 60)
    print("This test will identify and fix the body field selector issue.")
    print("Testing multiple selector strategies...")
    print("=" * 60)
    
    try:
        # Setup
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        config = ConfigLoader(base_dir)
        app_logger = AppLogger(config.base_dir, config_path=config.config_path)
        logger = app_logger.get_logger()
        
        # Load configurations
        browser_config = config.get_browser_automation_settings()
        providers_config = config.get_browser_providers_settings()
        senders_data = config.get_senders()
        email_personalization = config.get_email_personalization_settings()
        email_anti_spam = config.get_email_anti_spam_settings()
        email_content = config.get_email_content_settings()
        
        # Merge settings
        combined_email_settings = {**email_personalization, **email_anti_spam}
        
        # Find ProtonMail sender
        protonmail_sender = None
        for sender in senders_data:
            if sender.get('provider', '').lower() == 'protonmail':
                protonmail_sender = sender
                break
        
        if not protonmail_sender:
            print("❌ No ProtonMail sender found")
            return False
        
        email = protonmail_sender['email']
        password = protonmail_sender.get('password', '')
        
        print(f"📧 Sender: {email}")
        
        # Create browser handler
        print(f"\n🚀 Step 1: Starting browser...")
        browser_handler = BrowserHandler(browser_config, logger)
        
        if not browser_handler.start_playwright():
            print("❌ Failed to start Playwright")
            return False
        
        if not browser_handler.launch_browser():
            print("❌ Failed to launch browser")
            return False
        
        # Create context
        print(f"\n🍪 Step 2: Creating browser context...")
        cookie_file = protonmail_sender.get('cookie_file', '')
        if cookie_file and os.path.exists(cookie_file):
            context = browser_handler.create_context_with_cookies(email, cookie_file)
        else:
            context = browser_handler.browser.new_context()
            browser_handler.contexts[email] = context
        
        if not context:
            print("❌ Failed to create context")
            browser_handler.close_browser()
            return False
        
        # Create page
        print(f"\n📄 Step 3: Creating page...")
        page = browser_handler.create_page(email)
        
        if not page:
            print("❌ Failed to create page")
            browser_handler.close_browser()
            return False
        
        # Create ProtonMail automation
        print(f"\n🤖 Step 4: Initializing ProtonMail automation...")
        protonmail_automation = ProtonMailAutomation(
            providers_config['protonmail'], 
            logger,
            base_dir,
            combined_email_settings,
            email_content
        )
        
        # Test authentication
        print(f"\n🔐 Step 5: Testing authentication...")
        auth_success = protonmail_automation.authenticate_with_fallback(page, email, password)
        
        if not auth_success:
            print("❌ Authentication failed!")
            browser_handler.close_browser()
            return False
        
        print("✅ Authentication successful!")
        
        # Open compose window
        print(f"\n📝 Step 6: Opening compose window...")
        if not protonmail_automation.open_compose(page):
            print("❌ Failed to open compose window")
            browser_handler.close_browser()
            return False
        print("✅ Compose window opened")
        
        # Fill recipient and subject first
        print(f"\n📧 Step 7: Filling recipient and subject...")
        test_recipient = "test@example.com"
        test_subject = "Body Field Test"
        
        if not protonmail_automation.fill_recipient(page, test_recipient):
            print("❌ Failed to fill recipient")
            browser_handler.close_browser()
            return False
        
        if not protonmail_automation.fill_subject(page, test_subject):
            print("❌ Failed to fill subject")
            browser_handler.close_browser()
            return False
        
        print("✅ Recipient and subject filled")
        
        # Now test different body field selectors
        print(f"\n🔍 Step 8: Testing body field selectors...")
        
        # Extended list of body field selectors to test
        body_selectors_to_test = [
            # Original selectors
            '[data-testid="rooster-editor"]',
            '.composer-content [contenteditable="true"]',
            '.rooster-editor',
            '[role="textbox"]',
            '.editor-content',
            '.compose-body [contenteditable="true"]',
            'iframe[title*="editor"]',
            '.composer-body-container [contenteditable="true"]',
            '.editor-wrapper [contenteditable="true"]',
            '.ProseMirror',
            '[contenteditable="true"]',
            
            # Additional selectors to try
            '[data-testid="composer:body"]',
            '[data-testid="composer-body"]',
            '.composer-body',
            '.composer-editor',
            '.message-body',
            '.email-body',
            '.compose-editor',
            '.text-editor',
            '.editor',
            'div[contenteditable="true"]',
            'textarea',
            '.composer textarea',
            '.composer-content textarea',
            '.composer-body textarea',
            '[placeholder*="message"]',
            '[placeholder*="body"]',
            '[placeholder*="content"]',
            '[aria-label*="message"]',
            '[aria-label*="body"]',
            '[aria-label*="content"]',
            '.composer-content .editor',
            '.composer-content .text-editor',
            '.composer-content div[contenteditable]',
            '.composer div[contenteditable]',
            '.compose div[contenteditable]',
            'div[role="textbox"]',
            'div[contenteditable="true"]:not([data-testid*="to"]):not([data-testid*="subject"])',
        ]
        
        test_content = "This is a test message to verify body field filling works correctly."
        
        print(f"Testing {len(body_selectors_to_test)} different selectors...")
        
        working_selectors = []
        
        for i, selector in enumerate(body_selectors_to_test, 1):
            try:
                print(f"   {i:2d}. Testing: {selector}")
                
                # Try to find the element
                element = page.query_selector(selector)
                if element and element.is_visible():
                    print(f"       ✅ Element found and visible")
                    
                    # Try to click and fill
                    try:
                        element.click()
                        time.sleep(0.5)
                        
                        # Clear any existing content
                        page.keyboard.press("Control+a")
                        time.sleep(0.2)
                        page.keyboard.press("Delete")
                        time.sleep(0.5)
                        
                        # Type test content
                        page.keyboard.type(test_content)
                        time.sleep(1)
                        
                        # Check if content was actually filled
                        current_content = element.text_content() or element.input_value() or ""
                        if test_content.lower() in current_content.lower():
                            print(f"       🎉 SUCCESS! Content filled successfully")
                            working_selectors.append(selector)
                            
                            # Clear the content for next test
                            element.click()
                            page.keyboard.press("Control+a")
                            page.keyboard.press("Delete")
                            time.sleep(0.5)
                        else:
                            print(f"       ❌ Content not filled (got: '{current_content[:50]}...')")
                    
                    except Exception as fill_error:
                        print(f"       ❌ Error filling content: {fill_error}")
                
                else:
                    print(f"       ❌ Element not found or not visible")
                    
            except Exception as e:
                print(f"       ❌ Error testing selector: {e}")
        
        # Report results
        print(f"\n" + "=" * 60)
        print("📊 BODY FIELD SELECTOR TEST RESULTS")
        print("=" * 60)
        
        if working_selectors:
            print(f"🎉 SUCCESS! Found {len(working_selectors)} working selector(s):")
            for i, selector in enumerate(working_selectors, 1):
                print(f"   {i}. {selector}")
            
            print(f"\n📋 Recommended action:")
            print(f"   Update the body_field selectors in email_composer.py")
            print(f"   Put the working selector(s) at the top of the list")
            
            # Test with the best working selector
            best_selector = working_selectors[0]
            print(f"\n🧪 Final test with best selector: {best_selector}")
            
            try:
                element = page.query_selector(best_selector)
                if element:
                    element.click()
                    time.sleep(0.5)
                    page.keyboard.press("Control+a")
                    page.keyboard.press("Delete")
                    time.sleep(0.5)
                    
                    final_test_content = "Final test: Body field is working perfectly! ✅"
                    page.keyboard.type(final_test_content)
                    time.sleep(2)
                    
                    print(f"✅ Final test successful!")
                    print(f"   Content: {final_test_content}")
                    
            except Exception as e:
                print(f"❌ Final test failed: {e}")
        
        else:
            print("❌ No working selectors found!")
            print("   The body field might use a different approach (iframe, shadow DOM, etc.)")
            print("   Manual inspection of the HTML structure is needed.")
        
        # Keep browser open for inspection
        print(f"\n⏹️  Keeping browser open for 30 seconds for manual inspection...")
        print("   You can manually inspect the compose window to identify the body field.")
        
        for i in range(30, 0, -1):
            print(f"   Closing in {i} seconds...", end='\r')
            time.sleep(1)
        
        print("\n🛑 Closing browser...")
        
        # Cleanup
        page.close()
        browser_handler.close_browser()
        print("✅ Browser closed")
        
        return len(working_selectors) > 0
        
    except Exception as e:
        print(f"❌ Error during body field test: {e}")
        return False

def main():
    """Main function."""
    print("BULK_MAILER - Body Field Selector Fix Test")
    print("This test will identify the correct body field selector for ProtonMail.")
    print()
    
    success = test_body_field_selectors()
    
    if success:
        print("\n🎉 Body field selector test completed successfully!")
        print("Working selectors have been identified.")
    else:
        print("\n❌ Body field selector test failed!")
        print("Manual inspection may be required.")

if __name__ == "__main__":
    main()
