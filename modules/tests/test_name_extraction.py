#!/usr/bin/env python3

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

"""
Test suite for email name extraction functionality.
"""

import sys
import os
import unittest

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.utils import extract_name_from_email, _is_likely_company_name


class TestNameExtraction(unittest.TestCase):
    """Test cases for email name extraction functionality."""

    def test_basic_person_names(self):
        """Test extraction of basic person names."""
        test_cases = [
            ("john@company.com", "John"),
            ("jane.doe@example.com", "Jane Doe"),
            ("mike_wilson@startup.com", "Mike Wilson"),
            ("sarah-johnson@business.com", "Sarah Johnson"),
            ("david123@personal.com", "David"),
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = extract_name_from_email(email)
                self.assertEqual(result, expected)

    def test_generic_emails_default_behavior(self):
        """Test that generic emails return company names by default."""
        test_cases = [
            ("info@company.com", "Company"),
            ("support@techcorp.com", "Techcorp"),
            ("contact@microsoft.com", "Microsoft"),
            ("sales@google.com", "Google"),
            ("help@amazon.com", "Amazon"),
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = extract_name_from_email(email, no_company=False)
                self.assertEqual(result, expected)

    def test_no_company_behavior(self):
        """Test no_company=True behavior."""
        test_cases = [
            ("info@company.com", "There"),
            ("support@techcorp.com", "There"),
            ("john@company.com", "John"),  # Person name preserved
            ("jane.doe@example.com", "Jane Doe"),  # Person name preserved
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = extract_name_from_email(email, no_company=True)
                self.assertEqual(result, expected)

    def test_custom_fallback_name(self):
        """Test custom fallback name functionality."""
        test_cases = [
            ("info@company.com", "Friend"),
            ("support@techcorp.com", "Friend"),
            ("john@company.com", "John"),  # Person name preserved
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = extract_name_from_email(email, no_company=True, name_to_return_when_company_name="Friend")
                self.assertEqual(result, expected)

    def test_word_boundary_detection(self):
        """Test that company indicators are detected as whole words, not substrings."""
        # These should NOT be flagged as companies (person names with substrings)
        person_names = [
            ("francisco@company.com", "Francisco"),
            ("marco@business.com", "Marco"),
            ("disco@music.com", "Disco"),
            ("rocco@restaurant.com", "Rocco"),
            ("franco@consulting.com", "Franco"),
            ("datapoint@analytics.com", "Datapoint"),
            ("ecoline@gmail.com", "Ecoline"),
            ("nicole@startup.com", "Nicole"),
        ]
        
        for email, expected in person_names:
            with self.subTest(email=email):
                result = extract_name_from_email(email, no_company=True)
                self.assertEqual(result, expected, f"Expected {expected} but got {result} for {email}")

    def test_executive_roles(self):
        """Test that executive roles are treated as generic emails."""
        test_cases = [
            ("ceo@startup.com", "There", "Startup"),
            ("cto@techcorp.com", "There", "Techcorp"),
            ("founder@innovation.com", "There", "Innovation"),
            ("director@company.com", "There", "Company"),
        ]
        
        for email, expected_no_company, expected_default in test_cases:
            with self.subTest(email=email):
                result_no_company = extract_name_from_email(email, no_company=True)
                result_default = extract_name_from_email(email, no_company=False)
                self.assertEqual(result_no_company, expected_no_company)
                self.assertEqual(result_default, expected_default)

    def test_company_detection_function(self):
        """Test the _is_likely_company_name function directly."""
        # Should be detected as companies (using exact word matches or clear suffixes)
        company_names = [
            "SoftwareCompany",  # Contains "software" + "company"
            "TechCorporation",  # Contains "tech" + "corporation"
            "DataSystems",      # Contains "data" + "systems"
            "IBM",              # All uppercase
            "NASA",             # All uppercase
        ]
        
        for name in company_names:
            with self.subTest(name=name):
                result = _is_likely_company_name(name)
                self.assertTrue(result, f"{name} should be detected as company")

        # Should NOT be detected as companies (person names)
        person_names = [
            "Francisco",
            "Marco",
            "Disco", 
            "Nicole",
            "Datapoint",
            "John",
            "Maria",
        ]
        
        for name in person_names:
            with self.subTest(name=name):
                result = _is_likely_company_name(name)
                self.assertFalse(result, f"{name} should NOT be detected as company")

    def test_international_names(self):
        """Test that international names are handled correctly."""
        test_cases = [
            ("rajesh@company.com", "Rajesh"),
            ("priya.sharma@tech.com", "Priya Sharma"),
            ("ahmed.hassan@startup.com", "Ahmed Hassan"),
            ("li.wei@corp.com", "Li Wei"),
            ("maria.garcia@consulting.com", "Maria Garcia"),
        ]
        
        for email, expected in test_cases:
            with self.subTest(email=email):
                result = extract_name_from_email(email, no_company=True)
                self.assertEqual(result, expected)

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        test_cases = [
            ("", "there"),  # Empty email - function returns lowercase
            ("invalid", "there"),  # No @ symbol - function returns lowercase
            ("@company.com", "There"),  # Empty local part - should use fallback
            ("test@", "Test"),  # Empty domain - extracts from local part
        ]

        for email, expected in test_cases:
            with self.subTest(email=email):
                result = extract_name_from_email(email, no_company=True)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
