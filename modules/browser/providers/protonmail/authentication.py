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

import time
import random
from typing import Dict, Any, Optional
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

class ProtonMailAuthentication:
    """Handles ProtonMail authentication with fallback support."""
    
    def __init__(self, config: Dict[str, Any], logger, html_capture=None):
        """
        Initialize ProtonMail authentication.
        
        Args:
            config: Provider-specific configuration
            logger: Logger instance
            html_capture: HTML capture utility
        """
        self.config = config
        self.logger = logger
        self.html_capture = html_capture
        self.base_url = config.get("base_url", "https://mail.proton.me")
        self.login_url = config.get("login_url", "https://account.proton.me/login")
        
        # Multiple selector strategies for different ProtonMail interface versions
        self.login_selectors = {
            "username_field": [
                '#username',
                '[data-testid="username"]',
                'input[name="username"]',
                'input[type="email"]',
                'input[placeholder*="email"]',
                'input[placeholder*="username"]'
            ],
            "password_field": [
                '#password',
                '[data-testid="password"]',
                'input[name="password"]',
                'input[type="password"]',
                'input[placeholder*="password"]'
            ],
            "login_button": [
                'button[type="submit"]',
                '[data-testid="login-submit"]',
                'button:has-text("Sign in")',
                'button:has-text("Log in")',
                'button:has-text("Login")',
                '.login-button',
                '#login-button'
            ]
        }
        
        # Interface detection selectors
        self.interface_selectors = {
            "check_login": [
                '[data-testid="sidebar:compose"]',
                'button[title*="compose"]',
                'button[title*="Compose"]',
                '.compose-button',
                '[aria-label*="compose"]'
            ],
            "login_required": [
                '#username',
                '[data-testid="username"]',
                'input[name="username"]',
                'input[type="email"]'
            ]
        }
    
    def authenticate_with_fallback(self, page: Page, email: str, password: str = "") -> bool:
        """
        Attempt authentication with fallback from cookies to password.
        
        Args:
            page: Playwright page instance
            email: Email address for login
            password: Password for fallback authentication
            
        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Starting authentication with fallback...")
            
            # First attempt: Check if already logged in with cookies
            if self.navigate_to_mail(page):
                self.logger.info("✅ Cookie authentication successful")
                return True
            
            # Second attempt: Password-based login if cookies failed
            if password:
                self.logger.info("🔄 Cookie authentication failed, attempting password login...")
                return self.login_with_password(page, email, password)
            else:
                self.logger.error("❌ Cookie authentication failed and no password provided for fallback")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication with fallback failed: {e}")
            return False
    
    def navigate_to_mail(self, page: Page) -> bool:
        """
        Navigate to ProtonMail and verify login status.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if successfully navigated and logged in
        """
        try:
            self.logger.info("Navigating to ProtonMail...")
            page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
            
            # Capture HTML after initial navigation
            if self.html_capture:
                self.html_capture.capture_html(page, "initial_navigation", 
                                             "After navigating to ProtonMail main page")
            
            # Wait for page to load
            time.sleep(5)
            
            # Wait for page to load before checking state
            page.wait_for_load_state("load", timeout=15000)

            # Check if we're logged in by looking for compose button with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try to find compose button (indicates logged in)
                    page.wait_for_selector(self.interface_selectors["check_login"][0], timeout=15000)
                    self.logger.info("✅ Cookie authentication successful")

                    # Capture successful login state
                    if self.html_capture:
                        self.html_capture.capture_with_selectors(page, "successful_login",
                                                               {"compose_button": self.interface_selectors["check_login"][0]},
                                                               "Successfully logged in with cookies")
                    return True
                except PlaywrightTimeoutError:
                    # Check if we're on login page
                    try:
                        page.wait_for_selector(self.interface_selectors["login_required"][0], timeout=10000)
                        self.logger.warning("ProtonMail login required - cookies authentication failed")

                        # Capture failed cookie authentication
                        if self.html_capture:
                            self.html_capture.capture_with_selectors(page, "cookie_auth_failed",
                                                                   {"login_field": self.interface_selectors["login_required"][0]},
                                                                   "Cookie authentication failed - on login page")
                        return False
                    except PlaywrightTimeoutError:
                        if attempt < max_retries - 1:
                            self.logger.debug(f"Page state unclear, retrying... (attempt {attempt + 1}/{max_retries})")
                            page.wait_for_timeout(3000)  # Wait 3 seconds before retry
                            continue
                        else:
                            self.logger.error("Unknown ProtonMail page state - cannot determine login status after retries")

                            # Capture unknown state
                            if self.html_capture:
                                self.html_capture.capture_html(page, "unknown_state",
                                                             "Unknown page state after navigation")
                            return False
                    
        except Exception as e:
            self.logger.error(f"Failed to navigate to ProtonMail: {e}")
            return False
    
    def login_with_password(self, page: Page, email: str, password: str) -> bool:
        """
        Perform password-based login to ProtonMail.
        
        Args:
            page: Playwright page instance
            email: Email address
            password: Password
            
        Returns:
            bool: True if login successful
        """
        try:
            self.logger.info("Starting password-based login...")
            
            # Navigate to login page
            page.goto(self.login_url, wait_until="load", timeout=30000)

            # Wait for page to be ready (DOM loaded, not network idle)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            self.logger.debug("✅ Login page DOM loaded")

            # Additional wait for dynamic content
            time.sleep(2)
            
            # Capture login page
            if self.html_capture:
                self.html_capture.capture_html(page, "login_page_loaded", 
                                             "Login page loaded before filling credentials")
            
            # Find and fill username field
            username_field = self._find_element_by_selectors(page, self.login_selectors["username_field"])
            if not username_field:
                self.logger.error("❌ Username field not found")
                return False
            
            self.logger.debug("Filling username field...")
            username_field.click()
            time.sleep(0.5)
            # Clear field first
            username_field.fill("")
            time.sleep(0.3)
            # Type like human
            self._type_human_like(page, self.login_selectors["username_field"][0], email)
            
            # Capture after filling username
            if self.html_capture:
                self.html_capture.capture_form_state(page, "username_filled", 
                                                   {"username": self.login_selectors["username_field"][0]},
                                                   "After filling username field")
            
            time.sleep(1)
            
            # Find and fill password field
            password_field = self._find_element_by_selectors(page, self.login_selectors["password_field"])
            if not password_field:
                self.logger.error("❌ Password field not found")
                return False
            
            self.logger.debug("Filling password field...")
            password_field.click()
            time.sleep(0.5)
            # Clear field first
            password_field.fill("")
            time.sleep(0.3)
            # Type like human
            self._type_human_like(page, self.login_selectors["password_field"][0], password)
            
            # Capture after filling password
            if self.html_capture:
                self.html_capture.capture_form_state(page, "password_filled", 
                                                   {"password": self.login_selectors["password_field"][0]},
                                                   "After filling password field")
            
            time.sleep(1)
            
            # Find and click login button
            login_button = self._find_element_by_selectors(page, self.login_selectors["login_button"])
            if not login_button:
                self.logger.error("❌ Login button not found")
                return False
            
            self.logger.debug("Clicking login button...")
            # Human-like delay before clicking
            time.sleep(random.uniform(0.5, 1.2))
            login_button.click()
            # Small delay after click
            time.sleep(0.3)
            
            # Capture after clicking login
            if self.html_capture:
                self.html_capture.capture_html(page, "login_button_clicked",
                                             "After clicking login button")

            # Wait for login to complete and page to load
            try:
                page.wait_for_load_state("load", timeout=15000)
                self.logger.debug("✅ Page loaded after login")
            except Exception as e:
                self.logger.warning(f"⚠️ Page load timeout after login: {e}")
                # Continue anyway, might still work

            # Additional wait for dynamic content
            time.sleep(3)
            
            # Check if login was successful
            return self._verify_login_success(page)
                
        except Exception as e:
            self.logger.error(f"Password login failed: {e}")
            return False
    
    def _verify_login_success(self, page: Page) -> bool:
        """
        Verify if login was successful and handle apps page.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if login successful and mail interface accessible
        """
        try:
            # Wait for any redirect (could be to apps page or mail directly)
            time.sleep(3)
            current_url = page.url
            
            # Debug: Log current page state
            self.logger.info(f"🔍 POST-LOGIN DEBUG: Current URL = {current_url}")
            self.logger.info(f"🔍 POST-LOGIN DEBUG: Page title = {page.title()}")

            # CRITICAL: Wait for page to load before checking elements
            try:
                page.wait_for_load_state("load", timeout=10000)
                self.logger.info("🔍 Page loaded, checking for Mail app button...")
            except Exception as e:
                self.logger.warning(f"🔍 Page load timeout: {e}")

            # Additional wait for dynamic content
            time.sleep(2)

            # CRITICAL: Capture HTML to see what's actually on the page
            if self.html_capture:
                self.html_capture.capture_html(page, "post_login_page_state",
                                             f"Post-login page state - URL: {current_url}")

            # Check if we're on the apps selection page OR if we can find the Mail app button
            # Use explicit wait for the Mail app button
            mail_app_button = None
            try:
                page.wait_for_selector('[data-testid="explore-mail"]', timeout=10000)
                mail_app_button = page.query_selector('[data-testid="explore-mail"]')
                self.logger.info("🔍 Found Mail app button with explicit wait!")
            except Exception as e:
                self.logger.warning(f"🔍 Mail app button not found with explicit wait: {e}")
                mail_app_button = self._find_element_by_selectors(page, ['[data-testid="explore-mail"]'])

            # Debug: Check for various page indicators
            has_apps_url = "account.proton.me/apps" in current_url or "apps" in current_url
            self.logger.info(f"🔍 POST-LOGIN DEBUG: Has apps URL = {has_apps_url}")
            self.logger.info(f"🔍 POST-LOGIN DEBUG: Mail app button found = {mail_app_button is not None}")

            # Debug: Show page content structure
            try:
                all_buttons = page.query_selector_all('button, a, [role="button"]')
                self.logger.info(f"🔍 POST-LOGIN DEBUG: Found {len(all_buttons)} clickable elements on page")
                for i, btn in enumerate(all_buttons[:15]):  # Show first 15
                    try:
                        text = btn.text_content()[:50] if btn.text_content() else "No text"
                        tag = btn.tag_name
                        self.logger.info(f"🔍 Clickable {i+1}: {tag} - '{text}'")
                    except:
                        pass
            except Exception as e:
                self.logger.info(f"🔍 Error getting page elements: {e}")

            if has_apps_url or mail_app_button:
                self.logger.info("✅ Login successful - on apps page or Mail app button found")
                
                # Capture apps page for debugging
                if self.html_capture:
                    self.html_capture.capture_with_selectors(page, "apps_page_loaded", 
                                                           {
                                                               "mail_button": '[data-testid="explore-mail"]',
                                                               "mail_link_1": 'a[href*="mail.proton.me"]',
                                                               "mail_link_2": 'a:has-text("Mail")',
                                                               "mail_elements": '*:has-text("Mail")'
                                                           },
                                                           "Apps page loaded - looking for Mail app")
                
                # Look for mail app link and click it
                mail_app_selectors = [
                    '[data-testid="explore-mail"]',  # Primary selector from HTML
                    'button:has-text("Proton Mail")',
                    'a[href*="mail.proton.me"]',
                    '[data-testid="mail-app"]',
                    'a:has-text("Mail")',
                    '.app-tile:has-text("Mail")',
                    '[title*="Mail"]',
                    '[aria-label*="Mail"]',
                    'a[href*="/mail"]',
                    '.app-card:has-text("Mail")',
                    '.product-card:has-text("Mail")',
                    'button:has-text("Mail")',
                    '[data-app="mail"]'
                ]
                
                # Debug: Try each selector individually to see what's available
                self.logger.info("🔍 MAIL APP SELECTION DEBUG: Trying each selector...")
                for i, selector in enumerate(mail_app_selectors):
                    try:
                        element = page.query_selector(selector)
                        self.logger.info(f"🔍 Selector {i+1}: '{selector}' -> {'FOUND' if element else 'NOT FOUND'}")
                        if element:
                            self.logger.info(f"🔍 Element text: '{element.text_content()}'")
                    except Exception as e:
                        self.logger.info(f"🔍 Selector {i+1}: '{selector}' -> ERROR: {e}")

                mail_link = self._find_element_by_selectors(page, mail_app_selectors)
                if mail_link:
                    self.logger.info("✅ Clicking Mail app to access mail interface")
                    mail_link.click()

                    # Wait directly for compose button to appear (no manual delays!)
                    self.logger.info("🔍 Waiting for mail interface to load and compose button to appear...")
                    try:
                        page.wait_for_selector(self.interface_selectors["check_login"][0], timeout=45000)
                        self.logger.info("✅ Mail interface fully loaded - compose button found!")
                        return True
                    except Exception as e:
                        self.logger.error(f"❌ Mail interface failed to load - compose button not found after 45s: {e}")
                        # Continue to fallback logic below
                else:
                    self.logger.warning("❌ No Mail app button found with standard selectors")

                    # CRITICAL: Capture HTML when mail selection fails
                    if self.html_capture:
                        self.html_capture.capture_html(page, "mail_selection_failed",
                                                     "Failed to find Mail app button - capturing page state")

                    # Debug: Show all clickable elements on the page
                    self.logger.info("🔍 DEBUGGING: All clickable elements on page:")
                    try:
                        clickable_elements = page.query_selector_all('a, button, [role="button"], [onclick], div[onclick], span[onclick]')
                        self.logger.info(f"🔍 Total clickable elements found: {len(clickable_elements)}")
                        for i, element in enumerate(clickable_elements[:20]):  # Show first 20
                            try:
                                text = element.text_content()[:80] if element.text_content() else "No text"
                                tag = element.tag_name
                                classes = element.get_attribute('class') or "No class"
                                data_testid = element.get_attribute('data-testid') or "No testid"
                                href = element.get_attribute('href') or "No href"
                                self.logger.info(f"🔍 Clickable {i+1}: {tag} class='{classes[:30]}' testid='{data_testid}' href='{href[:30]}' text='{text}'")
                            except Exception as e:
                                self.logger.info(f"🔍 Error processing element {i+1}: {e}")
                    except Exception as e:
                        self.logger.info(f"🔍 Error getting clickable elements: {e}")

                    # Try finding any clickable element with "Mail" text
                    self.logger.info("🔍 Trying alternative Mail app detection...")
                    try:
                        # Look for any element containing "Mail" that might be clickable
                        mail_elements = page.query_selector_all('*:has-text("Mail")')
                        self.logger.info(f"🔍 Found {len(mail_elements)} elements containing 'Mail'")
                        for i, element in enumerate(mail_elements[:10]):  # Show first 10
                            try:
                                text = element.text_content()[:50] if element.text_content() else "No text"
                                tag = element.tag_name
                                classes = element.get_attribute('class') or "No class"
                                self.logger.info(f"🔍 Mail element {i+1}: {tag} class='{classes[:30]}' text='{text}'")
                            except:
                                pass

                        for element in mail_elements:
                            try:
                                # Check if element is clickable (has href, onclick, or is button/a tag)
                                tag_name = element.evaluate("el => el.tagName.toLowerCase()")
                                href = element.get_attribute("href")
                                onclick = element.get_attribute("onclick")
                                
                                if (tag_name in ["a", "button"] or href or onclick) and element.is_visible():
                                    self.logger.info(f"Found clickable Mail element: {tag_name}")
                                    element.click()
                                    time.sleep(3)
                                    break
                            except Exception:
                                continue
                        else:
                            # If no clickable Mail element found, try navigating directly
                            self.logger.info("No clickable Mail element found, navigating directly to mail")
                            page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                            time.sleep(3)
                    except Exception as e:
                        self.logger.warning(f"Error in alternative Mail detection: {e}")
                        # Fallback to direct navigation
                        self.logger.info("Falling back to direct navigation to mail")
                        page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                        time.sleep(3)
            
            # If we reach here, the mail app click didn't work, try direct compose button check
            try:
                self.logger.info("🔍 Mail app click may have failed, checking for compose button directly...")
                page.wait_for_selector(self.interface_selectors["check_login"][0], timeout=15000)
                self.logger.info("✅ Password login successful - compose button found directly")
                
                # Capture successful login
                if self.html_capture:
                    self.html_capture.capture_with_selectors(page, "password_login_success", 
                                                           {"compose_button": self.interface_selectors["check_login"][0]},
                                                           "Password login successful")
                return True
                
            except PlaywrightTimeoutError:
                self.logger.error("❌ Password login failed - compose button not found in mail interface")
                
                # Capture failed login
                if self.html_capture:
                    self.html_capture.capture_html(page, "password_login_failed", 
                                                 "Password login failed - compose button not found")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Error during login verification: {e}")
            
            # Capture error state
            if self.html_capture:
                self.html_capture.capture_html(page, "login_verification_error", 
                                             f"Error during login verification: {str(e)}")
            return False
    
    def _find_element_by_selectors(self, page: Page, selectors: list):
        """
        Find element using multiple selector strategies.
        
        Args:
            page: Playwright page instance
            selectors: List of CSS selectors to try
            
        Returns:
            Element if found, None otherwise
        """
        for selector in selectors:
            try:
                element = page.query_selector(selector)
                if element and element.is_visible():
                    self.logger.debug(f"Found element with selector: {selector}")
                    return element
            except Exception:
                continue
        
        self.logger.warning(f"Element not found with any of the selectors: {selectors}")
        return None
    
    def _type_human_like(self, page: Page, selector: str, text: str):
        """
        Type text with human-like delays and patterns.
        
        Args:
            page: Playwright page instance
            selector: CSS selector for input field
            text: Text to type
        """
        try:
            # Focus on the field
            element = page.locator(selector)
            element.click()
            time.sleep(0.2)
            
            # Clear field first
            element.fill("")
            time.sleep(0.1)
            
            # Type character by character with random delays
            for i, char in enumerate(text):
                page.keyboard.type(char)
                
                # Random delay between keystrokes (80-200ms)
                delay = random.randint(80, 200) / 1000
                time.sleep(delay)
                
                # Occasionally pause longer (simulate thinking/hesitation)
                if random.random() < 0.08:  # 8% chance
                    time.sleep(random.uniform(0.3, 0.8))
                
                # Slight pause after every few characters
                if i > 0 and i % random.randint(3, 7) == 0:
                    time.sleep(random.uniform(0.1, 0.3))
                    
        except Exception as e:
            self.logger.error(f"Error during human-like typing: {e}")
            # Fallback to regular fill
            try:
                page.locator(selector).fill(text)
            except:
                # Last resort - try direct element interaction
                element = self._find_element_by_selectors(page, [selector])
                if element:
                    element.fill(text)
