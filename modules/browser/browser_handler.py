# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Browser automation handler for email sending through web interfaces.
#              Manages Playwright browser instances, cookie loading, and browser
#              lifecycle management for automated email sending.
#
# Components: - Browser Instance Management
#             - Cookie Authentication System
#             - Anti-Detection Measures
#             - Error Handling and Recovery
#             - Screenshot Capture for Debugging
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

import json
import os
import random
import time
import threading
import asyncio
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional, Dict, Any, List

class BrowserHandler:
    """Manages Playwright browser instances for email automation."""
    
    def __init__(self, config: Dict[str, Any], logger):
        """
        Initialize browser handler with configuration and logger.
        
        Args:
            config: Browser automation configuration dictionary
            logger: Logger instance for logging operations
        """
        self.config = config
        self.logger = logger
        self.playwright = None
        self.browser = None
        self.contexts = {}  # Store browser contexts by email
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

        # Thread-local storage for thread-specific browser instances
        self._thread_local = threading.local()

    def _safe_start_playwright(self):
        """Safely start Playwright with proper error handling."""
        try:
            # Try normal startup first - it usually works fine
            playwright_instance = sync_playwright().start()
            self.logger.debug("Playwright started successfully")
            return playwright_instance

        except Exception as e:
            # If normal startup fails due to asyncio conflicts, try workaround
            self.logger.debug(f"Normal Playwright start failed: {e}, trying asyncio workaround...")

            try:
                # Temporarily monkey-patch asyncio detection only if needed
                original_get_running_loop = asyncio.get_running_loop

                def mock_get_running_loop():
                    raise RuntimeError("No running event loop")

                asyncio.get_running_loop = mock_get_running_loop

                try:
                    # Start Playwright with asyncio detection disabled
                    playwright_instance = sync_playwright().start()
                    self.logger.debug("Playwright started with asyncio workaround")
                    return playwright_instance
                finally:
                    # Always restore original function
                    asyncio.get_running_loop = original_get_running_loop

            except Exception as fallback_error:
                self.logger.error(f"Playwright startup failed even with workaround: {fallback_error}")
                return None

    def _get_thread_browser(self):
        """Get or create completely separate browser instance for current thread."""
        if not hasattr(self._thread_local, 'browser') or not self._thread_local.browser:
            # Create completely separate Playwright and browser instances for this thread
            if not hasattr(self._thread_local, 'playwright') or not self._thread_local.playwright:
                self._thread_local.playwright = self._safe_start_playwright()
                if not self._thread_local.playwright:
                    self.logger.error(f"Failed to start Playwright for thread {threading.current_thread().name}")
                    return None
                self.logger.debug(f"Started separate Playwright for thread {threading.current_thread().name}")

            # Configure browser options (same as main browser)
            browser_options = {
                "headless": self.config.get("headless", False),
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                    "--ignore-certificate-errors-spki-list",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            }

            self._thread_local.browser = self._thread_local.playwright.chromium.launch(**browser_options)
            self.logger.debug(f"Launched separate browser for thread {threading.current_thread().name}")

        return self._thread_local.browser

    def _get_thread_contexts(self):
        """Get or create contexts dictionary for current thread."""
        if not hasattr(self._thread_local, 'contexts'):
            self._thread_local.contexts = {}
        return self._thread_local.contexts

    def _get_thread_pages(self):
        """Get or create pages dictionary for current thread."""
        if not hasattr(self._thread_local, 'pages'):
            self._thread_local.pages = {}
        return self._thread_local.pages

    def start_playwright(self) -> bool:
        """
        Start Playwright instance safely.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.playwright is None:
                self.logger.info("Starting Playwright...")
                self.playwright = self._safe_start_playwright()
                if self.playwright:
                    self.logger.info("Playwright started successfully")
                    return True
                else:
                    self.logger.error("Failed to start Playwright safely")
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Playwright: {e}")
            return False
    
    def launch_browser(self) -> bool:
        """
        Launch browser instance with anti-detection measures.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.start_playwright():
                return False
                
            if self.browser is not None:
                self.logger.warning("Browser already launched. Using existing instance.")
                return True
            
            # Configure browser options (simplified approach like LinkedIn automation)
            browser_options = {
                "headless": self.config.get("headless", False),
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                    "--ignore-certificate-errors-spki-list",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            }
            
            self.logger.info(f"Launching browser (headless={self.config.get('headless', False)})...")
            self.browser = self.playwright.chromium.launch(**browser_options)
            self.logger.info("Browser launched successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch browser: {e}")
            return False
    
    def create_context_with_cookies(self, email: str, cookie_file: str) -> Optional[BrowserContext]:
        """
        Create browser context with cookies for specific email account.
        
        Args:
            email: Email address for the account
            cookie_file: Path to cookie file
            
        Returns:
            BrowserContext or None if failed
        """
        try:
            if not os.path.exists(cookie_file):
                self.logger.error(f"Cookie file not found: {cookie_file}")
                return None
            
            # Load cookies from file
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            
            self.logger.info(f"Loaded {len(cookies)} cookies for {email}")
            
            # Fix sameSite values for Playwright compatibility
            for cookie in cookies:
                if 'sameSite' in cookie:
                    samesite_value = cookie['sameSite'].lower()
                    if samesite_value == 'lax':
                        cookie['sameSite'] = 'Lax'
                    elif samesite_value == 'strict':
                        cookie['sameSite'] = 'Strict'
                    elif samesite_value in ['none', 'no_restriction']:
                        cookie['sameSite'] = 'None'
                    else:
                        cookie['sameSite'] = 'Lax'
            
            # Create context exactly like LinkedIn automation (direct parameters)
            context_params = {
                "storage_state": {"cookies": cookies},
                "viewport": {"width": 1920, "height": 1080},  # Fixed viewport like LinkedIn
                "device_scale_factor": 1,
                "is_mobile": False,
                "has_touch": False,
                "locale": 'en-US',
                "timezone_id": 'America/New_York'
            }

            # Add random user agent if enabled
            if self.config.get("use_random_user_agent", True):
                context_params["user_agent"] = random.choice(self.user_agents)
                self.logger.debug(f"Using random user agent for {email}")

            # Create context with direct parameters using main browser
            # This should only be called from main thread during preparation
            if not self.browser:
                self.logger.error("Main browser not available for context creation")
                return None

            context = self.browser.new_context(**context_params)

            # Store in shared contexts (accessible from all threads)
            self.contexts[email] = context
            
            self.logger.info(f"Browser context created for {email}")
            return context
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON from cookie file {cookie_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to create browser context for {email}: {e}")
            return None
    
    def _get_fullscreen_viewport(self) -> Dict[str, int]:
        """
        Generate full screen viewport size that matches actual screen dimensions.

        Returns:
            Dict with width and height optimized for full screen
        """
        # Use viewport sizes that better match common screen resolutions
        # These are designed to fill the browser content area completely
        viewports = [
            {"width": 1920, "height": 1080},  # Full HD (most common)
            {"width": 1920, "height": 1080},  # Full HD (weighted for common use)
            {"width": 1366, "height": 768},   # Common laptop resolution
            {"width": 1536, "height": 864},   # 1.5x scaling
            {"width": 1440, "height": 900}    # 16:10 ratio
        ]

        # For better randomization while maintaining full screen experience
        if self.config.get("randomize_viewport", True):
            return random.choice(viewports)
        else:
            # Default to Full HD for consistent experience
            return {"width": 1920, "height": 1080}
    
    def get_context(self, email: str) -> Optional[BrowserContext]:
        """
        Get browser context for specific email.
        
        Args:
            email: Email address
            
        Returns:
            BrowserContext or None if not found
        """
        return self.contexts.get(email)
    
    def create_page(self, sender_email: str) -> Optional[Page]:
        """
        Create new page in the context for specific sender email.
        Reuses the same context for all emails from the same sender to maintain session.

        Args:
            sender_email: Sender email address (used as context key for session reuse)

        Returns:
            Page or None if failed
        """
        try:
            # Use thread-local contexts and pages for complete thread isolation
            thread_contexts = self._get_thread_contexts()
            thread_pages = self._get_thread_pages()

            # Check if page already exists for this sender (for tab reuse)
            if sender_email in thread_pages:
                existing_page = thread_pages[sender_email]
                try:
                    # Test if page is still valid
                    existing_page.url
                    self.logger.info(f"🔄 Reusing existing browser tab for sender {sender_email}")
                    return existing_page
                except:
                    # Page is closed/invalid, remove it and create new one
                    del thread_pages[sender_email]
                    self.logger.debug(f"🔄 Previous tab for {sender_email} was closed, creating new one")

            # Check if context exists for this sender in current thread
            # KEY CHANGE: Use sender_email as context key to reuse sessions
            if sender_email not in thread_contexts:
                # Create context for this sender in current thread
                thread_browser = self._get_thread_browser()
                if not thread_browser:
                    self.logger.error(f"No browser available for thread {threading.current_thread().name}")
                    return None

                context = thread_browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    device_scale_factor=1,
                    is_mobile=False,
                    has_touch=False,
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                thread_contexts[sender_email] = context
                self.logger.info(f"🔄 Created new browser session for sender {sender_email} in thread {threading.current_thread().name}")
            else:
                self.logger.debug(f"🔄 Reusing existing browser session for sender {sender_email}")

            context = thread_contexts[sender_email]
            page = context.new_page()

            # Store the page for reuse
            thread_pages[sender_email] = page

            # Set page timeout
            page.set_default_timeout(self.config.get("page_load_timeout", 30) * 1000)

            # Simple approach - let the browser use its natural size (like LinkedIn automation)
            self.logger.debug(f"Page created with natural browser dimensions for {sender_email} in thread {threading.current_thread().name}")

            self.logger.debug(f"Created new page for {sender_email}")
            return page

        except Exception as e:
            self.logger.error(f"Failed to create page for {sender_email}: {e}")
            return None

    def ensure_fullwidth_content(self, page: Page) -> None:
        """
        Ensure page content uses full width after navigation.
        Call this method after navigating to any page.

        Args:
            page: Playwright page instance
        """
        try:
            # Additional CSS injection for specific sites like ProtonMail
            page.evaluate("""
                () => {
                    // Remove any max-width constraints on main containers
                    const selectors = [
                        '.main', '.container', '.content', '.wrapper',
                        '.main-area', '.sidebar + .main', '.content-container',
                        '[class*="container"]', '[class*="wrapper"]', '[class*="main"]',
                        '[class*="content"]', '[class*="layout"]'
                    ];

                    selectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            el.style.width = '100%';
                            el.style.maxWidth = 'none';
                            el.style.marginLeft = '0';
                            el.style.marginRight = '0';
                        });
                    });

                    // Force body and html to use full width
                    document.body.style.width = '100%';
                    document.body.style.maxWidth = 'none';
                    document.documentElement.style.width = '100%';
                    document.documentElement.style.maxWidth = 'none';

                    // ProtonMail specific adjustments
                    const protonSelectors = [
                        '[class*="main"]', '[class*="sidebar"]', '[class*="content"]',
                        '.main-area', '.content-area', '.app-container'
                    ];

                    protonSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            el.style.width = '100%';
                            el.style.maxWidth = 'none';
                        });
                    });
                }
            """)
            self.logger.debug("Full-width content adjustments applied")
        except Exception as e:
            self.logger.debug(f"Could not apply full-width content adjustments: {e}")
    
    def simulate_human_delay(self, min_delay: Optional[float] = None, max_delay: Optional[float] = None):
        """
        Simulate human-like delay between actions.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        if min_delay is None:
            min_delay = self.config.get("min_action_delay", 1)
        if max_delay is None:
            max_delay = self.config.get("max_action_delay", 3)
        
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        self.logger.debug(f"Human delay: {delay:.2f} seconds")
    
    def simulate_typing_delay(self) -> int:
        """
        Get random typing delay for human-like typing.
        
        Returns:
            Delay in milliseconds
        """
        min_delay = self.config.get("typing_delay_min", 50)
        max_delay = self.config.get("typing_delay_max", 150)
        return random.randint(min_delay, max_delay)
    
    def take_screenshot(self, page: Page, filename: str) -> bool:
        """
        Take screenshot for debugging purposes.
        
        Args:
            page: Page to screenshot
            filename: Filename for screenshot
            
        Returns:
            bool: True if successful
        """
        try:
            screenshot_dir = self.config.get("error_screenshot_dir", "logs/screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(screenshot_dir, f"{timestamp}_{filename}")
            
            page.screenshot(path=screenshot_path)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return False
    
    def close_context(self, sender_email: str):
        """
        Close browser context and page for specific sender email.

        Args:
            sender_email: Sender email address
        """
        try:
            # Close page first
            thread_pages = self._get_thread_pages()
            if sender_email in thread_pages:
                try:
                    thread_pages[sender_email].close()
                except:
                    pass  # Page might already be closed
                del thread_pages[sender_email]
                self.logger.debug(f"🔄 Closed browser tab for sender {sender_email}")

            # Close context in thread-local storage
            thread_contexts = self._get_thread_contexts()
            if sender_email in thread_contexts:
                thread_contexts[sender_email].close()
                del thread_contexts[sender_email]
                self.logger.info(f"🔄 Closed browser session for sender {sender_email}")
        except Exception as e:
            self.logger.error(f"Error closing context for {sender_email}: {e}")
    
    def close_all_contexts(self):
        """Close all browser contexts."""
        for email in list(self.contexts.keys()):
            self.close_context(email)
    
    def close_browser(self):
        """Close browser and stop Playwright."""
        try:
            # Close all contexts first
            self.close_all_contexts()
            
            # Close browser
            if self.browser:
                self.browser.close()
                self.browser = None
                self.logger.info("Browser closed")
            
            # Stop Playwright
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                self.logger.info("Playwright stopped")
                
        except Exception as e:
            self.logger.error(f"Error during browser cleanup: {e}")
    
    def is_browser_ready(self) -> bool:
        """
        Check if browser is ready for use.
        
        Returns:
            bool: True if browser is ready
        """
        return self.playwright is not None and self.browser is not None
