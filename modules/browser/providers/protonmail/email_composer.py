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

class ProtonMailEmailComposer:
    """Handles ProtonMail email composition and sending."""
    
    def __init__(self, config: Dict[str, Any], logger, html_capture=None):
        """
        Initialize ProtonMail email composer.
        
        Args:
            config: Provider-specific configuration
            logger: Logger instance
            html_capture: HTML capture utility
        """
        self.config = config
        self.logger = logger
        self.html_capture = html_capture
        
        # Timing configuration
        self.timing = {
            "compose_wait": config.get("compose_wait", 3),
            "send_wait": config.get("send_wait", 2),
            "page_load_wait": config.get("page_load_wait", 5)
        }
        
        # Email composition selectors with multiple strategies
        self.selectors = {
            "compose_button": [
                '[data-testid="sidebar:compose"]',
                'button[title*="compose"]',
                'button[title*="Compose"]',
                '.compose-button',
                '[aria-label*="compose"]',
                'button:has-text("Compose")',
                '[data-cy="compose-button"]'
            ],
            "to_field": [
                '[data-testid="composer:to"]',
                'input[placeholder*="To"]',
                'input[name="to"]',
                '.composer-to-editor input',
                '[aria-label*="To"]',
                '.to-field input'
            ],
            "subject_field": [
                '[data-testid="composer:subject"]',
                'input[placeholder*="Subject"]',
                'input[name="subject"]',
                '.composer-subject input',
                '[aria-label*="Subject"]',
                '.subject-field input'
            ],
            "body_field": [
                # ProtonMail uses iframe for email body - prioritize iframe selectors
                '[data-testid="rooster-iframe"]',
                'iframe[title*="Email composer"]',
                'iframe[title*="composer"]',
                'iframe[title*="editor"]',
                '.composer-content iframe',
                '.editor iframe',
                # Fallback to direct contenteditable (if iframe fails)
                '[data-testid="rooster-editor"]',
                '.composer-content [contenteditable="true"]',
                '.rooster-editor',
                '.ProseMirror',
                '[role="textbox"]',
                '.editor-content',
                '.compose-body [contenteditable="true"]',
                '.composer-body-container [contenteditable="true"]',
                '.editor-wrapper [contenteditable="true"]',
                # Avoid search fields - be more specific
                '.composer [contenteditable="true"]:not([data-testid*="search"])',
                '.compose [contenteditable="true"]:not([data-testid*="search"])',
                'div[contenteditable]:not([placeholder*="Search"]):not([data-testid*="search"])',
                '[contenteditable="true"]:not([placeholder*="Search"]):not([data-testid*="search"])',
                # Editor class selectors
                '.editor',
                '.composer-content .editor',
                '.message-editor',
                '.email-editor',
                '.composer-editor',
                # Last resort selectors
                'textarea',
                '.composer textarea'
            ],
            "send_button": [
                '[data-testid="composer:send-button"]',
                'button[title*="Send"]',
                'button:has-text("Send")',
                '.composer-send-button',
                '[aria-label*="Send"]',
                'button[type="submit"]'
            ]
        }
    
    def compose_and_send_email(self, page: Page, recipient_email: str, subject: str, 
                              body_content: str, content_type: str = "html") -> bool:
        """
        Complete email composition and sending workflow.
        
        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            subject: Email subject
            body_content: Email body content
            content_type: Content type (html or plain)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Capture before opening compose
            if self.html_capture:
                self.html_capture.capture_html(page, "before_compose", 
                                             "Before opening compose window")
            
            # Open compose window
            if not self.open_compose(page):
                return False
            
            # Capture after opening compose
            if self.html_capture:
                self.html_capture.capture_with_selectors(page, "compose_opened", 
                                                       {
                                                           "to_field": self.selectors["to_field"][0],
                                                           "subject_field": self.selectors["subject_field"][0],
                                                           "body_field": self.selectors["body_field"][0]
                                                       },
                                                       "Compose window opened")
            
            # Fill recipient
            if not self.fill_recipient(page, recipient_email):
                return False
            
            # Capture after filling recipient
            if self.html_capture:
                self.html_capture.capture_form_state(page, "recipient_filled", 
                                                   {"to_field": self.selectors["to_field"][0]},
                                                   f"After filling recipient: {recipient_email}")
            
            # Fill subject
            if not self.fill_subject(page, subject):
                return False
            
            # Capture after filling subject
            if self.html_capture:
                self.html_capture.capture_form_state(page, "subject_filled", 
                                                   {"subject_field": self.selectors["subject_field"][0]},
                                                   f"After filling subject: {subject}")
            
            # Fill body
            if not self.fill_body(page, body_content, content_type):
                return False
            
            # Capture after filling body
            if self.html_capture:
                self.html_capture.capture_form_state(page, "body_filled", 
                                                   {"body_field": self.selectors["body_field"][0]},
                                                   f"After filling body content ({content_type})")
            
            # Send email
            if not self.send_email(page):
                return False
            
            # Capture after sending
            if self.html_capture:
                self.html_capture.capture_html(page, "email_sent", 
                                             f"After sending email to {recipient_email}")
            
            self.logger.info(f"Successfully sent email to {recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to compose and send email: {e}")
            
            # Capture error state
            if self.html_capture:
                self.html_capture.capture_html(page, "email_send_error", 
                                             f"Error during email sending: {str(e)}")
            return False
    
    def open_compose(self, page: Page) -> bool:
        """
        Open email compose window or reuse existing one.
        For session reuse, this will click "New Message" if already in mail interface.

        Args:
            page: Playwright page instance

        Returns:
            bool: True if compose window opened successfully
        """
        try:
            self.logger.debug("Opening compose window...")

            # Check if we're already in a compose window (for session reuse)
            existing_to_field = self._find_element_by_selectors(page, self.selectors["to_field"])
            if existing_to_field:
                # Check if the compose window is empty/ready for new email
                try:
                    to_value = existing_to_field.input_value()
                    if not to_value or to_value.strip() == "":
                        self.logger.info("🔄 Reusing existing empty compose window")
                        return True
                    else:
                        self.logger.debug("🔄 Existing compose window has content, need to open new one")
                except:
                    pass

            # Find compose button (this will be "New Message" if already in mail interface)
            compose_button = self._find_element_by_selectors(page, self.selectors["compose_button"])
            if not compose_button:
                self.logger.error("Compose button not found")
                return False

            # Click compose button with human-like delay
            time.sleep(random.uniform(0.5, 1.0))
            compose_button.click()
            self.logger.info("🔄 Clicked compose/new message button")

            # Wait for compose window to open
            time.sleep(self.timing["compose_wait"])

            # Verify compose window is open by checking for recipient field
            try:
                page.wait_for_selector(self.selectors["to_field"][0], timeout=10000)
                self.logger.debug("Compose window opened successfully")
                return True
            except PlaywrightTimeoutError:
                self.logger.error("Compose window did not open - recipient field not found")
                return False

        except Exception as e:
            self.logger.error(f"Failed to open compose window: {e}")
            return False
    
    def fill_recipient(self, page: Page, recipient_email: str) -> bool:
        """
        Fill the recipient email field.
        
        Args:
            page: Playwright page instance
            recipient_email: Recipient email address
            
        Returns:
            bool: True if recipient filled successfully
        """
        try:
            self.logger.debug(f"Filling recipient: {recipient_email}")
            
            # Find recipient field
            to_field = self._find_element_by_selectors(page, self.selectors["to_field"])
            if not to_field:
                self.logger.error("Recipient field not found")
                return False
            
            # Click and fill recipient field
            to_field.click()
            time.sleep(0.5)
            
            # Type like human
            self._type_human_like(page, self.selectors["to_field"][0], recipient_email)
            
            # Press Tab or Enter to confirm recipient
            time.sleep(0.5)
            page.keyboard.press("Tab")
            time.sleep(0.3)
            
            self.logger.debug("Recipient filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill recipient: {e}")
            return False
    
    def fill_subject(self, page: Page, subject: str) -> bool:
        """
        Fill the email subject field.
        
        Args:
            page: Playwright page instance
            subject: Email subject
            
        Returns:
            bool: True if subject filled successfully
        """
        try:
            self.logger.debug(f"Filling subject: {subject}")
            
            # Find subject field
            subject_field = self._find_element_by_selectors(page, self.selectors["subject_field"])
            if not subject_field:
                self.logger.error("Subject field not found")
                return False
            
            # Click and fill subject field
            subject_field.click()
            time.sleep(0.5)
            
            # Clear field first
            subject_field.fill("")
            time.sleep(0.3)
            
            # Type like human
            self._type_human_like(page, self.selectors["subject_field"][0], subject)
            
            time.sleep(0.3)
            self.logger.debug("Subject filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fill subject: {e}")
            return False
    
    def fill_body(self, page: Page, body_content: str, content_type: str = "html") -> bool:
        """
        Fill the email body content with enhanced strategies.

        Args:
            page: Playwright page instance
            body_content: Email body content
            content_type: Content type (html or plain)

        Returns:
            bool: True if body filled successfully
        """
        try:
            self.logger.debug(f"Filling body content ({content_type}) - {len(body_content)} characters")

            # Enhanced body field finding with multiple strategies
            body_field = None
            successful_selector = None

            # Wait for compose window to fully load and iframe to be ready
            time.sleep(5)

            # Additional wait for iframe to load if we're looking for iframe selectors
            iframe_selectors = ['[data-testid="rooster-iframe"]', 'iframe[title*="composer"]', 'iframe[title*="Email composer"]']
            for iframe_selector in iframe_selectors:
                try:
                    page.wait_for_selector(iframe_selector, timeout=3000)
                    self.logger.debug(f"Iframe detected with selector: {iframe_selector}")
                    break
                except:
                    continue

            # Strategy 1: Try each selector with enhanced detection and filtering
            for selector in self.selectors["body_field"]:
                try:
                    self.logger.debug(f"Trying selector: {selector}")

                    # Wait for element with shorter timeout
                    page.wait_for_selector(selector, timeout=2000)
                    elements = page.query_selector_all(selector)

                    for element in elements:
                        if element and element.is_visible():
                            # Check if this is an iframe (ProtonMail uses iframe for email body)
                            try:
                                tag_name = element.evaluate("el => el.tagName").lower()
                            except:
                                tag_name = ""

                            if tag_name == 'iframe':
                                self.logger.debug(f"Found iframe element: {selector}")
                                # For iframe, we'll handle it specially in the filling method
                                body_field = element
                                successful_selector = selector
                                self.logger.info(f"Selected iframe body field: {selector}")
                                break

                            # Enhanced filtering to avoid search fields and wrong elements
                            try:
                                # Check if element is interactable and has reasonable size
                                bounding_box = element.bounding_box()
                                if not (bounding_box and bounding_box['width'] > 100 and bounding_box['height'] > 50):
                                    continue

                                # Get element attributes for filtering
                                placeholder = element.get_attribute('placeholder') or ''
                                aria_label = element.get_attribute('aria-label') or ''
                                class_name = element.get_attribute('class') or ''
                                id_attr = element.get_attribute('id') or ''

                                # Skip search fields and navigation elements
                                skip_keywords = ['search', 'nav', 'menu', 'toolbar', 'header', 'sidebar']
                                if any(keyword in (placeholder + aria_label + class_name + id_attr).lower()
                                       for keyword in skip_keywords):
                                    self.logger.debug(f"Skipping element with search/nav keywords: {selector}")
                                    continue

                                # For placeholder*="message", ensure it's in compose area
                                if 'placeholder*="message"' in selector:
                                    # Check if element is within compose container
                                    parent_classes = []
                                    current = element
                                    for _ in range(5):  # Check up to 5 parent levels
                                        try:
                                            current = current.evaluate("el => el.parentElement")
                                            if current:
                                                parent_class = current.get_attribute('class') or ''
                                                parent_classes.append(parent_class.lower())
                                            else:
                                                break
                                        except:
                                            break

                                    # Only accept if it's in compose area
                                    compose_keywords = ['compose', 'editor', 'message', 'mail']
                                    if not any(keyword in ' '.join(parent_classes) for keyword in compose_keywords):
                                        self.logger.debug(f"Skipping message field not in compose area: {selector}")
                                        continue

                                # Additional check for contenteditable elements
                                if element.get_attribute('contenteditable') == 'true':
                                    # Prefer larger contenteditable areas (likely the main editor)
                                    if bounding_box['width'] > 200 and bounding_box['height'] > 100:
                                        body_field = element
                                        successful_selector = selector
                                        self.logger.debug(f"Found large contenteditable body field: {selector}")
                                        break

                                # If we get here, it's a potential candidate
                                if not body_field:  # Only take first suitable candidate
                                    body_field = element
                                    successful_selector = selector
                                    self.logger.debug(f"Found potential body field: {selector}")

                            except Exception as check_error:
                                self.logger.debug(f"Error checking element: {check_error}")
                                continue

                    if body_field:
                        break

                except Exception as e:
                    self.logger.debug(f"Selector {selector} failed: {e}")
                    continue

            # Strategy 2: If no field found, try alternative approach
            if not body_field:
                self.logger.warning("Standard selectors failed, trying alternative approach...")

                # Try to find any contenteditable element in the compose area
                alternative_selectors = [
                    '.composer-container [contenteditable]',
                    '.composer [contenteditable]',
                    '.compose [contenteditable]',
                    'div[contenteditable="true"]',
                    '[contenteditable="true"]'
                ]

                for selector in alternative_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        for element in elements:
                            if element and element.is_visible():
                                # Check if it's not the subject or recipient field
                                placeholder = element.get_attribute('placeholder') or ''
                                aria_label = element.get_attribute('aria-label') or ''

                                if ('message' in placeholder.lower() or
                                    'body' in placeholder.lower() or
                                    'content' in placeholder.lower() or
                                    ('message' in aria_label.lower())):
                                    body_field = element
                                    successful_selector = selector
                                    self.logger.debug(f"Found body field with alternative selector: {selector}")
                                    break

                        if body_field:
                            break

                    except Exception as e:
                        self.logger.debug(f"Alternative selector {selector} failed: {e}")
                        continue

            if not body_field:
                self.logger.error("Body field not found with any strategy")
                if self.html_capture:
                    self.html_capture.capture_html(page, "body_field_not_found",
                                                 "Body field not found after all strategies")
                return False

            self.logger.info(f"Using body field selector: {successful_selector}")

            # Check if we're dealing with an iframe
            try:
                tag_name = body_field.evaluate("el => el.tagName").lower()
                is_iframe = tag_name == 'iframe'
            except:
                is_iframe = False

            if is_iframe:
                self.logger.info("Detected iframe body field - using iframe content filling strategy")
                # For iframe, we need to access the content inside the iframe
                try:
                    # Wait for iframe to load
                    time.sleep(2)

                    # Get the iframe's content frame
                    iframe_content = body_field.content_frame()
                    if iframe_content:
                        self.logger.debug("Successfully accessed iframe content")

                        # Try to find contenteditable element inside iframe
                        iframe_body_selectors = [
                            'body[contenteditable="true"]',
                            '[contenteditable="true"]',
                            'body',
                            'div[contenteditable="true"]',
                            '.editor',
                            'div'
                        ]

                        iframe_body_element = None
                        for iframe_selector in iframe_body_selectors:
                            try:
                                iframe_body_element = iframe_content.query_selector(iframe_selector)
                                if iframe_body_element:
                                    self.logger.debug(f"Found iframe body element with: {iframe_selector}")
                                    break
                            except:
                                continue

                        if iframe_body_element:
                            # Click on the iframe body element
                            iframe_body_element.click()
                            time.sleep(0.5)

                            # Clear content using page keyboard (iframe content doesn't have keyboard attribute)
                            iframe_body_element.click()
                            time.sleep(0.2)
                            page.keyboard.press("Control+a")
                            time.sleep(0.2)
                            page.keyboard.press("Delete")
                            time.sleep(0.5)

                            # Fill content based on type
                            if content_type.lower() == "html":
                                success = self._fill_iframe_html_content(page, iframe_content, iframe_body_element, body_content)
                            else:
                                success = self._fill_iframe_plain_content(page, iframe_content, body_content)

                            if success:
                                self.logger.info("Iframe content filled successfully")
                                if self.html_capture:
                                    self.html_capture.capture_html(page, "iframe_body_filled_success",
                                                                 f"Iframe body content filled successfully ({content_type})")
                                return True
                        else:
                            self.logger.error("Could not find body element inside iframe")
                    else:
                        self.logger.error("Could not access iframe content")

                except Exception as iframe_error:
                    self.logger.error(f"Error handling iframe: {iframe_error}")

                # If iframe handling failed, fall back to regular method
                self.logger.warning("Iframe handling failed, falling back to regular method")

            # Enhanced clicking and focusing strategy for non-iframe elements
            try:
                # Scroll element into view
                body_field.scroll_into_view_if_needed()
                time.sleep(0.5)

                # Try multiple click strategies
                click_success = False

                # Strategy 1: Regular click
                try:
                    body_field.click(timeout=5000)
                    click_success = True
                    self.logger.debug("Regular click successful")
                except Exception as e:
                    self.logger.debug(f"Regular click failed: {e}")

                # Strategy 2: Force click if regular click failed
                if not click_success:
                    try:
                        body_field.click(force=True)
                        click_success = True
                        self.logger.debug("Force click successful")
                    except Exception as e:
                        self.logger.debug(f"Force click failed: {e}")

                # Strategy 3: Focus if click failed
                if not click_success:
                    try:
                        body_field.focus()
                        click_success = True
                        self.logger.debug("Focus successful")
                    except Exception as e:
                        self.logger.debug(f"Focus failed: {e}")

                if not click_success:
                    self.logger.warning("All click strategies failed, proceeding anyway...")

                time.sleep(1)

            except Exception as e:
                self.logger.warning(f"Error during click/focus: {e}")

            # Enhanced content clearing
            try:
                # Multiple clearing strategies
                page.keyboard.press("Control+a")
                time.sleep(0.3)
                page.keyboard.press("Delete")
                time.sleep(0.3)

                # Additional clearing
                page.keyboard.press("Control+a")
                time.sleep(0.2)
                page.keyboard.press("Backspace")
                time.sleep(0.5)

                self.logger.debug("Content cleared")

            except Exception as e:
                self.logger.warning(f"Error during content clearing: {e}")

            # Enhanced content filling based on type
            if content_type.lower() == "html":
                success = self._fill_html_content(page, body_field, body_content)
            else:
                success = self._fill_plain_content(page, body_field, body_content)

            if success:
                self.logger.info("Body content filled successfully")

                # Capture successful state
                if self.html_capture:
                    self.html_capture.capture_html(page, "body_filled_success",
                                                 f"Body content filled successfully ({content_type})")
                return True
            else:
                self.logger.error("Failed to fill body content")
                return False

        except Exception as e:
            self.logger.error(f"Failed to fill email body: {e}")
            if self.html_capture:
                self.html_capture.capture_html(page, "body_fill_error",
                                             f"Error during body filling: {str(e)}")
            return False
    
    def send_email(self, page: Page) -> bool:
        """
        Send the composed email.
        
        Args:
            page: Playwright page instance
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            self.logger.debug("Sending email...")
            
            # Find send button
            send_button = self._find_element_by_selectors(page, self.selectors["send_button"])
            if not send_button:
                self.logger.error("Send button not found")
                return False
            
            # Click send button with human-like delay
            time.sleep(random.uniform(1.0, 2.0))
            send_button.click()
            self.logger.info("Send button clicked, waiting for email to be processed...")

            # Wait longer for email to be actually sent by ProtonMail servers
            initial_wait = self.timing["send_wait"]
            extended_wait = 8  # Additional wait for server processing

            self.logger.debug(f"Initial wait: {initial_wait}s for UI response...")
            time.sleep(initial_wait)

            # Check for success indicators (compose window should close)
            try:
                # Wait for compose window to disappear
                self.logger.debug("Checking if compose window closes...")
                page.wait_for_selector(self.selectors["to_field"][0], state="detached", timeout=10000)
                self.logger.info("Compose window closed - email accepted by ProtonMail")

                # Additional wait to ensure email is actually sent by servers
                self.logger.info(f"Waiting additional {extended_wait}s for server processing...")
                time.sleep(extended_wait)

                # Look for success indicators in the UI
                try:
                    # Check for success notification or sent folder indication
                    success_indicators = [
                        'text="Message sent"',
                        'text="Email sent"',
                        '[data-testid*="notification"]',
                        '.notification',
                        '[role="alert"]'
                    ]

                    for indicator in success_indicators:
                        try:
                            if page.query_selector(indicator):
                                self.logger.info(f"Found success indicator: {indicator}")
                                break
                        except:
                            continue

                except Exception as indicator_error:
                    self.logger.debug(f"Could not check success indicators: {indicator_error}")

                self.logger.info("Email sending process completed successfully")
                return True

            except PlaywrightTimeoutError:
                # Compose window still open, check for error messages
                self.logger.warning("Compose window still open after send attempt")

                # Look for error messages
                try:
                    error_indicators = [
                        'text*="error"',
                        'text*="failed"',
                        '[data-testid*="error"]',
                        '.error',
                        '[role="alert"]'
                    ]

                    for indicator in error_indicators:
                        try:
                            error_element = page.query_selector(indicator)
                            if error_element:
                                error_text = error_element.text_content() or ""
                                self.logger.error(f"Found error indicator: {error_text}")
                                break
                        except:
                            continue

                except Exception as error_check:
                    self.logger.debug(f"Could not check error indicators: {error_check}")

                return False
                
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
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
            # Fallback to regular typing
            try:
                page.keyboard.type(text)
            except:
                self.logger.error("Failed to type text even with fallback method")
    
    def _fill_html_content(self, page: Page, body_field, content: str) -> bool:
        """
        Fill HTML content with multiple strategies.

        Args:
            page: Playwright page instance
            body_field: Body field element
            content: HTML content to fill

        Returns:
            bool: True if successful
        """
        try:
            self.logger.debug("Attempting HTML content filling...")

            # Strategy 1: Direct innerHTML injection
            try:
                # Escape content for JavaScript
                escaped_content = content.replace('`', '\\`').replace('${', '\\${')
                body_field.evaluate(f"element => element.innerHTML = `{escaped_content}`")
                time.sleep(1)
                self.logger.debug("HTML content set via innerHTML")
                return True
            except Exception as e:
                self.logger.debug(f"innerHTML method failed: {e}")

            # Strategy 2: Type as plain text (fallback)
            self.logger.debug("Falling back to typing HTML as plain text")
            return self._fill_plain_content(page, body_field, content)

        except Exception as e:
            self.logger.error(f"Error filling HTML content: {e}")
            return False

    def _fill_plain_content(self, page: Page, body_field, content: str) -> bool:
        """
        Fill plain text content with enhanced typing strategies.

        Args:
            page: Playwright page instance
            body_field: Body field element
            content: Plain text content to fill

        Returns:
            bool: True if successful
        """
        try:
            self.logger.debug("Attempting plain text content filling...")

            # Strategy 1: Clipboard paste (fastest for long content)
            if len(content) > 100:
                try:
                    # Use clipboard for long content
                    escaped_content = content.replace('\\', '\\\\').replace('`', '\\`')
                    page.evaluate(f"""
                        navigator.clipboard.writeText(`{escaped_content}`).then(() => {{
                            console.log('Content copied to clipboard');
                        }}).catch(err => {{
                            console.error('Clipboard write failed:', err);
                        }});
                    """)
                    time.sleep(0.5)
                    page.keyboard.press("Control+v")
                    time.sleep(1)
                    self.logger.debug("Content pasted via clipboard")
                    return True
                except Exception as e:
                    self.logger.debug(f"Clipboard paste failed: {e}")

            # Strategy 2: Enhanced typing with chunks
            try:
                self._type_body_content_enhanced(page, content)
                self.logger.debug("Content typed successfully")
                return True
            except Exception as e:
                self.logger.debug(f"Enhanced typing failed: {e}")

            # Strategy 3: Simple typing (fallback)
            try:
                page.keyboard.type(content)
                self.logger.debug("Content typed with simple method")
                return True
            except Exception as e:
                self.logger.debug(f"Simple typing failed: {e}")

            return False

        except Exception as e:
            self.logger.error(f"Error filling plain content: {e}")
            return False

    def _type_body_content_enhanced(self, page: Page, content: str):
        """
        Enhanced typing with better chunking and human-like behavior.

        Args:
            page: Playwright page instance
            content: Content to type
        """
        try:
            # Adaptive chunk size based on content length
            if len(content) < 100:
                chunk_size = 20
            elif len(content) < 500:
                chunk_size = 50
            else:
                chunk_size = 100

            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

            self.logger.debug(f"Typing content in {len(chunks)} chunks of ~{chunk_size} characters")

            for i, chunk in enumerate(chunks):
                # Type chunk
                page.keyboard.type(chunk)

                # Human-like delays between chunks
                if i < len(chunks) - 1:
                    delay = random.uniform(0.05, 0.2)
                    time.sleep(delay)

                    # Occasional longer pause (simulate thinking)
                    if random.random() < 0.1:  # 10% chance
                        time.sleep(random.uniform(0.3, 0.7))

        except Exception as e:
            self.logger.error(f"Error in enhanced typing: {e}")
            raise

    def _type_body_content(self, page: Page, content: str):
        """
        Legacy typing method (kept for compatibility).

        Args:
            page: Playwright page instance
            content: Content to type
        """
        try:
            # Use enhanced method
            self._type_body_content_enhanced(page, content)

        except Exception as e:
            self.logger.error(f"Error typing body content: {e}")
            # Last resort - try to paste the content
            try:
                # Copy content to clipboard and paste
                page.evaluate(f"navigator.clipboard.writeText(`{content}`)")
                time.sleep(0.5)
                page.keyboard.press("Control+v")
            except:
                self.logger.error("Failed to paste content as fallback")

    def _fill_iframe_html_content(self, page: Page, iframe_content, iframe_body_element, content: str) -> bool:
        """
        Fill HTML content inside iframe.

        Args:
            page: Playwright page instance
            iframe_content: Iframe content frame
            iframe_body_element: Body element inside iframe
            content: HTML content to fill

        Returns:
            bool: True if successful
        """
        try:
            self.logger.debug("Filling HTML content in iframe...")

            # Try to set innerHTML directly
            try:
                escaped_content = content.replace('`', '\\`').replace('${', '\\${')
                iframe_body_element.evaluate(f"element => element.innerHTML = `{escaped_content}`")
                time.sleep(1)
                self.logger.debug("HTML content set in iframe via innerHTML")
                return True
            except Exception as e:
                self.logger.debug(f"iframe innerHTML method failed: {e}")

            # Fallback to typing using page keyboard
            page.keyboard.type(content)
            self.logger.debug("HTML content typed in iframe")
            return True

        except Exception as e:
            self.logger.error(f"Error filling iframe HTML content: {e}")
            return False

    def _fill_iframe_plain_content(self, page: Page, iframe_content, content: str) -> bool:
        """
        Fill plain text content inside iframe.

        Args:
            page: Playwright page instance
            iframe_content: Iframe content frame
            content: Plain text content to fill

        Returns:
            bool: True if successful
        """
        try:
            self.logger.debug("Filling plain text content in iframe with human-like typing...")

            # Try human-like typing first (more realistic)
            try:
                success = self._type_content_human_like(page, content)
                if success:
                    self.logger.debug("Content typed in iframe with human-like behavior")
                    return True
            except Exception as e:
                self.logger.debug(f"Human-like typing failed: {e}")

            # Fallback to clipboard paste for very long content (>500 chars) only
            if len(content) > 500:
                try:
                    self.logger.debug("Content is very long, using clipboard as fallback...")
                    escaped_content = content.replace('\\', '\\\\').replace('`', '\\`')
                    page.evaluate(f"""
                        navigator.clipboard.writeText(`{escaped_content}`).then(() => {{
                            console.log('Content copied to clipboard');
                        }}).catch(err => {{
                            console.error('Clipboard write failed:', err);
                        }});
                    """)
                    time.sleep(0.5)
                    page.keyboard.press("Control+v")
                    time.sleep(1)
                    self.logger.debug("Content pasted in iframe via clipboard")
                    return True
                except Exception as e:
                    self.logger.debug(f"iframe clipboard paste failed: {e}")

            # Final fallback to basic typing
            page.keyboard.type(content)
            self.logger.debug("Content typed in iframe (basic method)")
            return True

        except Exception as e:
            self.logger.error(f"Error filling iframe plain content: {e}")
            return False

    def _type_content_human_like(self, page: Page, content: str) -> bool:
        """
        Type content with human-like behavior including realistic delays and patterns.

        Args:
            page: Playwright page instance
            content: Content to type

        Returns:
            bool: True if successful
        """
        try:
            self.logger.debug(f"Starting human-like typing for {len(content)} characters...")

            # Split content into chunks (words, sentences, paragraphs)
            chunks = self._split_content_for_typing(content)

            total_chunks = len(chunks)
            for i, chunk in enumerate(chunks):
                # Type the chunk
                page.keyboard.type(chunk)

                # Add realistic delays based on chunk type and position
                if i < total_chunks - 1:  # Don't delay after the last chunk
                    delay = self._calculate_typing_delay(chunk, i, total_chunks)
                    if delay > 0:
                        time.sleep(delay)

                # Occasional longer pauses (simulating thinking/reading)
                if i > 0 and i % 15 == 0:  # Every 15 chunks
                    thinking_pause = random.uniform(0.8, 1.5)
                    self.logger.debug(f"Adding thinking pause: {thinking_pause:.2f}s")
                    time.sleep(thinking_pause)

            self.logger.debug("Human-like typing completed successfully")
            return True

        except Exception as e:
            self.logger.debug(f"Error in human-like typing: {e}")
            return False

    def _split_content_for_typing(self, content: str) -> list:
        """
        Split content into natural chunks for human-like typing while preserving original spacing.

        Args:
            content: Content to split

        Returns:
            list: List of content chunks
        """
        chunks = []

        # Debug: Log original content structure
        self.logger.debug(f"🔍 CONTENT SPLITTING DEBUG: Original content has {content.count(chr(10))} line breaks")

        # Simple approach: Split by sentences and preserve all spacing
        # Split by periods followed by space, but preserve the period and space
        import re

        # Split content while preserving line breaks and spacing
        # Use regex to split on sentence boundaries but keep delimiters
        sentence_pattern = r'(\. |\.\n|\n\n|\n)'
        parts = re.split(sentence_pattern, content)

        current_chunk = ""
        for part in parts:
            if part:  # Skip empty parts
                current_chunk += part

                # If we hit a sentence boundary or line break, make it a chunk
                if part in ['. ', '.\n', '\n\n', '\n'] or len(current_chunk) > 100:
                    if current_chunk.strip():
                        chunks.append(current_chunk)
                        current_chunk = ""

        # Add any remaining content
        if current_chunk.strip():
            chunks.append(current_chunk)

        # If no sentence splitting worked, fall back to simple word grouping
        if len(chunks) <= 1:
            words = content.split()
            chunks = []
            for i in range(0, len(words), 6):  # Groups of 6 words
                word_group = ' '.join(words[i:i+6])
                chunks.append(word_group)

        self.logger.debug(f"🔍 CONTENT SPLITTING DEBUG: Split into {len(chunks)} chunks")
        return chunks

    def _calculate_typing_delay(self, chunk: str, chunk_index: int, total_chunks: int) -> float:
        """
        Calculate realistic typing delay based on chunk characteristics.

        Args:
            chunk: The text chunk that was just typed
            chunk_index: Index of current chunk
            total_chunks: Total number of chunks

        Returns:
            float: Delay in seconds
        """
        base_delay = 0.1  # Base delay between chunks

        # Longer delays after punctuation
        if chunk.strip().endswith(('.', '!', '?')):
            return random.uniform(0.3, 0.7)  # Sentence end pause

        # Medium delays after commas
        if chunk.strip().endswith(','):
            return random.uniform(0.2, 0.4)  # Comma pause

        # Longer delays after paragraph breaks
        if '\n\n' in chunk:
            return random.uniform(0.5, 1.0)  # Paragraph pause

        # Shorter delays for word groups
        if len(chunk.split()) <= 4:
            return random.uniform(0.1, 0.3)  # Word group pause

        # Variable delay based on chunk length
        length_factor = min(len(chunk) / 50, 0.5)  # Max 0.5s for length
        random_factor = random.uniform(0.05, 0.25)

        return base_delay + length_factor + random_factor
