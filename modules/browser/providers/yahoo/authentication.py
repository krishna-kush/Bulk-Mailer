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
# Components: - Multi-Provider SMTP Management (Gmail, Outlook, fYahoo, Custom)
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
from ..base.authentication import BaseAuthentication

class YahooAuthentication(BaseAuthentication):
    """Handles Yahoo Mail authentication with fallback support."""
    
    def __init__(self, config: Dict[str, Any], logger, html_capture=None):
        """
        Initialize Yahoo Mail authentication.

        Args:
            config: Browser automation configuration
            logger: Logger instance
            html_capture: HTML capture utility for debugging
        """
        super().__init__(config, logger, html_capture)
        
        # Yahoo Mail URLs
        self.login_url = "https://login.yahoo.com"
        self.mail_url = "https://mail.yahoo.com"
        
        # Authentication selectors
        self.auth_selectors = {
            "email_field": [
                'input[name="username"]',
                'input[id="login-username"]',
                '#username',
                'input[type="email"]',
                'input[placeholder*="email"]',
                'input[placeholder*="username"]'
            ],
            "password_field": [
                'input[name="password"]',
                'input[id="login-passwd"]',
                '#passwd',
                'input[type="password"]',
                'input[placeholder*="password"]'
            ],
            "next_button": [
                'input[id="login-signin"]',
                'button[id="login-signin"]',
                'input[name="signin"]',
                'button[name="signin"]',
                'input[value="Next"]',
                'button:has-text("Next")',
                'input[type="submit"]'
            ],
            "sign_in_button": [
                'input[id="login-signin"]',
                'button[id="login-signin"]',
                'input[name="signin"]',
                'button[name="signin"]',
                'input[value="Sign in"]',
                'button:has-text("Sign in")',
                'input[type="submit"]'
            ]
        }
        
        # Interface check selectors (to verify successful login)
        self.interface_selectors = {
            "check_login": [
                # Modern Yahoo Mail compose button selectors
                'button[data-test-id="compose-button"]',
                'a[data-test-id="compose-button"]',
                'button:has-text("Compose")',
                'a:has-text("Compose")',
                '[aria-label*="Compose"]',
                '[aria-label*="compose"]',
                '.compose-button',
                '#compose-button',
                'button[title*="Compose"]',

                # Alternative Mail interface indicators
                '[data-test-id="folder-tree"]',
                '[data-test-id="message-list"]',
                '.message-list',
                '.folder-tree',
                '#mail-app-component',
                '[data-test-id*="mail"]',

                # Yahoo Mail specific containers (only exist on Mail interface)
                '.mail-app',
                '#mail-app',
                '.ymail-app',

                # Inbox indicators (specific to Mail interface)
                ':has-text("Inbox")',
                '[data-test-id*="inbox"]',
                '.inbox',

                # Mail-specific navigation
                '.mail-nav',
                '.mail-sidebar',
                '.message-list-container'
            ]
        }
    

    
    def authenticate(self, page: Page, email: str, password: str) -> bool:
        """
        Authenticate with Yahoo Mail using fallback methods.

        Args:
            page: Playwright page instance
            email: Email address
            password: Password

        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Starting Yahoo Mail authentication with fallback...")

            # Try cookie authentication first
            if self._try_cookie_authentication(page):
                return True

            # Fallback to password authentication
            self.logger.info("🔄 Cookie authentication failed, attempting password login...")

            # Check for "too many attempts" and clear browser data if needed
            if self._check_and_handle_rate_limiting(page, email):
                self.logger.info("🔄 Cleared browser data due to rate limiting, retrying with fresh context...")
                # Return True to indicate we should retry with a fresh context
                return "RETRY_FRESH_CONTEXT"

            return self._password_authentication(page, email, password)

        except Exception as e:
            self.logger.error(f"Yahoo Mail authentication failed: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_auth_failed", f"Authentication failed: {e}")
            return False
    
    def _try_cookie_authentication(self, page: Page) -> bool:
        """
        Try to authenticate using existing cookies.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if cookie authentication successful
        """
        try:
            self.logger.info("Navigating to Yahoo Mail...")
            page.goto(self.mail_url, wait_until="load", timeout=30000)
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_cookie_attempt", "Yahoo Mail cookie authentication attempt")
            
            # Check if we're already logged in
            try:
                page.wait_for_selector(self.interface_selectors["check_login"][0], timeout=10000)
                self.logger.info("✅ Cookie authentication successful - already logged in")
                return True
            except PlaywrightTimeoutError:
                self.logger.warning("Yahoo Mail login required - cookies authentication failed")
                return False
                
        except Exception as e:
            self.logger.warning(f"Cookie authentication failed: {e}")
            return False
    
    def _password_authentication(self, page: Page, email: str, password: str) -> bool:
        """
        Authenticate using email and password.
        
        Args:
            page: Playwright page instance
            email: Email address
            password: Password
            
        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Starting password-based login...")
            
            # Navigate to login page
            page.goto(self.login_url, wait_until="load", timeout=30000)
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_login_page", "Yahoo Mail login page loaded")
            
            # Fill email field
            email_field = self._find_element_by_selectors(page, self.auth_selectors["email_field"], 10000)
            if not email_field:
                self.logger.error("❌ Email field not found")
                return False
            
            self.logger.info("✅ Found email field, filling email...")
            email_field.click()
            email_field.fill("")  # Clear the field
            email_field.type(email, delay=random.randint(50, 150))
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_email_filled", "Yahoo Mail email field filled")
            
            # Click Next button (Yahoo has two-step login)
            next_button = self._find_element_by_selectors(page, self.auth_selectors["next_button"], 5000)
            if next_button:
                self.logger.info("✅ Found Next button, clicking...")
                next_button.click()
                time.sleep(1)  # Reduced from 3s to 1s

                if self.html_capture:
                    self.html_capture.capture_html(page, "yahoo_after_next", "Yahoo Mail after clicking Next")

                # Check for verification prompts after clicking Next
                self._handle_verification_prompts(page, email)
            
            # Fill password field
            password_field = self._find_element_by_selectors(page, self.auth_selectors["password_field"], 10000)
            if not password_field:
                self.logger.error("❌ Password field not found")

                # Check if this is due to verification failure or rate limiting
                if self._check_verification_failure(page):
                    self.logger.error("❌ Authentication failed due to verification failure - requesting fresh context")
                    return "RETRY_FRESH_CONTEXT"
                elif self._check_and_handle_rate_limiting(page, email):
                    self.logger.error("❌ Authentication failed due to rate limiting - requesting fresh context")
                    return "RETRY_FRESH_CONTEXT"

                return False
            
            self.logger.info("✅ Found password field, filling password...")
            password_field.click()
            password_field.fill("")  # Clear the field
            password_field.type(password, delay=random.randint(50, 150))
            
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_password_filled", "Yahoo Mail password field filled")
            
            # Click Sign In button
            sign_in_button = self._find_element_by_selectors(page, self.auth_selectors["sign_in_button"], 5000)
            if not sign_in_button:
                self.logger.error("❌ Sign In button not found")
                return False

            self.logger.info("✅ Found Sign In button, clicking...")
            sign_in_button.click()

            # Wait for login to complete
            time.sleep(2)  # Reduced from 5s to 2s

            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_after_signin", "Yahoo Mail after clicking Sign In")

            # Check for CAPTCHA or verification prompts
            self._handle_verification_prompts(page, email)
            
            # Handle post-authentication navigation
            return self._handle_post_authentication_navigation(page, email)
                
        except Exception as e:
            self.logger.error(f"Password authentication failed: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_password_auth_error", f"Password auth error: {e}")
            return False
    


    def _check_and_handle_rate_limiting(self, page: Page, email: str = "Unknown") -> bool:
        """
        Check for rate limiting messages and clear browser data if needed.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if rate limiting was detected and handled
        """
        try:
            # Check page content for rate limiting indicators
            page_content = page.content().lower()
            page_url = page.url.lower()

            rate_limit_indicators = [
                'too many attempts',
                'too many tries',
                'account temporarily locked',
                'temporarily unavailable',
                'try again later',
                'suspicious activity',
                'unusual activity detected',
                'account access limited',
                'security measures',
                'blocked for security'
            ]

            rate_limited = False
            for indicator in rate_limit_indicators:
                if indicator in page_content or indicator in page_url:
                    rate_limited = True
                    self.logger.warning(f"🚫 Rate limiting detected: '{indicator}'")
                    break

            if rate_limited:
                self.logger.warning(f"🚫 Rate limiting detected for {email}")
                self.logger.info("🧹 Clearing browser context completely to reset rate limiting...")

                if self.html_capture:
                    self.html_capture.capture_html(page, "yahoo_rate_limited", f"Yahoo Mail rate limiting detected for {email}")

                # Clear all browser data
                context = page.context
                context.clear_cookies()
                context.clear_permissions()

                # Clear local storage and session storage
                try:
                    page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
                except Exception as e:
                    self.logger.debug(f"Failed to clear storage: {e}")

                # Navigate to a clean page
                try:
                    page.goto("about:blank")
                    time.sleep(2)
                except Exception as e:
                    self.logger.debug(f"Failed to navigate to blank page: {e}")

                self.logger.warning("⚠️  Browser context needs to be recreated due to rate limiting")
                self.logger.warning("🔄 The system will close this context and create a fresh one")

                return True

            return False

        except Exception as e:
            self.logger.debug(f"Rate limiting check failed: {e}")
            return False

    def _check_verification_failure(self, page: Page) -> bool:
        """
        Check if verification failed or if more verification attempts are needed.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if verification failed
        """
        try:
            page_content = page.content().lower()
            page_url = page.url.lower()

            verification_failure_indicators = [
                'too many verification attempts',
                'verification failed',
                'incorrect verification',
                'verification unsuccessful',
                'try again',
                'verification limit exceeded',
                'maximum attempts reached',
                'account temporarily locked',
                'suspicious activity',
                'unusual activity detected',
                'security check failed',
                'please try again later',
                'verification code expired',
                'invalid verification'
            ]

            for indicator in verification_failure_indicators:
                if indicator in page_content or indicator in page_url:
                    self.logger.warning(f"🚫 Verification failure detected: '{indicator}'")

                    if self.html_capture:
                        self.html_capture.capture_html(page, "yahoo_verification_failed",
                                                     f"Yahoo Mail verification failed - {indicator}")
                    return True

            return False

        except Exception as e:
            self.logger.debug(f"Verification failure check failed: {e}")
            return False

    def _handle_post_authentication_navigation(self, page: Page, email: str) -> bool:
        """
        Handle navigation after password authentication.
        Smartly navigates through device verification and homepage to reach Mail.

        Args:
            page: Playwright page instance
            email: Email address for logging

        Returns:
            bool: True if successfully reached Mail interface
        """
        try:
            # Wait a moment for page to load after password submission
            time.sleep(3)

            # Check current page state and navigate accordingly
            current_url = page.url.lower()
            self.logger.info(f"🔍 Post-authentication URL: {current_url}")

            # Check if we're already on Mail interface (best case)
            if self._check_if_on_mail_interface(page):
                self.logger.info("✅ Already on Mail interface - no navigation needed!")
                return True

            # Check if we're on device verification page
            if "device-verification" in current_url or "challenge" in current_url:
                self.logger.info("🔐 On device verification page - clicking Next...")
                if not self._handle_device_verification(page):
                    return False

                # After device verification, wait and check what page we're on
                time.sleep(2)  # Reduced from 5s to 2s
                current_url = page.url.lower()
                self.logger.info(f"🔍 After device verification URL: {current_url}")

                if self._check_if_on_mail_interface(page):
                    self.logger.info("✅ Reached Mail interface after device verification!")
                    return True
                else:
                    self.logger.info("📄 Not on Mail interface yet, continuing navigation...")
                    # Force check if we're on homepage and navigate to Mail
                    if "yahoo.com" in current_url and "mail" not in current_url:
                        self.logger.info("🏠 Detected Yahoo homepage after device verification - navigating to Mail...")
                        return self._navigate_to_mail_from_homepage(page)

            # Check if we're on Yahoo homepage - navigate directly to Mail
            if self._check_if_on_homepage(page):
                self.logger.info("🏠 On Yahoo homepage - navigating directly to Mail...")
                try:
                    page.goto("https://mail.yahoo.com/", wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)  # Reduced from 5s to 2s

                    if self._check_if_on_mail_interface(page):
                        self.logger.info("✅ Reached Mail interface via direct navigation!")
                        return True
                    else:
                        self.logger.warning("⚠️  Direct navigation to Mail failed")
                except Exception as e:
                    self.logger.error(f"Direct navigation to Mail failed: {e}")
                    return False

            # Final attempt: wait for Mail interface to appear
            self.logger.info("🔍 Waiting for Mail interface to load...")

            # Try each selector with increased timeout
            for selector in self.interface_selectors["check_login"]:
                try:
                    self.logger.debug(f"Trying to find Mail interface with selector: {selector}")
                    element = page.wait_for_selector(selector, timeout=10000)
                    if element:
                        self.logger.info(f"✅ Mail interface loaded successfully! Found: {selector}")
                        return True
                except PlaywrightTimeoutError:
                    continue
                except Exception as e:
                    self.logger.debug(f"Error with selector {selector}: {e}")
                    continue

            # If we get here, none of the selectors worked - try direct navigation to Mail
            self.logger.warning("⚠️  Mail interface not detected, trying direct navigation to mail.yahoo.com...")

            try:
                # Capture current state for debugging
                current_url = page.url
                current_title = page.title()
                self.logger.info(f"Current page before direct navigation: Title='{current_title}', URL={current_url}")

                # Navigate directly to Yahoo Mail
                self.logger.info("🔗 Navigating directly to https://mail.yahoo.com/")
                page.goto("https://mail.yahoo.com/", wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)

                # Check if we're now on Mail interface
                if self._check_if_on_mail_interface(page):
                    self.logger.info("✅ Successfully reached Mail interface via direct navigation!")
                    return True
                else:
                    self.logger.error("❌ Direct navigation to Mail also failed")

            except Exception as e:
                self.logger.error(f"Direct navigation to Mail failed: {e}")

            # Final failure
            self.logger.error("❌ All attempts to reach Mail interface failed")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_navigation_failed",
                                             f"Failed to reach Mail interface for {email}")
            return False

        except Exception as e:
            self.logger.error(f"Post-authentication navigation failed: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_navigation_error", f"Navigation error: {e}")
            return False

    def _check_if_on_mail_interface(self, page: Page) -> bool:
        """Check if currently on Yahoo Mail interface."""
        try:
            # First check URL - most reliable indicator
            current_url = page.url.lower()

            # STRICT CHECK: Only consider it Mail interface if URL contains mail.yahoo.com
            if "mail.yahoo.com" in current_url:
                self.logger.info(f"✅ On Mail interface by URL: {current_url}")
                return True

            # If not on mail.yahoo.com, we're NOT on Mail interface regardless of elements
            if "yahoo.com" in current_url and "mail" not in current_url:
                self.logger.info(f"❌ Not on Mail interface - on Yahoo homepage: {current_url}")
                return False

            # For other URLs, check for Mail interface elements (but be strict)
            self.logger.debug("🔍 Checking for Mail interface elements...")

            # Only check compose button and very specific Mail elements
            mail_specific_selectors = [
                'button[data-test-id="compose-button"]',
                'a[data-test-id="compose-button"]',
                'button:has-text("Compose")',
                'a:has-text("Compose")',
                '[data-test-id="folder-tree"]',
                '[data-test-id="message-list"]'
            ]

            for selector in mail_specific_selectors:
                try:
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        self.logger.info(f"✅ Found Mail interface element: {selector}")
                        return True
                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue

            self.logger.debug("❌ No Mail interface elements found")
            return False
        except Exception as e:
            self.logger.debug(f"Error in Mail interface detection: {e}")
            return False

    def _check_if_on_homepage(self, page: Page) -> bool:
        """Check if currently on Yahoo homepage."""
        try:
            current_url = page.url.lower()

            # First check URL - most reliable indicator
            if "mail.yahoo.com" in current_url:
                # Already on Mail page
                return False

            if "yahoo.com" in current_url and "mail" not in current_url:
                self.logger.info(f"🏠 Detected Yahoo homepage: {current_url}")
                return True

            # If URL check is inconclusive, check page title
            try:
                page_title = page.title().lower()

                # Check title indicators
                homepage_indicators = [
                    "weather, search, politics" in page_title,
                    "yahoo | mail, weather" in page_title,
                    "yahoo.com" in page_title and "mail" not in page_title
                ]

                if any(homepage_indicators):
                    self.logger.info(f"🏠 Detected Yahoo homepage by title: {page_title}")
                    return True
            except Exception as e:
                self.logger.debug(f"Error getting page title: {e}")

            # Final check - look for Mail link which only exists on homepage
            try:
                mail_link = page.query_selector('a[href="https://mail.yahoo.com/"]')
                if mail_link:
                    self.logger.info("🏠 Detected Yahoo homepage by Mail link presence")
                    return True
            except Exception:
                pass

            return False
        except Exception as e:
            self.logger.debug(f"Error in homepage detection: {e}")
            return False

    def _handle_device_verification(self, page: Page) -> bool:
        """Handle device verification step."""
        try:
            # Look for device verification Next button
            device_selectors = [
                'button[id="device-finger-print-challenge-submit-button"]',
                'button:has-text("Next")',
                'button[type="submit"]',
                'input[value="Next"]'
            ]

            next_button = self._find_element_by_selectors(page, device_selectors, 10000)
            if not next_button:
                self.logger.warning("⚠️  Device verification Next button not found")
                return False

            self.logger.info("✅ Found device verification Next button, clicking...")
            next_button.click()

            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_device_verification_clicked",
                                             "Yahoo Mail device verification Next clicked")

            # Wait for navigation
            time.sleep(5)
            return True

        except Exception as e:
            self.logger.error(f"Device verification failed: {e}")
            return False

    def _navigate_to_mail_from_homepage(self, page: Page) -> bool:
        """Navigate to Mail from Yahoo homepage."""
        try:
            # Look for Mail link
            mail_selectors = [
                'a[href="https://mail.yahoo.com/"]',
                'a[data-ylk*="mail.yahoo.com"]',
                'a:has-text("Mail")',
                '[aria-label*="Check your mail"]',
                '#ybarMailLink'
            ]

            mail_link = self._find_element_by_selectors(page, mail_selectors, 10000)
            if not mail_link:
                self.logger.warning("⚠️  Mail link not found on homepage")
                return False

            self.logger.info("✅ Found Mail link, clicking...")

            # Get current number of pages before clicking
            context = page.context
            initial_pages = len(context.pages)

            # Remove target="_blank" attribute to force same-tab opening
            try:
                page.evaluate('(element) => element.removeAttribute("target")', mail_link)
                self.logger.debug("🔧 Removed target='_blank' from Mail link")
            except Exception as e:
                self.logger.debug(f"Could not remove target attribute: {e}")

            # Click the Mail link (should now open in same tab)
            mail_link.click()

            if self.html_capture:
                self.html_capture.capture_html(page, "yahoo_mail_link_clicked",
                                             "Yahoo Mail link clicked from homepage")

            # Wait for Mail page to load (should be in same tab now)
            self.logger.info("⏳ Waiting for Mail page to load...")
            time.sleep(5)

            # Check if URL changed to Mail
            try:
                current_url = page.url.lower()
                if "mail.yahoo.com" in current_url:
                    self.logger.info(f"✅ Successfully navigated to Mail: {current_url}")
                    return True
                else:
                    self.logger.warning(f"⚠️  Still not on Mail page: {current_url}")

                    # Check if new tab opened despite our efforts
                    current_pages = len(context.pages)
                    if current_pages > initial_pages:
                        self.logger.info("📑 Mail opened in new tab despite removing target attribute")
                        # Find and switch to Mail tab
                        for new_page in context.pages:
                            try:
                                if "mail.yahoo.com" in new_page.url.lower():
                                    self.logger.info(f"✅ Found Mail tab: {new_page.url}")
                                    # Navigate current page to Mail URL instead of switching tabs
                                    page.goto(new_page.url, wait_until="domcontentloaded")
                                    time.sleep(3)
                                    # Close the extra tab
                                    new_page.close()
                                    self.logger.info("✅ Navigated to Mail and closed extra tab")
                                    return True
                            except Exception as e:
                                self.logger.debug(f"Error handling new tab: {e}")
                                continue

                    return False
            except Exception as e:
                self.logger.error(f"Error checking Mail navigation: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Navigation to Mail from homepage failed: {e}")
            return False

    def is_authenticated(self, page: Page) -> bool:
        """
        Check if currently authenticated with Yahoo Mail.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if authenticated
        """
        try:
            # Check for compose button presence
            compose_button = self._find_element_by_selectors(page, self.interface_selectors["check_login"], 3000)
            return compose_button is not None
        except Exception:
            return False
