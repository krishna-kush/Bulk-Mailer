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
# Description: Test runner for browser automation functionality.
#              Runs unit tests and integration tests for browser automation.
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
import subprocess
import argparse

def run_unit_tests():
    """Run unit tests for browser automation."""
    print("=" * 60)
    print("RUNNING BROWSER AUTOMATION UNIT TESTS")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), "test_browser_automation.py")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running unit tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests for browser automation."""
    print("=" * 60)
    print("RUNNING BROWSER AUTOMATION INTEGRATION TESTS")
    print("=" * 60)
    
    test_file = os.path.join(os.path.dirname(__file__), "test_browser_integration.py")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    dependencies = [
        ("playwright", "pip install playwright"),
        ("playwright browsers", "playwright install")
    ]
    
    missing = []
    
    # Check playwright
    try:
        import playwright
        print("✓ Playwright installed")
    except ImportError:
        missing.append(dependencies[0])
    
    # Check if browser binaries are installed
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        try:
            browser = p.chromium.launch(headless=True)
            browser.close()
            print("✓ Playwright browser binaries installed")
        except Exception:
            missing.append(dependencies[1])
        finally:
            p.stop()
    except Exception:
        missing.append(dependencies[1])
    
    if missing:
        print("\nMissing dependencies:")
        for dep, install_cmd in missing:
            print(f"  - {dep}: {install_cmd}")
        return False
    
    print("✓ All dependencies are installed")
    return True

def main():
    """Main function to run tests."""
    parser = argparse.ArgumentParser(description="Run browser automation tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency check")
    
    args = parser.parse_args()
    
    print("BULK_MAILER - Browser Automation Test Runner")
    print("=" * 60)
    
    # Check dependencies unless skipped
    if not args.skip_deps:
        if not check_dependencies():
            print("\n❌ Dependency check failed. Please install missing dependencies.")
            sys.exit(1)
        print()
    
    success = True
    
    # Run unit tests
    if not args.integration:
        if not run_unit_tests():
            success = False
            print("❌ Unit tests failed")
        else:
            print("✅ Unit tests passed")
        print()
    
    # Run integration tests
    if not args.unit:
        print("⚠️  Integration tests require:")
        print("  1. Valid ProtonMail account with cookies saved")
        print("  2. Internet connection")
        print("  3. ProtonMail sender configured in config.ini")
        print()
        
        response = input("Do you want to run integration tests? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            if not run_integration_tests():
                success = False
                print("❌ Integration tests failed")
            else:
                print("✅ Integration tests passed")
        else:
            print("⏭️  Skipping integration tests")
        print()
    
    # Final result
    print("=" * 60)
    if success:
        print("🎉 ALL BROWSER AUTOMATION TESTS COMPLETED SUCCESSFULLY!")
        print("Browser automation is ready to use.")
    else:
        print("❌ SOME TESTS FAILED")
        print("Please check the output above for details.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
