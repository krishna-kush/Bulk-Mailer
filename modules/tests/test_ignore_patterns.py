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
# Description: Test script for ignore patterns functionality in recipient manager
#
# ================================================================================

import os
import sys
import tempfile
import csv

# Add the parent directories to the path so we can import modules
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.dirname(current_dir)
mailer_dir = os.path.dirname(modules_dir)
sys.path.insert(0, mailer_dir)

from config.config_loader import ConfigLoader
from modules.recipient.recipient_manager import RecipientManager
from modules.logger.logger import AppLogger

def test_ignore_patterns():
    """Test the ignore patterns functionality."""
    
    print("🧪 Testing Ignore Patterns Functionality")
    print("=" * 50)
    
    # Create a temporary CSV file with test emails
    test_emails = [
        "john.doe@company.com",
        "test@example.com",
        "noreply@business.com", 
        "admin@testdomain.com",
        "valid@legitimate.com",
        "demo@demo.com",
        "support@gmail.com",
        "info@realcompany.com"
    ]
    
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_csv:
        writer = csv.writer(temp_csv)
        for email in test_emails:
            writer.writerow([email])
        temp_csv_path = temp_csv.name
    
    try:
        # Test different ignore patterns
        test_cases = [
            {
                "name": "No ignore patterns",
                "patterns": [],
                "expected_count": 8
            },
            {
                "name": "Ignore example domains",
                "patterns": ["*@example.com", "*@demo.com"],
                "expected_count": 6
            },
            {
                "name": "Ignore role-based emails",
                "patterns": ["noreply*", "admin*", "support*"],
                "expected_count": 5
            },
            {
                "name": "Ignore test and demo patterns",
                "patterns": ["test*", "demo*", "*@demo.*"],
                "expected_count": 6
            },
            {
                "name": "Ignore Gmail domain",
                "patterns": ["*@gmail.com"],
                "expected_count": 7
            },
            {
                "name": "Complex ignore patterns",
                "patterns": ["*@example.*", "*@demo.*", "noreply*", "admin*", "test*", "*@gmail.com"],
                "expected_count": 3
            }
        ]
        
        # Initialize logger
        logger = AppLogger(
            base_dir=mailer_dir,
            config_path="config/config.ini"
        ).get_logger()
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['name']}")
            print(f"   Patterns: {test_case['patterns']}")
            
            # Create config with ignore patterns
            config_settings = {
                'recipients_from': 'csv',
                'recipients_path': temp_csv_path,
                'db_table': '',
                'db_email_column': 'email',
                'db_id_column': 'id',
                'filter_columns': {},
                'ignore_patterns': test_case['patterns']
            }
            
            # Create recipient manager
            recipient_manager = RecipientManager(config_settings, mailer_dir, logger)
            
            # Get recipients
            recipients = recipient_manager.get_recipients()
            
            # Check results
            actual_count = len(recipients)
            expected_count = test_case['expected_count']
            
            print(f"   Expected: {expected_count} emails")
            print(f"   Actual:   {actual_count} emails")
            
            if actual_count == expected_count:
                print("   ✅ PASSED")
            else:
                print("   ❌ FAILED")
                print(f"   📧 Loaded emails: {[r['email'] for r in recipients]}")
            
        print(f"\n🧹 Cleaning up temporary file: {temp_csv_path}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_csv_path):
            os.unlink(temp_csv_path)
    
    print("\n✨ Ignore patterns testing completed!")

if __name__ == "__main__":
    test_ignore_patterns()
