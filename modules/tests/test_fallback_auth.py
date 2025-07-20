#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Fallback Authentication Test
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Test script for the robust fallback authentication system.
#              Tests both cookie and password authentication with HTML debugging.
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
from modules.browser.providers.protonmail_automation import ProtonMailAutomation

def test_fallback_authentication():
    """Test the fallback authentication system."""
    
    print("=" * 60)
    print("🔐 FALLBACK AUTHENTICATION TEST")
    print("=" * 60)
    print("This will test both cookie and password authentication.")
    print("HTML captures will be saved for debugging.")
    print("Browser will stay open - DO NOT CLOSE IT!")
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
        cookie_file = protonmail_sender.get('cookie_file', '')
        
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {'***' if password else 'Not provided'}")
        print(f"🍪 Cookie file: {cookie_file}")
        print(f"🍪 Cookie exists: {os.path.exists(cookie_file) if cookie_file else False}")
        
        # Create browser handler
        print(f"\n🚀 Step 1: Starting browser...")
        browser_handler = BrowserHandler(browser_config, logger)
        
        if not browser_handler.start_playwright():
            print("❌ Failed to start Playwright")
            return False
        print("✅ Playwright started")
        
        if not browser_handler.launch_browser():
            print("❌ Failed to launch browser")
            return False
        print("✅ Browser launched")
        
        # Create context with cookies (if available)
        print(f"\n🍪 Step 2: Creating browser context...")
        if cookie_file and os.path.exists(cookie_file):
            context = browser_handler.create_context_with_cookies(email, cookie_file)
            print("✅ Context created with cookies")
        else:
            # Create context without cookies for password-only test
            context = browser_handler.browser.new_context()
            browser_handler.contexts[email] = context
            print("✅ Context created without cookies")
        
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
        print("✅ Page created")
        
        # Create ProtonMail automation with HTML capture
        print(f"\n🤖 Step 4: Initializing ProtonMail automation...")
        protonmail_automation = ProtonMailAutomation(
            providers_config['protonmail'], 
            logger,
            base_dir
        )
        print("✅ ProtonMail automation initialized")
        
        # Test fallback authentication
        print(f"\n🔐 Step 5: Testing fallback authentication...")
        auth_success = protonmail_automation.authenticate_with_fallback(page, email, password)
        
        if auth_success:
            print("✅ Authentication successful!")
            
            # Test email composition (without sending)
            print(f"\n📝 Step 6: Testing email composition...")
            
            # Open compose window
            if protonmail_automation.open_compose(page):
                print("✅ Compose window opened")
                
                # Fill test data
                test_recipient = "test@example.com"
                test_subject = "Fallback Authentication Test"
                test_body = "This is a test of the fallback authentication system."
                
                if protonmail_automation.fill_recipient(page, test_recipient):
                    print("✅ Recipient filled")
                    
                    if protonmail_automation.fill_subject(page, test_subject):
                        print("✅ Subject filled")
                        
                        if protonmail_automation.fill_body(page, test_body, "plain"):
                            print("✅ Body filled")
                            print("📧 Email composition test successful!")
                        else:
                            print("❌ Failed to fill body")
                    else:
                        print("❌ Failed to fill subject")
                else:
                    print("❌ Failed to fill recipient")
            else:
                print("❌ Failed to open compose window")
        else:
            print("❌ Authentication failed!")
        
        # Show HTML capture information
        if hasattr(protonmail_automation, 'html_capture') and protonmail_automation.html_capture:
            capture_info = protonmail_automation.html_capture.get_session_summary()
            print(f"\n📸 HTML Capture Summary:")
            print(f"   - Session ID: {capture_info['session_id']}")
            print(f"   - Captures taken: {capture_info['capture_count']}")
            print(f"   - Capture directory: {capture_info['capture_dir']}")
            print(f"   - Files pattern: {capture_info['files_pattern']}")
        
        # Final assessment
        print(f"\n" + "=" * 60)
        print("📊 FALLBACK AUTHENTICATION TEST RESULTS")
        print("=" * 60)
        
        if auth_success:
            print("✅ SUCCESS: Fallback authentication system working!")
            print("   - Authentication completed successfully")
            print("   - Email composition interface accessible")
            print("   - HTML captures saved for analysis")
        else:
            print("❌ FAILURE: Fallback authentication failed")
            print("   - Check HTML captures for debugging")
            print("   - Verify credentials and cookie files")
        
        print(f"\n📋 Next Steps:")
        if auth_success:
            print("1. ✅ System is ready for production use")
            print("2. 📧 You can now send emails using browser automation")
            print("3. 🔍 Review HTML captures if needed for optimization")
        else:
            print("1. 🔍 Check HTML captures in logs/html_captures/")
            print("2. 🔑 Verify password is correct")
            print("3. 🍪 Export fresh cookies if using cookie authentication")
            print("4. 🌐 Check ProtonMail interface for changes")
        
        print(f"\n⏹️  Keeping browser open for 10 seconds for inspection...")

        # Keep browser open for a short time
        for i in range(10, 0, -1):
            print(f"   Closing in {i} seconds...", end='\r')
            time.sleep(1)

        print("\n🛑 Closing browser...")

        # Cleanup
        page.close()
        browser_handler.close_browser()
        print("✅ Browser closed")
        
        return auth_success
        
    except Exception as e:
        print(f"❌ Error during fallback authentication test: {e}")
        return False

def main():
    """Main function."""
    print("BULK_MAILER - Fallback Authentication Test")
    print("This test will verify the robust fallback authentication system.")
    print()
    
    success = test_fallback_authentication()
    
    if success:
        print("\n🎉 Fallback authentication test completed successfully!")
        print("The system can now handle both cookie and password authentication.")
    else:
        print("\n❌ Fallback authentication test failed!")
        print("Please check the HTML captures and logs for debugging.")

if __name__ == "__main__":
    main()
