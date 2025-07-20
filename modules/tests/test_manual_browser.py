#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Manual Browser Test
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Manual browser test for ProtonMail automation.
#              Opens browser with cookies loaded and keeps it open for manual testing.
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

def test_manual_browser():
    """Open browser with ProtonMail cookies for manual testing."""
    
    print("=" * 60)
    print("🌐 MANUAL BROWSER TEST - ProtonMail")
    print("=" * 60)
    print("This will open a browser with your ProtonMail cookies loaded.")
    print("The browser will stay open for manual testing.")
    print("Press Ctrl+C when you're done testing.")
    print("=" * 60)
    
    try:
        # Setup
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        config = ConfigLoader(base_dir)
        app_logger = AppLogger(config.base_dir, config_path=config.config_path)
        logger = app_logger.get_logger()
        
        # Load configurations
        browser_config = config.get_browser_automation_settings()
        senders_data = config.get_senders()
        
        # Find ProtonMail sender
        protonmail_sender = None
        for sender in senders_data:
            if sender.get('provider', '').lower() == 'protonmail':
                protonmail_sender = sender
                break
        
        if not protonmail_sender:
            print("❌ No ProtonMail sender found in configuration")
            return False
        
        email = protonmail_sender['email']
        cookie_file = protonmail_sender['cookie_file']
        
        print(f"📧 Testing with: {email}")
        print(f"🍪 Cookie file: {cookie_file}")
        
        # Check cookie file exists
        if not os.path.exists(cookie_file):
            print(f"❌ Cookie file not found: {cookie_file}")
            return False
        
        print("✅ Cookie file found")
        
        # Create browser handler
        print("\n🚀 Starting browser...")
        browser_handler = BrowserHandler(browser_config, logger)
        
        # Start Playwright
        if not browser_handler.start_playwright():
            print("❌ Failed to start Playwright")
            return False
        
        print("✅ Playwright started")
        
        # Launch browser
        if not browser_handler.launch_browser():
            print("❌ Failed to launch browser")
            return False
        
        print("✅ Browser launched")
        
        # Create context with cookies
        print(f"\n🍪 Loading cookies for {email}...")
        context = browser_handler.create_context_with_cookies(email, cookie_file)
        
        if not context:
            print("❌ Failed to create browser context with cookies")
            browser_handler.close_browser()
            return False
        
        print("✅ Browser context created with cookies")
        
        # Create page
        print("\n📄 Creating page...")
        page = browser_handler.create_page(email)
        
        if not page:
            print("❌ Failed to create page")
            browser_handler.close_browser()
            return False
        
        print("✅ Page created")
        
        # Navigate to ProtonMail
        print("\n🌐 Navigating to ProtonMail...")
        page.goto("https://mail.proton.me", wait_until="domcontentloaded", timeout=30000)
        
        print("✅ Navigated to ProtonMail")
        print("\n" + "=" * 60)
        print("🎉 BROWSER IS NOW OPEN WITH COOKIES LOADED!")
        print("=" * 60)
        print("📋 What you can do now:")
        print("1. Check if you're logged into ProtonMail")
        print("2. Try navigating around the interface")
        print("3. Test email composition manually")
        print("4. Check if all elements are accessible")
        print()
        print("🔍 Browser Details:")
        print(f"   - Email: {email}")
        print(f"   - URL: https://mail.proton.me")
        print(f"   - Headless: {browser_config.get('headless', False)}")
        print()
        print("⏹️  Press Ctrl+C when you're done testing...")
        print("=" * 60)
        
        # Keep browser open until user interrupts
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 User interrupted - closing browser...")
        
        # Cleanup
        print("🧹 Cleaning up...")
        page.close()
        browser_handler.close_browser()
        print("✅ Browser closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during manual browser test: {e}")
        return False

def main():
    """Main function."""
    success = test_manual_browser()
    
    if success:
        print("\n✅ Manual browser test completed successfully!")
    else:
        print("\n❌ Manual browser test failed!")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
