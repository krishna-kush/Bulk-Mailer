# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: HTML capture utility for debugging browser automation.
#              Captures page source at critical steps for analysis and optimization.
#
# Components: - HTML Source Capture
#             - Timestamped File Naming
#             - Selector Analysis
#             - Debug Information Extraction
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

import os
import time
from datetime import datetime
from typing import Optional, Dict, Any
from playwright.sync_api import Page

class HTMLCapture:
    """Utility for capturing HTML at critical automation steps."""
    
    def __init__(self, base_dir: str, logger):
        """
        Initialize HTML capture utility.
        
        Args:
            base_dir: Base directory for the mailer
            logger: Logger instance
        """
        self.base_dir = base_dir
        self.logger = logger
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create session-specific capture directory
        self.capture_dir = os.path.join(base_dir, "logs", "html_captures", self.session_id)
        os.makedirs(self.capture_dir, exist_ok=True)
        
        # Capture counter for ordering
        self.capture_count = 0
    
    def capture_html(self, page: Page, step_name: str, description: str = "", 
                    additional_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Capture HTML source at a specific step.
        
        Args:
            page: Playwright page instance
            step_name: Name of the step (e.g., "initial_load", "after_login")
            description: Human-readable description
            additional_info: Additional information to include in the capture
            
        Returns:
            Path to the saved HTML file
        """
        try:
            self.capture_count += 1
            
            # Generate filename
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"{self.capture_count:02d}_{timestamp}_{step_name}.html"
            filepath = os.path.join(self.capture_dir, filename)
            
            # Get page information
            current_url = page.url
            page_title = page.title()
            
            # Get HTML content
            html_content = page.content()
            
            # Create debug header
            debug_header = f"""<!--
================================================================================
HTML CAPTURE DEBUG INFORMATION
================================================================================
Session ID: {self.session_id}
Capture Count: {self.capture_count}
Step Name: {step_name}
Description: {description}
Timestamp: {datetime.now().isoformat()}
Current URL: {current_url}
Page Title: {page_title}
"""
            
            # Add additional info if provided
            if additional_info:
                debug_header += "\nAdditional Information:\n"
                for key, value in additional_info.items():
                    debug_header += f"  {key}: {value}\n"
            
            debug_header += "================================================================================\n-->\n\n"
            
            # Combine debug header with HTML content
            full_content = debug_header + html_content
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            self.logger.debug(f"HTML captured: {step_name} -> {filename}")
            
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to capture HTML for step '{step_name}': {e}")
            return ""
    
    def capture_with_selectors(self, page: Page, step_name: str, selectors: Dict[str, str], 
                              description: str = "") -> str:
        """
        Capture HTML and analyze specific selectors.
        
        Args:
            page: Playwright page instance
            step_name: Name of the step
            selectors: Dictionary of selector names and CSS selectors to analyze
            description: Human-readable description
            
        Returns:
            Path to the saved HTML file
        """
        try:
            # Analyze selectors
            selector_results = {}
            for name, selector in selectors.items():
                try:
                    element = page.query_selector(selector)
                    if element:
                        # Get element info
                        tag_name = element.evaluate("el => el.tagName")
                        is_visible = element.is_visible()
                        text_content = element.text_content()[:100] if element.text_content() else ""
                        
                        selector_results[name] = {
                            "selector": selector,
                            "found": True,
                            "tag": tag_name,
                            "visible": is_visible,
                            "text": text_content
                        }
                    else:
                        selector_results[name] = {
                            "selector": selector,
                            "found": False
                        }
                except Exception as e:
                    selector_results[name] = {
                        "selector": selector,
                        "error": str(e)
                    }
            
            # Capture HTML with selector analysis
            additional_info = {
                "selector_analysis": selector_results
            }
            
            return self.capture_html(page, step_name, description, additional_info)
            
        except Exception as e:
            self.logger.error(f"Failed to capture HTML with selectors for step '{step_name}': {e}")
            return ""
    
    def capture_form_state(self, page: Page, step_name: str, form_selectors: Dict[str, str], 
                          description: str = "") -> str:
        """
        Capture HTML and analyze form field states.
        
        Args:
            page: Playwright page instance
            step_name: Name of the step
            form_selectors: Dictionary of form field names and selectors
            description: Human-readable description
            
        Returns:
            Path to the saved HTML file
        """
        try:
            # Analyze form fields
            form_analysis = {}
            for field_name, selector in form_selectors.items():
                try:
                    element = page.query_selector(selector)
                    if element:
                        field_type = element.get_attribute("type") or "unknown"
                        field_value = element.input_value() if field_type in ["text", "email", "password"] else ""
                        is_enabled = element.is_enabled()
                        is_visible = element.is_visible()
                        
                        form_analysis[field_name] = {
                            "selector": selector,
                            "found": True,
                            "type": field_type,
                            "value_length": len(field_value) if field_value else 0,
                            "enabled": is_enabled,
                            "visible": is_visible
                        }
                    else:
                        form_analysis[field_name] = {
                            "selector": selector,
                            "found": False
                        }
                except Exception as e:
                    form_analysis[field_name] = {
                        "selector": selector,
                        "error": str(e)
                    }
            
            # Capture HTML with form analysis
            additional_info = {
                "form_analysis": form_analysis
            }
            
            return self.capture_html(page, step_name, description, additional_info)
            
        except Exception as e:
            self.logger.error(f"Failed to capture form state for step '{step_name}': {e}")
            return ""
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current capture session.
        
        Returns:
            Dictionary with session information
        """
        return {
            "session_id": self.session_id,
            "capture_count": self.capture_count,
            "capture_dir": self.capture_dir,
            "files_pattern": f"{self.session_id}_*.html"
        }
    
    def cleanup_old_captures(self, days_to_keep: int = 7):
        """
        Clean up old HTML capture files.
        
        Args:
            days_to_keep: Number of days to keep capture files
        """
        try:
            if not os.path.exists(self.capture_dir):
                return
            
            current_time = time.time()
            cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
            
            removed_count = 0
            for filename in os.listdir(self.capture_dir):
                if filename.endswith('.html'):
                    filepath = os.path.join(self.capture_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        removed_count += 1
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old HTML capture files")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old captures: {e}")
