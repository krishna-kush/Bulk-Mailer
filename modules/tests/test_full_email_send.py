#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Full Email Send Test
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Simple full email send test that bypasses the complex queue system
#              and directly sends emails to recipients.csv using the enhanced
#              iframe body filling system.
#
# License: MIT License
# Created: 2025
#
# ================================================================================

import os
import sys
import time
import csv

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config_loader import ConfigLoader
from modules.logger.logger import AppLogger
from modules.browser.browser_handler import BrowserHandler
from modules.browser.providers.protonmail import ProtonMailAutomation

def load_recipients(recipients_path):
    """Load recipients from CSV file."""
    recipients = []
    try:
        with open(recipients_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():  # Skip empty rows
                    recipients.append(row[0].strip())
        return recipients
    except Exception as e:
        print(f"❌ Error loading recipients: {e}")
        return []

def test_full_email_send():
    """Test full email sending to recipients.csv."""
    
    print("=" * 70)
    print("📧 FULL EMAIL SEND TEST")
    print("=" * 70)
    print("This test will send real emails to recipients in recipients.csv")
    print("Using the complete system with:")
    print("✅ Enhanced iframe body filling")
    print("✅ Manual randomization processing")
    print("✅ Fallback authentication")
    print("✅ Real email templates")
    print("=" * 70)
    
    try:
        # Setup
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        config = ConfigLoader(base_dir)
        app_logger = AppLogger(config.base_dir, config_path=config.config_path)
        logger = app_logger.get_logger()
        
        # Load all configurations
        browser_config = config.get_browser_automation_settings()
        providers_config = config.get_browser_providers_settings()
        senders_data = config.get_senders()
        email_personalization = config.get_email_personalization_settings()
        email_anti_spam = config.get_email_anti_spam_settings()
        email_content = config.get_email_content_settings()
        
        # Merge settings for complete configuration
        combined_email_settings = {**email_personalization, **email_anti_spam}
        
        print(f"📋 System Configuration:")
        print(f"   ✅ Manual randomization: {combined_email_settings.get('enable_manual_randomization', False)}")
        print(f"   ✅ HTML obfuscation: {combined_email_settings.get('enable_html_obfuscation', False)}")
        print(f"   ✅ Content type: {email_content.get('content_type', 'html')}")
        
        # Load recipients
        recipients_path = config.get_recipients_settings().get('recipients_path', 'recipients.csv')
        recipients = load_recipients(recipients_path)
        
        if not recipients:
            print("❌ No recipients found")
            return False
        
        print(f"\n📧 Recipients loaded: {len(recipients)} emails")
        for i, recipient in enumerate(recipients, 1):
            print(f"   {i}. {recipient}")
        
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
        
        print(f"\n📧 Sender: {email}")
        print(f"🔑 Authentication: {'Password + Cookie fallback' if password else 'Cookie only'}")
        
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
        
        # Create ProtonMail automation
        print(f"\n🤖 Step 3: Initializing ProtonMail automation...")
        protonmail_automation = ProtonMailAutomation(
            providers_config['protonmail'], 
            logger,
            base_dir,
            combined_email_settings,
            email_content
        )
        
        # Send emails to each recipient
        print(f"\n📧 Step 4: Sending emails...")
        
        sent_count = 0
        failed_count = 0
        
        for i, recipient in enumerate(recipients, 1):
            print(f"\n📧 Sending email {i}/{len(recipients)} to: {recipient}")
            
            try:
                # Create a new page for each email
                page = browser_handler.create_page(email)
                if not page:
                    print(f"   ❌ Failed to create page for {recipient}")
                    failed_count += 1
                    continue
                
                # Send email using the complete workflow
                success = protonmail_automation.compose_and_send_email_with_processing(
                    page, recipient, email, password
                )
                
                if success:
                    print(f"   ✅ Email sent successfully to {recipient}")
                    sent_count += 1
                else:
                    print(f"   ❌ Failed to send email to {recipient}")
                    failed_count += 1
                
                # Close page
                page.close()
                
                # Add delay between emails
                if i < len(recipients):
                    delay = 5  # 5 seconds between emails
                    print(f"   ⏳ Waiting {delay} seconds before next email...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"   ❌ Error sending to {recipient}: {e}")
                failed_count += 1
                try:
                    page.close()
                except:
                    pass
        
        # Show HTML capture information
        if hasattr(protonmail_automation, 'html_capture') and protonmail_automation.html_capture:
            capture_info = protonmail_automation.html_capture.get_session_summary()
            print(f"\n📸 HTML Capture Summary:")
            print(f"   - Session ID: {capture_info['session_id']}")
            print(f"   - Captures taken: {capture_info['capture_count']}")
            print(f"   - Capture directory: {capture_info['capture_dir']}")
        
        # Final results
        print(f"\n" + "=" * 70)
        print("📊 FULL EMAIL SEND TEST RESULTS")
        print("=" * 70)
        print(f"📧 Total recipients: {len(recipients)}")
        print(f"✅ Successfully sent: {sent_count}")
        print(f"❌ Failed to send: {failed_count}")
        print(f"📈 Success rate: {(sent_count/len(recipients)*100):.1f}%" if recipients else "0%")
        
        if sent_count > 0:
            print(f"\n🎉 SUCCESS: {sent_count} email(s) sent successfully!")
            print("✅ Enhanced iframe body filling working")
            print("✅ Manual randomization applied")
            print("✅ Complete email workflow functional")
        else:
            print(f"\n❌ No emails sent successfully")
            print("Check the logs and HTML captures for debugging")
        
        print(f"\n⏹️  Keeping browser open for 15 seconds for inspection...")
        
        # Keep browser open for inspection
        for i in range(15, 0, -1):
            print(f"   Closing in {i} seconds...", end='\r')
            time.sleep(1)
        
        print("\n🛑 Closing browser...")
        
        # Cleanup
        browser_handler.close_browser()
        print("✅ Browser closed")
        
        return sent_count > 0
        
    except Exception as e:
        print(f"❌ Error during full email send test: {e}")
        return False

def main():
    """Main function."""
    print("BULK_MAILER - Full Email Send Test")
    print("This test will send real emails to recipients.csv using the complete system.")
    print()
    
    # Confirmation prompt
    response = input("⚠️  This will send REAL emails to recipients.csv. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    success = test_full_email_send()
    
    if success:
        print("\n🎉 Full email send test completed successfully!")
        print("The complete email system is working perfectly!")
    else:
        print("\n❌ Full email send test failed!")
        print("Check the logs and HTML captures for debugging.")

if __name__ == "__main__":
    main()
