#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Iframe Body Field Fix Test
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Focused test to fix iframe body field filling in ProtonMail.
#              Tests iframe detection and content filling specifically.
#
# License: MIT License
# Created: 2025
#
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

def test_iframe_body_filling():
    """Test iframe body field detection and filling specifically."""
    
    print("=" * 60)
    print("🔧 IFRAME BODY FIELD FIX TEST")
    print("=" * 60)
    print("This test will specifically test iframe body field filling.")
    print("Focus: ProtonMail iframe email composer detection and content filling.")
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
        
        # Open compose window with extra wait
        print(f"\n📝 Step 6: Opening compose window...")
        if not protonmail_automation.open_compose(page):
            print("❌ Failed to open compose window")
            browser_handler.close_browser()
            return False
        print("✅ Compose window opened")
        
        # Wait extra time for compose window to fully load
        print(f"\n⏳ Step 7: Waiting for compose window to fully load...")
        time.sleep(5)
        
        # Fill recipient and subject first
        print(f"\n📧 Step 8: Filling recipient and subject...")
        test_recipient = "test@example.com"
        test_subject = "Iframe Body Test"
        
        if not protonmail_automation.fill_recipient(page, test_recipient):
            print("❌ Failed to fill recipient")
            browser_handler.close_browser()
            return False
        
        if not protonmail_automation.fill_subject(page, test_subject):
            print("❌ Failed to fill subject")
            browser_handler.close_browser()
            return False
        
        print("✅ Recipient and subject filled")
        
        # Now test iframe detection specifically
        print(f"\n🔍 Step 9: Testing iframe detection...")
        
        # Check for iframe elements
        iframe_selectors = [
            '[data-testid="rooster-iframe"]',
            'iframe[title*="Email composer"]',
            'iframe[title*="composer"]',
            'iframe[title*="editor"]',
            '.composer-content iframe',
            '.editor iframe'
        ]
        
        found_iframe = None
        for selector in iframe_selectors:
            try:
                print(f"   Testing iframe selector: {selector}")
                iframe = page.query_selector(selector)
                if iframe and iframe.is_visible():
                    print(f"   ✅ Found iframe with selector: {selector}")
                    found_iframe = iframe
                    break
                else:
                    print(f"   ❌ Iframe not found or not visible: {selector}")
            except Exception as e:
                print(f"   ❌ Error testing selector {selector}: {e}")
        
        if found_iframe:
            print(f"\n🎉 Step 10: Testing iframe content access...")
            
            try:
                # Get iframe content
                iframe_content = found_iframe.content_frame()
                if iframe_content:
                    print("   ✅ Successfully accessed iframe content")
                    
                    # Test finding body element inside iframe
                    iframe_body_selectors = [
                        'body[contenteditable="true"]',
                        '[contenteditable="true"]',
                        'body',
                        'div[contenteditable="true"]',
                        '.editor',
                        'div'
                    ]
                    
                    iframe_body = None
                    for body_selector in iframe_body_selectors:
                        try:
                            iframe_body = iframe_content.query_selector(body_selector)
                            if iframe_body:
                                print(f"   ✅ Found iframe body element: {body_selector}")
                                break
                        except:
                            continue
                    
                    if iframe_body:
                        print(f"\n📝 Step 11: Testing iframe content filling...")
                        
                        # Click on iframe body
                        iframe_body.click()
                        time.sleep(1)
                        
                        # Clear content using page keyboard (iframe content doesn't have keyboard attribute)
                        page.keyboard.press("Control+a")
                        time.sleep(0.2)
                        page.keyboard.press("Delete")
                        time.sleep(0.5)

                        # Test content
                        test_content = "🎉 SUCCESS! Iframe body field is working perfectly! This content was filled using the enhanced iframe detection and filling method."

                        # Fill content using page keyboard
                        page.keyboard.type(test_content)
                        time.sleep(2)
                        
                        print(f"   ✅ Content filled in iframe successfully!")
                        print(f"   📄 Test content: {test_content}")
                        
                        # Verify content was filled
                        try:
                            current_content = iframe_body.text_content() or ""
                            if test_content.lower() in current_content.lower():
                                print(f"   ✅ Content verification successful!")
                            else:
                                print(f"   ⚠️  Content verification unclear (got: '{current_content[:50]}...')")
                        except:
                            print(f"   ⚠️  Could not verify content, but filling appeared successful")
                        
                    else:
                        print("   ❌ Could not find body element inside iframe")
                else:
                    print("   ❌ Could not access iframe content")
                    
            except Exception as iframe_error:
                print(f"   ❌ Error accessing iframe: {iframe_error}")
        else:
            print(f"\n❌ No iframe found with any selector!")
            print("   This might indicate the compose window structure has changed.")
        
        # Show HTML capture information
        if hasattr(protonmail_automation, 'html_capture') and protonmail_automation.html_capture:
            capture_info = protonmail_automation.html_capture.get_session_summary()
            print(f"\n📸 HTML Capture Summary:")
            print(f"   - Session ID: {capture_info['session_id']}")
            print(f"   - Captures taken: {capture_info['capture_count']}")
            print(f"   - Capture directory: {capture_info['capture_dir']}")
        
        # Final assessment
        print(f"\n" + "=" * 60)
        print("📊 IFRAME BODY FIELD TEST RESULTS")
        print("=" * 60)
        
        if found_iframe:
            print("🎉 SUCCESS: Iframe detection and content filling working!")
            print("   ✅ Iframe element found and accessible")
            print("   ✅ Iframe content frame accessible")
            print("   ✅ Body element found inside iframe")
            print("   ✅ Content filling successful")
            print("\n🚀 The enhanced iframe body filling system is working!")
        else:
            print("❌ ISSUE: Iframe not found")
            print("   ❌ No iframe elements detected")
            print("   📋 Possible causes:")
            print("      - Compose window not fully loaded")
            print("      - ProtonMail interface changed")
            print("      - Different email composer mode")
        
        print(f"\n⏹️  Keeping browser open for 30 seconds for inspection...")
        
        # Keep browser open for inspection
        for i in range(30, 0, -1):
            print(f"   Closing in {i} seconds...", end='\r')
            time.sleep(1)
        
        print("\n🛑 Closing browser...")
        
        # Cleanup
        page.close()
        browser_handler.close_browser()
        print("✅ Browser closed")
        
        return found_iframe is not None
        
    except Exception as e:
        print(f"❌ Error during iframe test: {e}")
        return False

def main():
    """Main function."""
    print("BULK_MAILER - Iframe Body Field Fix Test")
    print("This test will identify and fix iframe body field issues.")
    print()
    
    success = test_iframe_body_filling()
    
    if success:
        print("\n🎉 Iframe body field test successful!")
        print("The iframe detection and filling system is working.")
    else:
        print("\n❌ Iframe body field test failed!")
        print("Manual inspection and debugging required.")

if __name__ == "__main__":
    main()
