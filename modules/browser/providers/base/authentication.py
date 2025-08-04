# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Base authentication class for email providers to eliminate code duplication
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
from ...file_captcha_manager import get_file_captcha_manager

class BaseAuthentication:
    """Base class for email provider authentication with common functionality."""
    
    def __init__(self, config: Dict[str, Any], logger, html_capture=None):
        """
        Initialize base authentication.
        
        Args:
            config: Provider-specific configuration
            logger: Logger instance
            html_capture: HTML capture utility
        """
        self.config = config
        self.logger = logger
        self.html_capture = html_capture
    
    def _find_element_by_selectors(self, page: Page, selectors: list, timeout: int = 5000) -> Optional[Any]:
        """
        Find element using multiple selectors with timeout.
        
        Args:
            page: Playwright page instance
            selectors: List of CSS selectors to try
            timeout: Timeout in milliseconds
            
        Returns:
            Element if found, None otherwise
        """
        for selector in selectors:
            try:
                element = page.wait_for_selector(selector, timeout=timeout)
                if element and element.is_visible():
                    self.logger.debug(f"✅ Found element with selector: {selector}")
                    return element
            except PlaywrightTimeoutError:
                self.logger.debug(f"⏰ Timeout waiting for selector: {selector}")
                continue
            except Exception as e:
                self.logger.debug(f"❌ Error with selector {selector}: {e}")
                continue
        
        self.logger.debug(f"❌ No element found with any of {len(selectors)} selectors")
        return None
    
    def _handle_verification_prompts(self, page: Page, email: str) -> None:
        """
        Handle CAPTCHA/verification prompts that require manual intervention.
        
        Args:
            page: Playwright page instance
            email: Email address for context
        """
        try:
            verification_found = False
            found_selector = None
            
            # Check URL for verification indicators
            current_url = page.url.lower()
            
            # Skip device verification pages - these should be handled automatically
            if "device-verification" in current_url:
                self.logger.debug("🔐 Device verification page detected - will be handled automatically")
                return
            
            url_verification_indicators = [
                'recaptcha', 'captcha', 'security', 'robot', 'suspicious'
            ]
            
            # Only check for 'challenge' if it's not device verification
            if 'challenge' in current_url and 'device' not in current_url:
                url_verification_indicators.append('challenge')

            for indicator in url_verification_indicators:
                if indicator in current_url:
                    verification_found = True
                    found_selector = f"URL contains '{indicator}'"
                    break
            
            # Check for verification elements on page
            if not verification_found:
                verification_selectors = [
                    'iframe[src*="recaptcha"]',
                    '.recaptcha-checkbox',
                    '#recaptcha',
                    '[data-sitekey]',
                    '.captcha',
                    '.verification',
                    'input[name="captcha"]'
                ]
                
                for selector in verification_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            verification_found = True
                            found_selector = selector
                            break
                    except Exception:
                        continue
            
            if verification_found:
                # Capture verification state
                if self.html_capture:
                    self.html_capture.capture_html(page, f"{self._get_provider_name()}_verification_prompt",
                                                 f"{self._get_provider_name()} verification prompt detected")

                # Get browser information
                try:
                    current_title = page.title()
                    current_url = page.url
                except Exception:
                    current_title = "Unknown"
                    current_url = page.url if page else "Unknown"

                # Use file-based CAPTCHA manager
                captcha_manager = get_file_captcha_manager(self.logger)
                success = captcha_manager.request_captcha_verification(
                    email=email,
                    provider=self._get_provider_name(),
                    browser_title=current_title,
                    browser_url=current_url,
                    detection_method=found_selector
                )

                if success:
                    self.logger.info(f"✅ CAPTCHA verification completed for {email}")

                    # Capture post-verification state
                    if self.html_capture:
                        self.html_capture.capture_html(page, f"{self._get_provider_name()}_after_verification",
                                                     f"{self._get_provider_name()} after verification completion")
                else:
                    self.logger.error(f"❌ CAPTCHA verification failed for {email}")
                
        except Exception as e:
            self.logger.debug(f"Verification prompt check failed: {e}")
    
    def _check_rate_limiting(self, page: Page) -> bool:
        """
        Check for rate limiting indicators.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if rate limiting detected
        """
        try:
            # Common rate limiting indicators
            rate_limit_indicators = [
                'temporarily unavailable',
                'too many attempts',
                'rate limit',
                'try again later',
                'suspicious activity',
                'unusual activity'
            ]
            
            page_content = page.content().lower()
            
            for indicator in rate_limit_indicators:
                if indicator in page_content:
                    self.logger.warning(f"🚫 Rate limiting detected: '{indicator}'")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Rate limiting check failed: {e}")
            return False
    
    def _get_provider_name(self) -> str:
        """Get the provider name for logging/capture purposes."""
        return self.__class__.__name__.replace('Authentication', '').lower()
    
    def _wait_with_random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """
        Wait with randomized delay to appear more human-like.
        
        Args:
            min_seconds: Minimum wait time
            max_seconds: Maximum wait time
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def _type_with_human_delay(self, element, text: str, min_delay: int = 50, max_delay: int = 150):
        """
        Type text with human-like delays between characters.
        
        Args:
            element: Playwright element to type into
            text: Text to type
            min_delay: Minimum delay between characters (ms)
            max_delay: Maximum delay between characters (ms)
        """
        element.type(text, delay=random.randint(min_delay, max_delay))
    
    def _capture_html_state(self, page: Page, step_name: str, description: str = ""):
        """
        Capture HTML state for debugging.
        
        Args:
            page: Playwright page instance
            step_name: Name of the step for file naming
            description: Description of what's being captured
        """
        if self.html_capture:
            self.html_capture.capture_html(page, f"{self._get_provider_name()}_{step_name}", description)
