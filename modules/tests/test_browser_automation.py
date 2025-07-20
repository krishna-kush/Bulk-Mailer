# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Test suite for browser automation functionality.
#              Tests browser handler, provider automation, and email sending.
#
# Components: - Browser Handler Tests
#             - ProtonMail Automation Tests
#             - Browser Email Sender Tests
#             - Integration Tests
#             - Cookie Validation Tests
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
import unittest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.browser.browser_handler import BrowserHandler
from modules.browser.providers.protonmail_automation import ProtonMailAutomation
from modules.browser.browser_email_sender import BrowserEmailSender
from modules.mailer.unified_email_sender import UnifiedEmailSender

class TestBrowserHandler(unittest.TestCase):
    """Test cases for BrowserHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "headless": True,
            "max_concurrent_browsers": 2,
            "browser_timeout": 30,
            "page_load_timeout": 15,
            "min_action_delay": 1,
            "max_action_delay": 2,
            "randomize_viewport": True,
            "use_random_user_agent": True
        }
        self.logger = Mock()
        self.browser_handler = BrowserHandler(self.config, self.logger)
    
    def test_initialization(self):
        """Test browser handler initialization."""
        self.assertIsNotNone(self.browser_handler)
        self.assertEqual(self.browser_handler.config, self.config)
        self.assertEqual(self.browser_handler.logger, self.logger)
        self.assertIsNone(self.browser_handler.playwright)
        self.assertIsNone(self.browser_handler.browser)
    
    def test_random_viewport_generation(self):
        """Test random viewport generation."""
        viewport = self.browser_handler._get_random_viewport()
        self.assertIn("width", viewport)
        self.assertIn("height", viewport)
        self.assertIsInstance(viewport["width"], int)
        self.assertIsInstance(viewport["height"], int)
    
    def test_simulate_human_delay(self):
        """Test human delay simulation."""
        import time
        start_time = time.time()
        self.browser_handler.simulate_human_delay(0.1, 0.2)
        end_time = time.time()
        delay = end_time - start_time
        self.assertGreaterEqual(delay, 0.1)
        self.assertLessEqual(delay, 0.3)  # Allow some tolerance
    
    def test_typing_delay(self):
        """Test typing delay generation."""
        delay = self.browser_handler.simulate_typing_delay()
        self.assertIsInstance(delay, int)
        self.assertGreaterEqual(delay, 50)
        self.assertLessEqual(delay, 150)

class TestProtonMailAutomation(unittest.TestCase):
    """Test cases for ProtonMail automation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            "base_url": "https://mail.proton.me",
            "login_url": "https://account.proton.me/login",
            "compose_button": '[data-testid="sidebar:compose"]',
            "to_field": '[data-testid="composer:to"]',
            "subject_field": '[data-testid="composer:subject"]',
            "body_field": '[data-testid="rooster-editor"]',
            "send_button": '[data-testid="composer:send-button"]',
            "compose_wait": 2,
            "send_wait": 1,
            "page_load_wait": 3
        }
        self.logger = Mock()
        self.automation = ProtonMailAutomation(self.config, self.logger)
    
    def test_initialization(self):
        """Test ProtonMail automation initialization."""
        self.assertIsNotNone(self.automation)
        self.assertEqual(self.automation.config, self.config)
        self.assertEqual(self.automation.base_url, "https://mail.proton.me")
        self.assertIn("compose_button", self.automation.selectors)

