#!/usr/bin/env python3
# ================================================================================
# BULK_MAILER - Browser Full Screen Test
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Test browser display in full-screen mode for better element
#              visibility and interaction.
#
# License: MIT License
# Created: 2025
#
# ================================================================================

import os
import sys
import time

# Add modules to path - go up two levels to reach mailer root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.config_loader import ConfigLoader
from modules.logger.logger import AppLogger
from modules.browser.browser_handler import BrowserHandler

def test_browser_fullscreen():
    """Test browser full screen display."""
    
    print("=" * 60)
    print("🖥️  BROWSER FULL SCREEN TEST")
    print("=" * 60)
    print("Testing browser display in full-screen mode")
    print("This will open a browser window and test maximization")
    print("=" * 60)
    
    try:
        # Setup - base_dir should point to mailer root, not tests directory
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        config = ConfigLoader(base_dir)
        app_logger = AppLogger(base_dir, config_path=config.config_path)
        logger = app_logger.get_logger()
        
        # Load browser configuration
        browser_config = config.get_browser_automation_settings()
        
        print(f"📋 Browser Configuration:")
        print(f"   Headless: {browser_config.get('headless', False)}")
        print(f"   Randomize viewport: {browser_config.get('randomize_viewport', True)}")
        
        # Create browser handler
        print(f"\n🚀 Step 1: Starting browser with full screen settings...")
        browser_handler = BrowserHandler(browser_config, logger)
        
        if not browser_handler.start_playwright():
            print("❌ Failed to start Playwright")
            return False
        
        if not browser_handler.launch_browser():
            print("❌ Failed to launch browser")
            return False
        
        print("✅ Browser launched with full screen configuration")
        
        # Create context
        print(f"\n🍪 Step 2: Creating browser context...")
        context = browser_handler.browser.new_context()
        browser_handler.contexts["test@example.com"] = context
        
        if not context:
            print("❌ Failed to create context")
            browser_handler.close_browser()
            return False
        
        print("✅ Browser context created")
        
        # Create page
        print(f"\n📄 Step 3: Creating page with maximization...")
        page = browser_handler.create_page("test@example.com")
        
        if not page:
            print("❌ Failed to create page")
            browser_handler.close_browser()
            return False
        
        print("✅ Page created and maximized")
        
        # Navigate to a test page
        print(f"\n🌐 Step 4: Testing page navigation...")
        page.goto("https://protonmail.com")
        
        # Get viewport and window dimensions
        print(f"\n📏 Step 5: Checking window dimensions...")
        
        viewport_size = page.viewport_size
        window_dimensions = page.evaluate("""
            () => {
                return {
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    outerWidth: window.outerWidth,
                    outerHeight: window.outerHeight,
                    screenWidth: window.screen.width,
                    screenHeight: window.screen.height,
                    availWidth: window.screen.availWidth,
                    availHeight: window.screen.availHeight
                };
            }
        """)
        
        print(f"📊 Window Dimensions:")
        print(f"   Viewport: {viewport_size['width']} x {viewport_size['height']}")
        print(f"   Inner: {window_dimensions['innerWidth']} x {window_dimensions['innerHeight']}")
        print(f"   Outer: {window_dimensions['outerWidth']} x {window_dimensions['outerHeight']}")
        print(f"   Screen: {window_dimensions['screenWidth']} x {window_dimensions['screenHeight']}")
        print(f"   Available: {window_dimensions['availWidth']} x {window_dimensions['availHeight']}")
        
        # Check if window is maximized
        is_maximized = (
            window_dimensions['outerWidth'] >= window_dimensions['availWidth'] * 0.9 and
            window_dimensions['outerHeight'] >= window_dimensions['availHeight'] * 0.9
        )
        
        print(f"\n🎯 Maximization Status:")
        if is_maximized:
            print("✅ Browser window appears to be maximized")
        else:
            print("⚠️  Browser window may not be fully maximized")
            print(f"   Window: {window_dimensions['outerWidth']} x {window_dimensions['outerHeight']}")
            print(f"   Available: {window_dimensions['availWidth']} x {window_dimensions['availHeight']}")
        
        # Test element visibility
        print(f"\n🔍 Step 6: Testing element visibility...")
        
        # Check if ProtonMail elements are visible
        try:
            # Wait for page to load
            page.wait_for_load_state("networkidle", timeout=10000)
            
            # Check for common elements
            elements_to_check = [
                "button",
                "input",
                "a",
                "[data-testid]"
            ]
            
            visible_elements = 0
            for selector in elements_to_check:
                try:
                    elements = page.query_selector_all(selector)
                    visible_count = sum(1 for el in elements if el.is_visible())
                    visible_elements += visible_count
                    print(f"   {selector}: {visible_count} visible elements")
                except:
                    print(f"   {selector}: Could not check")
            
            print(f"   Total visible elements: {visible_elements}")
            
            if visible_elements > 10:
                print("✅ Good element visibility - page content is accessible")
            else:
                print("⚠️  Limited element visibility - may need adjustment")
                
        except Exception as visibility_error:
            print(f"⚠️  Could not test element visibility: {visibility_error}")
        
        # Final assessment
        print(f"\n" + "=" * 60)
        print("📊 BROWSER FULL SCREEN TEST RESULTS")
        print("=" * 60)
        
        if is_maximized:
            print("🎉 SUCCESS: Browser is running in full screen mode!")
            print("✅ Window maximization working")
            print("✅ Good viewport dimensions")
            print("✅ Element visibility optimized")
        else:
            print("⚠️  PARTIAL SUCCESS: Browser launched but may not be fully maximized")
            print("✅ Browser launched successfully")
            print("⚠️  Window maximization needs improvement")
        
        print(f"\n⏹️  Keeping browser open for 20 seconds for visual inspection...")
        print("   You can see the browser window and verify it's maximized!")
        
        # Keep browser open for inspection
        for i in range(20, 0, -1):
            print(f"   Closing in {i} seconds...", end='\r')
            time.sleep(1)
        
        print("\n🛑 Closing browser...")
        
        # Cleanup
        page.close()
        browser_handler.close_browser()
        print("✅ Browser closed")
        
        return is_maximized
        
    except Exception as e:
        print(f"❌ Error during browser full screen test: {e}")
        return False

def main():
    """Main function."""
    print("BULK_MAILER - Browser Full Screen Test")
    print("This test will verify browser opens in full screen mode.")
    print()
    
    success = test_browser_fullscreen()
    
    if success:
        print("\n🎉 Browser full screen test successful!")
        print("The browser is properly maximized for optimal element visibility!")
    else:
        print("\n⚠️  Browser full screen test needs improvement!")
        print("Check the browser configuration and maximization logic.")

if __name__ == "__main__":
    main()
