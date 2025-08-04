# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Base email composer class for email providers to eliminate code duplication
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

class BaseEmailComposer:
    """Base class for email composition with common functionality."""
    
    def __init__(self, config: Dict[str, Any], logger, html_capture=None):
        """
        Initialize base email composer.
        
        Args:
            config: Provider-specific configuration
            logger: Logger instance
            html_capture: HTML capture utility
        """
        self.config = config
        self.logger = logger
        self.html_capture = html_capture
        
        # REDUCED DELAYS for faster email composition (addressing user feedback)
        self.delays = {
            'compose_click': (0.3, 0.8),      # Reduced from ~1 minute to <1 second
            'field_fill': (0.1, 0.4),        # Very short delays
            'between_fields': (0.2, 0.6),    # Quick transitions
            'send_click': (0.3, 0.7),        # Quick send
            'post_send': (1.0, 2.0)          # Minimal wait after sending
        }
    
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
    
    def _wait_with_random_delay(self, delay_type: str = 'between_fields'):
        """
        Wait with randomized delay based on delay type.
        
        Args:
            delay_type: Type of delay from self.delays
        """
        if delay_type in self.delays:
            min_delay, max_delay = self.delays[delay_type]
            delay = random.uniform(min_delay, max_delay)
            time.sleep(delay)
        else:
            time.sleep(random.uniform(0.2, 0.8))  # Default short delay
    
    def _type_with_human_delay(self, element, text: str, min_delay: int = 20, max_delay: int = 50):
        """
        Type text with human-like delays between characters (REDUCED delays).
        
        Args:
            element: Playwright element to type into
            text: Text to type
            min_delay: Minimum delay between characters (ms) - much reduced
            max_delay: Maximum delay between characters (ms) - much reduced
        """
        element.type(text, delay=random.randint(min_delay, max_delay))
    
    def _fill_field_with_validation(self, page: Page, selectors: list, value: str, 
                                   field_name: str, clear_first: bool = True) -> bool:
        """
        Fill a form field with validation and error handling.
        
        Args:
            page: Playwright page instance
            selectors: List of selectors to try for the field
            value: Value to fill
            field_name: Name of field for logging
            clear_first: Whether to clear field before filling
            
        Returns:
            bool: True if successful
        """
        try:
            field = self._find_element_by_selectors(page, selectors, 10000)
            if not field:
                self.logger.error(f"❌ {field_name} field not found")
                return False
            
            self.logger.info(f"✅ Found {field_name} field, filling...")
            
            # Click to focus
            field.click()
            self._wait_with_random_delay('field_fill')
            
            # Clear if requested
            if clear_first:
                field.fill("")
                
            # Type with human-like delay
            self._type_with_human_delay(field, value)
            
            # Capture state
            self._capture_html_state(page, f"{field_name.lower()}_filled", 
                                   f"{field_name} field filled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill {field_name} field: {e}")
            return False
    
    def _click_element_with_retry(self, page: Page, selectors: list, element_name: str, 
                                 max_retries: int = 3) -> bool:
        """
        Click an element with retry logic.
        
        Args:
            page: Playwright page instance
            selectors: List of selectors to try
            element_name: Name of element for logging
            max_retries: Maximum number of retry attempts
            
        Returns:
            bool: True if successful
        """
        for attempt in range(max_retries):
            try:
                element = self._find_element_by_selectors(page, selectors, 10000)
                if not element:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"⚠️  {element_name} not found, retrying... (attempt {attempt + 1})")
                        time.sleep(1)  # Short retry delay
                        continue
                    else:
                        self.logger.error(f"❌ {element_name} not found after {max_retries} attempts")
                        return False
                
                self.logger.info(f"✅ Found {element_name}, clicking...")
                element.click()
                
                # Capture state
                self._capture_html_state(page, f"{element_name.lower().replace(' ', '_')}_clicked", 
                                       f"{element_name} clicked")
                
                return True
                
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"⚠️  Failed to click {element_name}, retrying... (attempt {attempt + 1}): {e}")
                    time.sleep(1)  # Short retry delay
                else:
                    self.logger.error(f"❌ Failed to click {element_name} after {max_retries} attempts: {e}")
                    return False
        
        return False
    
    def _wait_for_success_indicator(self, page: Page, success_selectors: list, 
                                   timeout: int = 15000) -> bool:
        """
        Wait for email send success indicators.
        
        Args:
            page: Playwright page instance
            success_selectors: List of selectors that indicate success
            timeout: Timeout in milliseconds
            
        Returns:
            bool: True if success indicator found
        """
        try:
            for selector in success_selectors:
                try:
                    element = page.wait_for_selector(selector, timeout=timeout)
                    if element:
                        self.logger.info("Found success indicator")
                        return True
                except PlaywrightTimeoutError:
                    continue
            
            self.logger.warning("No success indicator found within timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for success indicator: {e}")
            return False
    
    def _capture_html_state(self, page: Page, step_name: str, description: str = ""):
        """
        Capture HTML state for debugging.
        
        Args:
            page: Playwright page instance
            step_name: Name of the step for file naming
            description: Description of what's being captured
        """
        if self.html_capture:
            provider_name = self._get_provider_name()
            self.html_capture.capture_html(page, f"{provider_name}_{step_name}", description)
    
    def _get_provider_name(self) -> str:
        """Get the provider name for logging/capture purposes."""
        return self.__class__.__name__.replace('EmailComposer', '').lower()
    
    def _handle_contenteditable_body(self, page: Page, body_field, body_content: str, 
                                    content_type: str) -> bool:
        """
        Handle contenteditable body fields (common in modern email interfaces).
        
        Args:
            page: Playwright page instance
            body_field: The contenteditable element
            body_content: Content to fill
            content_type: 'html' or 'text'
            
        Returns:
            bool: True if successful
        """
        try:
            self.logger.info("Detected contenteditable body field - using direct content filling strategy")
            
            # Click to focus
            body_field.click()
            self._wait_with_random_delay('field_fill')
            
            # Clear existing content
            body_field.evaluate("element => element.innerHTML = ''")
            
            # Fill content based on type
            if content_type.lower() == 'html':
                body_field.evaluate(f"element => element.innerHTML = `{body_content}`")
            else:
                body_field.evaluate(f"element => element.textContent = `{body_content}`")
            
            self.logger.info("Contenteditable body filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill contenteditable body: {e}")
            return False