class TestBrowserEmailSender(unittest.TestCase):
    """Test cases for BrowserEmailSender class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.browser_config = {
            "enable_browser_automation": True,
            "headless": True,
            "max_concurrent_browsers": 2
        }
        self.providers_config = {
            "protonmail": {
                "enabled": True,
                "base_url": "https://mail.proton.me"
            }
        }
        self.logger = Mock()
        self.browser_sender = BrowserEmailSender(
            self.browser_config, 
            self.providers_config, 
            self.logger
        )
    
    def test_initialization(self):
        """Test browser email sender initialization."""
        self.assertIsNotNone(self.browser_sender)
        self.assertEqual(len(self.browser_sender.provider_automations), 1)
        self.assertIn("protonmail", self.browser_sender.provider_automations)
    
    def test_supported_providers(self):
        """Test supported providers list."""
        providers = self.browser_sender.get_supported_providers()
        self.assertIn("protonmail", providers)
    
    def test_provider_support_check(self):
        """Test provider support checking."""
        self.assertTrue(self.browser_sender.is_provider_supported("protonmail"))
        self.assertFalse(self.browser_sender.is_provider_supported("unsupported"))

class TestUnifiedEmailSender(unittest.TestCase):
    """Test cases for UnifiedEmailSender class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.smtp_configs = {
            "default": {
                "host": "smtp.example.com",
                "port": 587,
                "use_tls": True
            }
        }
        self.browser_config = {
            "enable_browser_automation": True,
            "headless": True
        }
        self.providers_config = {
            "protonmail": {
                "enabled": True,
                "base_url": "https://mail.proton.me"
            }
        }
        self.logger = Mock()
    
    def test_smtp_mode_initialization(self):
        """Test unified sender initialization in SMTP mode."""
        sender = UnifiedEmailSender(
            self.smtp_configs, 
            self.browser_config, 
            self.providers_config, 
            "smtp", 
            self.logger
        )
        self.assertEqual(sender.get_sending_mode(), "smtp")
        self.assertIsNotNone(sender.smtp_sender)
        self.assertIsNone(sender.browser_sender)
    
    def test_browser_mode_initialization(self):
        """Test unified sender initialization in browser mode."""
        with patch('modules.browser.browser_email_sender.BrowserEmailSender') as mock_browser:
            mock_instance = Mock()
            mock_instance.start_browser.return_value = True
            mock_browser.return_value = mock_instance
            
            sender = UnifiedEmailSender(
                self.smtp_configs, 
                self.browser_config, 
                self.providers_config, 
                "browser", 
                self.logger
            )
            self.assertEqual(sender.get_sending_mode(), "browser")
    
    def test_invalid_mode_fallback(self):
        """Test fallback to SMTP mode for invalid sending mode."""
        sender = UnifiedEmailSender(
            self.smtp_configs, 
            self.browser_config, 
            self.providers_config, 
            "invalid_mode", 
            self.logger
        )
        self.assertEqual(sender.get_sending_mode(), "smtp")

class TestCookieValidation(unittest.TestCase):
    """Test cases for cookie validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
        
        # Create temporary cookie file
        self.temp_cookie_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        cookie_data = [
            {
                "domain": ".proton.me",
                "name": "test_cookie",
                "value": "test_value",
                "path": "/",
                "sameSite": "lax",
                "secure": True,
                "httpOnly": False
            }
        ]
        json.dump(cookie_data, self.temp_cookie_file)
        self.temp_cookie_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.temp_cookie_file.name)
        except:
            pass
    
    def test_cookie_file_loading(self):
        """Test cookie file loading."""
        config = {"headless": True}
        handler = BrowserHandler(config, self.logger)
        
        # Test with valid cookie file
        with patch.object(handler, 'browser') as mock_browser:
            mock_context = Mock()
            mock_browser.new_context.return_value = mock_context
            
            context = handler.create_context_with_cookies("test@proton.me", self.temp_cookie_file.name)
            self.assertIsNotNone(context)
    
    def test_missing_cookie_file(self):
        """Test handling of missing cookie file."""
        config = {"headless": True}
        handler = BrowserHandler(config, self.logger)
        
        context = handler.create_context_with_cookies("test@proton.me", "nonexistent.json")
        self.assertIsNone(context)

class TestIntegration(unittest.TestCase):
    """Integration tests for browser automation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = Mock()
    
    def test_end_to_end_configuration(self):
        """Test end-to-end configuration validation."""
        # Test sender configuration validation
        sender_info = {
            "email": "test@proton.me",
            "provider": "protonmail",
            "cookie_file": "/path/to/cookies.json"
        }
        
        browser_config = {"enable_browser_automation": True}
        providers_config = {"protonmail": {"enabled": True}}
        
        with patch('modules.browser.browser_email_sender.BrowserEmailSender') as mock_browser:
            mock_instance = Mock()
            mock_instance.start_browser.return_value = True
            mock_instance.is_provider_supported.return_value = True
            mock_browser.return_value = mock_instance
            
            sender = UnifiedEmailSender(
                {}, browser_config, providers_config, "browser", self.logger
            )
            
            # This should not raise an exception
            is_valid = sender.validate_sender_configuration(sender_info)
            # Note: Will be False due to missing cookie file, but shouldn't crash

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestBrowserHandler))
    test_suite.addTest(unittest.makeSuite(TestProtonMailAutomation))
    test_suite.addTest(unittest.makeSuite(TestBrowserEmailSender))
    test_suite.addTest(unittest.makeSuite(TestUnifiedEmailSender))
    test_suite.addTest(unittest.makeSuite(TestCookieValidation))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
