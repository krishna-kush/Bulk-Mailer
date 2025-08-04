# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: File-based CAPTCHA management system that uses temporary files
#              for user input instead of blocking terminal input
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
import threading
from typing import Dict, Any, Optional
from datetime import datetime

class FileCaptchaManager:
    """
    File-based CAPTCHA management system that creates temporary files for user input
    instead of blocking terminal input, allowing multiple concurrent CAPTCHAs.
    """
    
    def __init__(self, logger, temp_dir: str = "captcha_temp"):
        """
        Initialize the file-based CAPTCHA manager.
        
        Args:
            logger: Logger instance
            temp_dir: Directory to store temporary CAPTCHA files
        """
        self.logger = logger
        self.temp_dir = temp_dir
        self.active_captchas = {}  # email -> file_path
        self.lock = threading.Lock()
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Clean up any existing temp files on startup
        self._cleanup_temp_files()
        
        self.logger.info(f"📁 File-based CAPTCHA manager initialized - temp dir: {self.temp_dir}")
    
    def request_captcha_verification(self, email: str, provider: str, browser_title: str,
                                   browser_url: str, detection_method: str) -> bool:
        """
        Request CAPTCHA verification using smart handling:
        - Single browser with captcha: Terminal input (simple)
        - Multiple browsers with captcha: File-based input for ALL (advanced)

        Args:
            email: Email account requiring verification
            provider: Email provider (yahoo, protonmail, etc.)
            browser_title: Browser window title for identification
            browser_url: Browser URL for identification
            detection_method: How the CAPTCHA was detected

        Returns:
            bool: True if verification completed successfully
        """
        self.logger.info(f"🚀 CAPTCHA verification request started for {email}")
        self.logger.debug(f"🔧 Request details - Provider: {provider}, Detection: {detection_method}")

        # Check if this is the first/only CAPTCHA or if there are multiple
        self.logger.debug(f"🔒 Acquiring lock for CAPTCHA count check...")
        with self.lock:
            self.logger.debug(f"🔓 Lock acquired for CAPTCHA count check")
            # Check existing active captchas BEFORE adding current one
            existing_captcha_count = len(self.active_captchas)
            existing_accounts = list(self.active_captchas.keys())

            self.logger.debug(f"📊 Current state - Existing: {existing_captcha_count}, Accounts: {existing_accounts}")

            # Prevent duplicate entries for same email
            if email in self.active_captchas:
                self.logger.warning(f"⚠️ CAPTCHA already active for {email}, skipping duplicate request")
                return False

            # Add this account to active list to track concurrent CAPTCHAs
            self.logger.debug(f"➕ Adding {email} to active CAPTCHA list")
            self.active_captchas[email] = "PENDING"
            total_captcha_count = len(self.active_captchas)
            self.logger.debug(f"✅ Added {email} to active list, new count: {total_captcha_count}")
        # Lock is released here - IMPORTANT!

        self.logger.debug(f"🔓 Lock released after CAPTCHA count check")
        self.logger.debug(f"🔍 CAPTCHA count check: {existing_captcha_count} existing + 1 current = {total_captcha_count} total active CAPTCHAs")
        self.logger.debug(f"🔍 Active CAPTCHAs: {list(self.active_captchas.keys())}")

        # SIMPLIFIED: Always use file-based CAPTCHA for multi-browser setup
        self.logger.info(f"🎯 Using file-based CAPTCHA system for {email} (total active: {total_captcha_count})")

        self.logger.debug(f"🔧 Calling _handle_multiple_captcha_file for {email}")
        result = self._handle_multiple_captcha_file(email, provider, browser_title, browser_url, detection_method)
        self.logger.debug(f"🔧 _handle_multiple_captcha_file returned {result} for {email}")
        return result
    def _handle_single_captcha_terminal(self, email: str, provider: str, browser_title: str,
                                       browser_url: str, detection_method: str) -> bool:
        """
        Handle single CAPTCHA using terminal input with interruption support.
        Can be interrupted if multiple CAPTCHAs are detected.

        Args:
            email: Email account requiring verification
            provider: Email provider
            browser_title: Browser window title
            browser_url: Browser URL
            detection_method: CAPTCHA detection method

        Returns:
            bool: True if verification completed successfully
        """
        try:
            self.logger.warning("🤖 CAPTCHA/Verification prompt detected!")
            self.logger.warning(f"🔍 Detection method: {detection_method}")
            self.logger.warning("⏳ Please complete the verification manually in the browser...")

            # Show detailed prompt to user
            print("\n" + "="*80)
            print("🤖 VERIFICATION REQUIRED - SPECIFIC BROWSER WINDOW")
            print("="*80)
            print(f"📧 Account: {email}")
            print(f"🏢 Provider: {provider.upper()}")
            print(f"🌐 Browser: {browser_title}")
            print(f"🔗 URL: {browser_url}")
            print(f"🔍 Detection: {detection_method}")
            print("="*80)
            print("A verification/CAPTCHA prompt has been detected in the browser window above.")
            print("Please:")
            print("1. Find the browser window with the matching title/URL")
            print("2. Complete the verification/CAPTCHA manually")
            print("3. Press ENTER below ONLY after completing THIS specific verification")
            print("="*80)

            # Check periodically if we've been converted to file-based mode
            check_interval = 1  # seconds
            max_wait_time = 600  # 10 minutes
            checks_done = 0
            max_checks = max_wait_time // check_interval

            print(f"⏳ Waiting for verification completion for {email}...")
            print("   (Press ENTER after completing CAPTCHA, or system will auto-switch to file mode if multiple CAPTCHAs detected)")

            # Use threading to handle input and checking simultaneously
            import threading
            import queue

            input_queue = queue.Queue()
            input_received = threading.Event()

            def get_input():
                try:
                    input()  # Wait for user input
                    input_queue.put("DONE")
                    input_received.set()
                except:
                    pass

            # Start input thread
            input_thread = threading.Thread(target=get_input, daemon=True)
            input_thread.start()

            while checks_done < max_checks:
                # Check if we've been converted to file-based mode
                with self.lock:
                    if email in self.active_captchas and self.active_captchas[email] != "PENDING":
                        # We've been converted to file-based mode
                        file_path = self.active_captchas[email]
                        self.logger.warning(f"🔄 Account {email} converted to file-based mode: {file_path}")
                        print(f"\n🔄 Multiple CAPTCHAs detected! Switching to file-based mode.")
                        print(f"📁 Please check file: {file_path}")
                        print("   Complete the CAPTCHA and write 'DONE' in the file.")

                        # Now wait for file input instead
                        return self._wait_for_file_input(file_path, email)

                # Check if user pressed enter
                if input_received.is_set():
                    self.logger.info(f"✅ User indicated verification completed for {email}")
                    return True

                time.sleep(check_interval)
                checks_done += 1

            # Timeout reached
            self.logger.error(f"⏰ Terminal CAPTCHA verification timeout for {email} after {max_wait_time//60} minutes")
            return False

        except Exception as e:
            self.logger.error(f"Error in single CAPTCHA handling for {email}: {e}")
            return False

    def _handle_multiple_captcha_file(self, email: str, provider: str, browser_title: str,
                                    browser_url: str, detection_method: str) -> bool:
        """
        Handle multiple CAPTCHAs using file-based input system.

        Args:
            email: Email account requiring verification
            provider: Email provider
            browser_title: Browser window title
            browser_url: Browser URL
            detection_method: CAPTCHA detection method

        Returns:
            bool: True if verification completed successfully
        """
        self.logger.info(f"🚀 Starting multiple CAPTCHA file handling for {email}")

        # Create unique temp file for this account
        self.logger.debug(f"🔧 Creating temp file path for {email}")
        safe_email = email.replace('@', '_at_').replace('.', '_dot_')

        # Add microseconds to timestamp to avoid collisions
        import time
        timestamp = datetime.now().strftime("%H%M%S") + f"_{int(time.time() * 1000000) % 1000000:06d}"
        temp_file = os.path.join(self.temp_dir, f"captcha_{safe_email}_{timestamp}.txt")
        self.logger.debug(f"📁 Temp file path created: {temp_file}")

        # Small delay to avoid race conditions
        time.sleep(0.01)  # 10ms delay

        # Store active CAPTCHA info (quick lock for dictionary update only)
        self.logger.debug(f"🔒 Acquiring lock to update active CAPTCHA info for {email}")
        with self.lock:
            self.active_captchas[email] = temp_file
        self.logger.debug(f"✅ Updated active_captchas[{email}] = {temp_file} (lock released)")

        try:
            # Create temp file with instructions
            self.logger.debug(f"🔧 Creating CAPTCHA file for {email}: {temp_file}")
            self._create_captcha_file(temp_file, email, provider, browser_title, browser_url, detection_method)
            self.logger.debug(f"✅ CAPTCHA file created successfully for {email}")

            self.logger.warning(f"🤖 Multiple CAPTCHAs detected - using file-based system")
            self.logger.warning(f"📁 Created CAPTCHA file for {email}: {temp_file}")
            self.logger.warning(f"🔄 Browser automation paused for {email} - waiting for user input in file")

            # Wait for user input in file
            self.logger.debug(f"🔧 Starting file monitoring for {email}")
            success = self._wait_for_file_input(temp_file, email)
            self.logger.debug(f"🔧 File monitoring completed for {email}, success: {success}")

            return success

        except Exception as e:
            self.logger.error(f"❌ Error in multiple CAPTCHA handling for {email}: {e}")
            self.logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return False

        finally:
            # Cleanup with better error handling
            try:
                with self.lock:
                    if email in self.active_captchas:
                        del self.active_captchas[email]
                        self.logger.debug(f"🧹 Removed {email} from active CAPTCHA list")
            except Exception as e:
                self.logger.error(f"Error cleaning up active captcha list for {email}: {e}")

            # Delete temp file
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    self.logger.info(f"🗑️  Deleted CAPTCHA file: {temp_file}")
            except Exception as e:
                self.logger.warning(f"Failed to delete temp file {temp_file}: {e}")

    def _create_file_for_existing_account(self, email: str):
        """
        Create a CAPTCHA file for an account that was already using terminal input.
        This is called when switching from single to multiple CAPTCHA mode.

        Args:
            email: Email account that needs a file created
        """
        self.logger.info(f"🚀 Creating file for existing account: {email}")

        # Create unique temp file for this account
        self.logger.debug(f"🔧 Creating temp file path for existing account {email}")
        safe_email = email.replace('@', '_at_').replace('.', '_dot_')
        timestamp = datetime.now().strftime("%H%M%S")
        temp_file = os.path.join(self.temp_dir, f"captcha_{safe_email}_{timestamp}.txt")
        self.logger.debug(f"📁 Temp file path for existing account: {temp_file}")

        # Update active CAPTCHA info (quick lock for dictionary update only)
        with self.lock:
            self.active_captchas[email] = temp_file
        self.logger.debug(f"✅ Updated active_captchas[{email}] = {temp_file} for existing account")

        # Create temp file with generic instructions since we don't have original details
        self.logger.debug(f"🔧 Creating CAPTCHA file for existing account {email}")
        self._create_captcha_file(
            temp_file,
            email,
            "UNKNOWN",
            "Browser window for " + email,
            "Check your browser window",
            "Multiple CAPTCHA mode conversion"
        )
        self.logger.debug(f"✅ CAPTCHA file created for existing account {email}")

        self.logger.warning(f"📁 Created CAPTCHA file for existing account {email}: {temp_file}")
        self.logger.warning(f"🔄 Account {email} switched from terminal to file-based input")

    def _create_captcha_file(self, file_path: str, email: str, provider: str,
                           browser_title: str, browser_url: str, detection_method: str):
        """
        Create temporary file with CAPTCHA instructions for user.
        
        Args:
            file_path: Path to temporary file
            email: Email account
            provider: Email provider
            browser_title: Browser window title
            browser_url: Browser URL
            detection_method: CAPTCHA detection method
        """
        instructions = f"""
================================================================================
🤖 CAPTCHA VERIFICATION REQUIRED
================================================================================
📧 Account: {email}
🏢 Provider: {provider.upper()}
🌐 Browser Window: {browser_title}
🔗 URL: {browser_url}
🔍 Detection Method: {detection_method}
⏰ Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

📋 INSTRUCTIONS:
1. Find the browser window with the title/URL shown above
2. Complete the CAPTCHA/verification in that browser window
3. After completing the CAPTCHA, write "DONE" in this file and save it
4. The system will automatically detect your input and continue processing

⚠️  IMPORTANT:
- Do NOT delete this file
- Write "DONE" (without quotes) on a new line
- Save the file after writing
- The browser automation will resume automatically

================================================================================
🎯 Write "DONE" below this line after completing CAPTCHA:

"""
        
        try:
            # Ensure temp directory exists
            self.logger.debug(f"🔧 Ensuring temp directory exists: {os.path.dirname(file_path)}")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            self.logger.debug(f"✅ Temp directory confirmed: {os.path.dirname(file_path)}")

            # Check if file already exists (shouldn't happen but let's be safe)
            if os.path.exists(file_path):
                self.logger.warning(f"⚠️ File already exists, will overwrite: {file_path}")

            self.logger.debug(f"🔧 Writing CAPTCHA instructions to file: {file_path}")
            self.logger.debug(f"📝 Instructions length: {len(instructions)} characters")

            # Write with explicit flushing
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(instructions)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force write to disk

            self.logger.info(f"📝 Created CAPTCHA instruction file: {file_path}")
            self.logger.debug(f"✅ File write completed successfully: {file_path}")

            # Verify file was created and has content
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                self.logger.debug(f"✅ File verification - Size: {file_size} bytes")
            else:
                self.logger.error(f"❌ File verification failed - File does not exist: {file_path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to create CAPTCHA file {file_path}: {e}")
            self.logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")

            # Additional debugging info
            self.logger.error(f"❌ File path: {file_path}")
            self.logger.error(f"❌ Directory exists: {os.path.exists(os.path.dirname(file_path))}")
            self.logger.error(f"❌ Directory writable: {os.access(os.path.dirname(file_path), os.W_OK)}")
            raise
    
    def _wait_for_file_input(self, file_path: str, email: str,
                           check_interval: int = 5, max_wait_minutes: int = 10) -> bool:
        """
        Wait for user input in the temporary file.

        Args:
            file_path: Path to temporary file
            email: Email account
            check_interval: How often to check file (seconds)
            max_wait_minutes: Maximum wait time (minutes)

        Returns:
            bool: True if user input detected, False if timeout
        """
        self.logger.info(f"🚀 Starting file input monitoring for {email}")
        self.logger.debug(f"🔧 File monitoring parameters - File: {file_path}, Interval: {check_interval}s, Max: {max_wait_minutes}m")

        max_checks = (max_wait_minutes * 60) // check_interval
        checks_done = 0

        self.logger.info(f"⏳ Waiting for user input in file: {file_path}")
        self.logger.debug(f"📊 Will check file {max_checks} times with {check_interval}s intervals")

        self.logger.debug(f"🔄 Starting file monitoring loop for {email}")
        while checks_done < max_checks:
            self.logger.debug(f"🔄 File check iteration {checks_done + 1}/{max_checks} for {email}")
            try:
                # Skip the active check to avoid deadlock - assume still active
                self.logger.debug(f"✅ Continuing monitoring for {email} (skipping active check to avoid deadlock)")

                # Check if file still exists (no lock needed for file system check)
                self.logger.debug(f"📁 Checking if file exists: {file_path}")
                if not os.path.exists(file_path):
                    self.logger.warning(f"⚠️  CAPTCHA file deleted externally: {file_path}")
                    # Quick lock only for dictionary cleanup
                    with self.lock:
                        if email in self.active_captchas:
                            del self.active_captchas[email]
                    self.logger.debug(f"🧹 Removed {email} from active list due to deleted file")
                    return False
                self.logger.debug(f"✅ File exists: {file_path}")

                # Read file content with better error handling
                self.logger.debug(f"📖 About to read file content: {file_path}")
                try:
                    self.logger.debug(f"📖 Opening file for reading: {file_path}")
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.logger.debug(f"📖 File opened successfully, reading content...")
                        content = f.read().strip()
                        self.logger.debug(f"📖 File read operation completed")
                    self.logger.debug(f"✅ File read successfully, content length: {len(content)} chars")
                    self.logger.debug(f"📄 File content preview (last 50 chars): {repr(content[-50:])}")
                except (IOError, OSError, UnicodeDecodeError) as e:
                    self.logger.error(f"❌ Failed to read CAPTCHA file {file_path}: {e}")
                    self.logger.error(f"❌ File read error details: {type(e).__name__}: {str(e)}")
                    self.logger.debug(f"😴 Sleeping {check_interval}s after file read error for {email}")
                    time.sleep(check_interval)
                    checks_done += 1
                    self.logger.debug(f"⏰ Continuing after file read error, check {checks_done}/{max_checks} for {email}")
                    continue
                except Exception as e:
                    self.logger.error(f"❌ Unexpected error reading file {file_path}: {e}")
                    self.logger.error(f"❌ Unexpected error details: {type(e).__name__}: {str(e)}")
                    import traceback
                    self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
                    self.logger.debug(f"😴 Sleeping {check_interval}s after unexpected file error for {email}")
                    time.sleep(check_interval)
                    checks_done += 1
                    self.logger.debug(f"⏰ Continuing after unexpected file error, check {checks_done}/{max_checks} for {email}")
                    continue

                # Check for user input
                self.logger.debug(f"🔍 About to check user input for {email}")
                user_input_detected = self._check_user_input(content)
                self.logger.debug(f"🔍 User input check completed for {email}: {user_input_detected}")

                if user_input_detected:
                    self.logger.info(f"✅ User input detected for {email} - CAPTCHA completed!")
                    return True

                self.logger.debug(f"❌ No user input detected for {email}, continuing loop")

                # Log waiting status (but not too frequently to avoid spam)
                if checks_done % 2 == 0:  # Log every 10 seconds instead of every 5
                    elapsed_minutes = (checks_done * check_interval) // 60
                    elapsed_seconds = (checks_done * check_interval) % 60
                    self.logger.warning(f"⏳ Still waiting for CAPTCHA completion for {email} "
                                      f"(elapsed: {elapsed_minutes}m {elapsed_seconds}s)")

                    # Show current active CAPTCHAs (with thread safety)
                    try:
                        self.logger.debug(f"📊 Logging active CAPTCHAs for iteration {checks_done + 1}")
                        self._log_active_captchas()
                    except Exception as log_error:
                        self.logger.error(f"Error logging active captchas: {log_error}")

                self.logger.debug(f"😴 About to sleep for {check_interval}s before next check for {email}")
                time.sleep(check_interval)
                self.logger.debug(f"😴 Sleep completed for {email}")
                checks_done += 1
                self.logger.debug(f"⏰ Completed check {checks_done}/{max_checks} for {email}")
                self.logger.debug(f"🔄 About to start next iteration for {email}")

            except Exception as e:
                self.logger.error(f"❌ Unexpected error in file monitoring for {email}: {e}")
                self.logger.error(f"❌ Error details: {type(e).__name__}: {str(e)}")
                import traceback
                self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
                self.logger.debug(f"😴 Sleeping {check_interval}s after error for {email}")
                time.sleep(check_interval)
                checks_done += 1
                self.logger.debug(f"⏰ Continuing after error, check {checks_done}/{max_checks} for {email}")

        # Timeout reached
        self.logger.error(f"⏰ CAPTCHA verification timeout for {email} after {max_wait_minutes} minutes")
        self.logger.debug(f"❌ File monitoring loop ended for {email} due to timeout")
        return False
    
    def _check_user_input(self, content: str) -> bool:
        """
        Check if user has provided valid input in the file.

        Args:
            content: File content

        Returns:
            bool: True if valid input found
        """
        self.logger.debug(f"🔍 Checking user input in content (length: {len(content)})")
        self.logger.debug(f"🔍 Content preview: {repr(content[:100])}...")

        # Look for "DONE" in the content (case insensitive)
        lines = content.lower().split('\n')
        self.logger.debug(f"🔍 Split content into {len(lines)} lines")

        for i, line in enumerate(lines):
            line = line.strip()
            self.logger.debug(f"🔍 Checking line {i+1}: {repr(line)}")
            if line == 'done' or line == '"done"' or line == "'done'":
                self.logger.debug(f"✅ Found DONE on line {i+1}: {repr(line)}")
                return True

        self.logger.debug(f"❌ No DONE found in {len(lines)} lines")
        return False
    
    def _log_active_captchas(self):
        """Log current active CAPTCHA verifications."""
        with self.lock:
            if self.active_captchas:
                active_count = len(self.active_captchas)
                active_emails = list(self.active_captchas.keys())
                self.logger.info(f"📊 Active CAPTCHA verifications: {active_count}")
                for email in active_emails:
                    self.logger.info(f"   • {email}")
    
    def _cleanup_temp_files(self):
        """Clean up any existing temporary CAPTCHA files."""
        try:
            if os.path.exists(self.temp_dir):
                for filename in os.listdir(self.temp_dir):
                    if filename.startswith('captcha_') and filename.endswith('.txt'):
                        file_path = os.path.join(self.temp_dir, filename)
                        os.remove(file_path)
                        self.logger.debug(f"Cleaned up old CAPTCHA file: {file_path}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of active CAPTCHA verifications.
        
        Returns:
            Dict containing status information
        """
        with self.lock:
            return {
                'active_count': len(self.active_captchas),
                'active_accounts': list(self.active_captchas.keys()),
                'temp_dir': self.temp_dir,
                'temp_files': list(self.active_captchas.values())
            }
    
    def force_complete_captcha(self, email: str) -> bool:
        """
        Force complete CAPTCHA for specific account (for testing/emergency).
        
        Args:
            email: Email account to force complete
            
        Returns:
            bool: True if account was found and completed
        """
        with self.lock:
            if email in self.active_captchas:
                file_path = self.active_captchas[email]
                try:
                    # Append "DONE" to the file
                    with open(file_path, 'a', encoding='utf-8') as f:
                        f.write('\nDONE\n')
                    self.logger.info(f"🔧 Force completed CAPTCHA for {email}")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to force complete CAPTCHA for {email}: {e}")
                    return False
            else:
                self.logger.warning(f"No active CAPTCHA found for {email}")
                return False

# Global file CAPTCHA manager instance
_file_captcha_manager = None
_manager_lock = threading.Lock()

def get_file_captcha_manager(logger=None, temp_dir: str = "captcha_temp"):
    """
    Get the global file CAPTCHA manager instance (singleton pattern).

    Args:
        logger: Logger instance (required for first call)
        temp_dir: Directory for temporary files

    Returns:
        FileCaptchaManager instance
    """
    global _file_captcha_manager

    with _manager_lock:
        if _file_captcha_manager is None:
            if logger is None:
                raise ValueError("Logger is required for first initialization of file CAPTCHA manager")
            _file_captcha_manager = FileCaptchaManager(logger, temp_dir)
            logger.info("🔧 Created global CAPTCHA manager singleton")
        else:
            logger.debug("🔧 Using existing global CAPTCHA manager singleton")

        return _file_captcha_manager
