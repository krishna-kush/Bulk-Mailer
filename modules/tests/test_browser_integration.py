# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Integration test for browser automation functionality.
#              Tests actual browser automation with real ProtonMail interface.
#
# Components: - Real Browser Testing
#             - Cookie Validation
#             - ProtonMail Interface Testing
#             - Email Composition Testing
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

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config_loader import ConfigLoader
from modules.logger.logger import AppLogger
from modules.browser.browser_handler import BrowserHandler
from modules.browser.providers.protonmail_automation import ProtonMailAutomation
from modules.browser.browser_email_sender import BrowserEmailSender

def test_browser_automation():
    """Test browser automation functionality with real browser."""
    
    # Setup
    base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
    config = ConfigLoader(base_dir)
    app_logger = AppLogger(config.base_dir, config_path=config.config_path)
    logger = app_logger.get_logger()
    
    logger.info("=" * 60)
    logger.info("BROWSER AUTOMATION INTEGRATION TEST")
    logger.info("=" * 60)
    
    try:
        # Load configurations
        browser_config = config.get_browser_automation_settings()
        providers_config = config.get_browser_providers_settings()
        senders_data = config.get_senders()
        
        logger.info(f"Browser automation enabled: {browser_config.get('enable_browser_automation')}")
        logger.info(f"Headless mode: {browser_config.get('headless')}")
        logger.info(f"Available providers: {list(providers_config.keys())}")
        
        # Find a ProtonMail sender for testing
        protonmail_sender = None
        for sender in senders_data:
            if sender.get('provider', '').lower() == 'protonmail':
                protonmail_sender = sender
                break
        
        if not protonmail_sender:
            logger.error("No ProtonMail sender found in configuration")
            logger.info("Please configure a ProtonMail sender with provider='protonmail' and valid cookie_file")
            return False
        
        logger.info(f"Testing with ProtonMail sender: {protonmail_sender['email']}")
        
        # Check if cookie file exists
        cookie_file = protonmail_sender.get('cookie_file')
        if not cookie_file or not os.path.exists(cookie_file):
            logger.error(f"Cookie file not found: {cookie_file}")
            logger.info("Please ensure the cookie file exists and contains valid ProtonMail cookies")
            return False
        
        logger.info(f"Cookie file found: {cookie_file}")
        
        # Test 1: Browser Handler
        logger.info("\n--- Test 1: Browser Handler ---")
        browser_handler = BrowserHandler(browser_config, logger)
        
        if not browser_handler.start_playwright():
            logger.error("Failed to start Playwright")
            return False
        
        if not browser_handler.launch_browser():
            logger.error("Failed to launch browser")
            return False
        
        logger.info("✓ Browser handler initialized successfully")
        
        # Test 2: Cookie Loading
        logger.info("\n--- Test 2: Cookie Loading ---")
        context = browser_handler.create_context_with_cookies(
            protonmail_sender['email'], 
            cookie_file
        )
        
        if not context:
            logger.error("Failed to create browser context with cookies")
            browser_handler.close_browser()
            return False
        
        logger.info("✓ Browser context created with cookies")
        
        # Test 3: ProtonMail Login Validation
        logger.info("\n--- Test 3: ProtonMail Login Validation ---")
        page = browser_handler.create_page(protonmail_sender['email'])
        
        if not page:
            logger.error("Failed to create page")
            browser_handler.close_browser()
            return False
        
        protonmail_automation = ProtonMailAutomation(
            providers_config['protonmail'], 
            logger
        )
        
        is_logged_in = protonmail_automation.validate_login(page)
        
        if not is_logged_in:
            logger.error("ProtonMail login validation failed")
            logger.info("Please check if cookies are valid and not expired")
            page.close()
            browser_handler.close_browser()
            return False
        
        logger.info("✓ ProtonMail login validation successful")
        
        # Test 4: Email Composition (without sending)
        logger.info("\n--- Test 4: Email Composition Test ---")
        
        # Navigate to mail interface
        if not protonmail_automation.navigate_to_mail(page):
            logger.error("Failed to navigate to ProtonMail interface")
            page.close()
            browser_handler.close_browser()
            return False
        
        # Open compose window
        if not protonmail_automation.open_compose(page):
            logger.error("Failed to open compose window")
            page.close()
            browser_handler.close_browser()
            return False
        
        logger.info("✓ Compose window opened successfully")
        
        # Fill test data (but don't send)
        test_recipient = "test@example.com"
        test_subject = "Browser Automation Test"
        test_body = "This is a test email from browser automation system."
        
        if not protonmail_automation.fill_recipient(page, test_recipient):
            logger.error("Failed to fill recipient")
            page.close()
            browser_handler.close_browser()
            return False
        
        if not protonmail_automation.fill_subject(page, test_subject):
            logger.error("Failed to fill subject")
            page.close()
            browser_handler.close_browser()
            return False
        
        if not protonmail_automation.fill_body(page, test_body, "plain"):
            logger.error("Failed to fill body")
            page.close()
            browser_handler.close_browser()
            return False
        
        logger.info("✓ Email composition successful")
        logger.info("  - Recipient filled")
        logger.info("  - Subject filled")
        logger.info("  - Body filled")
        
        # Take screenshot for verification
        if browser_config.get('screenshot_on_error', True):
            browser_handler.take_screenshot(page, "composition_test.png")
            logger.info("✓ Screenshot saved for verification")
        
        # Test 5: Browser Email Sender
        logger.info("\n--- Test 5: Browser Email Sender ---")
        browser_sender = BrowserEmailSender(browser_config, providers_config, logger)
        
        if not browser_sender.start_browser():
            logger.error("Failed to start browser email sender")
            page.close()
            browser_handler.close_browser()
            return False
        
        # Validate sender configuration
        if not browser_sender.validate_sender_cookies(protonmail_sender):
            logger.error("Sender cookie validation failed")
            browser_sender.close()
            page.close()
            browser_handler.close_browser()
            return False
        
        logger.info("✓ Browser email sender validation successful")
        
        # Cleanup
        logger.info("\n--- Cleanup ---")
        page.close()
        browser_sender.close()
        browser_handler.close_browser()
        
        logger.info("✓ All resources cleaned up")
        
        # Success
        logger.info("\n" + "=" * 60)
        logger.info("✅ BROWSER AUTOMATION TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info("All browser automation components are working correctly!")
        logger.info("You can now use browser automation mode by setting:")
        logger.info("  sending_mode = browser")
        logger.info("in your config.ini file.")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Browser automation test failed: {e}")
        logger.error("Please check your configuration and try again")
        return False

def main():
    """Main function to run the integration test."""
    print("Starting Browser Automation Integration Test...")
    print("This test will verify that browser automation is working correctly.")
    print("Make sure you have:")
    print("1. Valid ProtonMail cookies saved")
    print("2. Playwright installed (pip install playwright)")
    print("3. Browser binaries installed (playwright install)")
    print()
    
    success = test_browser_automation()
    
    if success:
        print("\n🎉 Browser automation is ready to use!")
        sys.exit(0)
    else:
        print("\n❌ Browser automation test failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
