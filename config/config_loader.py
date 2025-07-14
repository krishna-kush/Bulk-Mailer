
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

import configparser
import os

class ConfigLoader:
    """Manages application configuration from config.ini."""

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(self.base_dir, "config", "config.ini")
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            self._create_default_config()
        self.config.read(self.config_path)

        # Validate essential settings after loading
        self._validate_essential_settings()

    def _create_default_config(self):
        """Creates a default config.ini if it doesn't exist."""
        self.config["SMTP"] = {
            "host": "smtp.example.com",
            "port": "587",
            "use_tls": "True"
        }
        # SMTP_CONFIGS section intentionally omitted - must be configured by user
        # This ensures validation will catch missing SMTP configuration
        # SENDERS section intentionally omitted - must be configured by user
        # This ensures validation will catch missing sender configuration
        self.config["RATE_LIMITER"] = {
            "global_limit": "0"
        }
        self.config["RETRY_SETTINGS"] = {
            "max_retries_per_sender": "3",
            "retry_delay": "5",
            "max_retries_per_recipient": "5"
        }
        self.config["FAILURE_TRACKING"] = {
            "max_failures_before_block": "5",
            "cooldown_period": "300",
            "failure_window": "3600",
            "reset_failures_after": "7200"
        }
        self.config["FALLBACK_SETTINGS"] = {
            "enable_fallback": "True",
            "max_fallback_attempts": "3"
        }
        self.config["RETRY_STRATEGY"] = {
            "max_retries_per_sender": "3",
            "retry_delay_seconds": "5",
            "enable_fallback_senders": "True",
            "max_fallback_attempts": "2",
            "track_sender_failures": "True",
            "failure_threshold": "5",
            "cooldown_period_minutes": "30",
            "reset_failure_count_hours": "24"
        }
        self.config["APPLICATION"] = {
            "sender_strategy": "rotate_email" # rotate_email, duplicate_send
        }
        self.config["LOGGING"] = {
            "console_level": "INFO",
            "file_levels": "DEBUG,INFO,WARNING,ERROR,CRITICAL",
            "max_log_files_to_keep": "10",
            "log_dir": "logs"
        }
        self.config["RECIPIENTS"] = {
            "recipients_from": "csv",
            "recipients_path": "recipients.csv",
            "db_table": "",
            "db_email_column": "email",
            "db_id_column": "id",
            "filter_columns": ""
        }
        self.config["EMAIL_CONTENT"] = {
            "subject": "Test Subject",
            "body_html_file": "email_template.html",
            "attachment_dir": "attachments"
        }
        # EMAIL_PERSONALIZATION section intentionally omitted - optional feature
        # Users can add this section if they want personalization
        # EMAIL_ATTACHMENTS section intentionally omitted - optional feature
        # Users can add this section if they want CID attachments
        with open(self.config_path, "w") as configfile:
            self.config.write(configfile)

    def _validate_essential_settings(self):
        """Validate essential settings and quit if missing critical configuration."""
        errors = []

        # Check for SENDERS section
        if not self.config.has_section("SENDERS"):
            errors.append("❌ SENDERS section is missing from config.ini")
        else:
            # Check if we have at least one sender configured
            senders = self.get_senders()
            if not senders:
                errors.append("❌ No senders configured in SENDERS section")
            else:
                # Validate each sender has required fields
                for i, sender in enumerate(senders, 1):
                    if not sender.get('email'):
                        errors.append(f"❌ Sender {i}: Missing email address")
                    if not sender.get('password'):
                        errors.append(f"❌ Sender {i}: Missing password")

        # Check for SMTP_CONFIGS section (required for multiple SMTP providers)
        if not self.config.has_section("SMTP_CONFIGS"):
            errors.append("❌ SMTP_CONFIGS section is missing from config.ini")
        else:
            # Check if we have at least basic SMTP configurations
            try:
                smtp_configs = self.get_smtp_configs()
                if not smtp_configs or len(smtp_configs) <= 1:  # Only default config
                    errors.append("❌ No additional SMTP configurations found in SMTP_CONFIGS section")
            except Exception as e:
                errors.append(f"❌ Error reading SMTP_CONFIGS: {e}")
                for smtp_id, smtp_config in smtp_configs.items():
                    if not smtp_config.get('host'):
                        errors.append(f"❌ SMTP '{smtp_id}': Missing host")
                    if not smtp_config.get('port'):
                        errors.append(f"❌ SMTP '{smtp_id}': Missing port")

        # Check for EMAIL_CONTENT section
        if not self.config.has_section("EMAIL_CONTENT"):
            errors.append("❌ EMAIL_CONTENT section is missing from config.ini")
        else:
            subject = self.get("EMAIL_CONTENT", "subject")
            if not subject:
                errors.append("❌ EMAIL_CONTENT: Missing subject")

            body_html_file = self.get("EMAIL_CONTENT", "body_html_file")
            if not body_html_file:
                errors.append("❌ EMAIL_CONTENT: Missing body_html_file")
            else:
                # Check if template file exists
                template_path = os.path.join(self.base_dir, body_html_file)
                if not os.path.exists(template_path):
                    errors.append(f"❌ EMAIL_CONTENT: Template file not found: {template_path}")

        # Check for RECIPIENTS section
        if not self.config.has_section("RECIPIENTS"):
            errors.append("❌ RECIPIENTS section is missing from config.ini")
        else:
            recipients_from = self.get("RECIPIENTS", "recipients_from")
            if not recipients_from:
                errors.append("❌ RECIPIENTS: Missing recipients_from setting")

            recipients_path = self.get("RECIPIENTS", "recipients_path")
            if not recipients_path:
                errors.append("❌ RECIPIENTS: Missing recipients_path setting")

        # If we have errors, print them and quit
        if errors:
            print("\n" + "="*60)
            print("🚨 CONFIGURATION VALIDATION FAILED")
            print("="*60)
            print("The following essential settings are missing or invalid:")
            print()
            for error in errors:
                print(f"  {error}")
            print()
            print("💡 Please check your config.ini file and ensure all required")
            print("   settings are properly configured.")
            print()
            print("📖 Refer to config.example.ini for detailed configuration examples.")
            print("="*60)
            exit(1)

        # Success message
        print("✅ Configuration validation passed - all essential settings found")

    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)

    def getboolean(self, section, option, fallback=False):
        return self.config.getboolean(section, option, fallback=fallback)

    def getint(self, section, option, fallback=0):
        return self.config.getint(section, option, fallback=fallback)

    def get_log_dir(self):
        log_dir = self.get("LOGGING", "log_dir", fallback="logs")
        if not os.path.isabs(log_dir):
            log_dir = os.path.join(self.base_dir, log_dir)
        return log_dir

    def get_senders(self):
        senders = []
        for key, value in self.config.items("SENDERS"):
            if key.endswith("_email"):
                prefix = key.replace("_email", "")
                email = value
                password = self.config.get("SENDERS", f"{prefix}_password")
                smtp_id = self.config.get("SENDERS", f"{prefix}_smtp", fallback="default")
                # Parse rate limiting settings for this sender
                total_limit_per_run = self.config.getint("SENDERS", f"{prefix}_total_limit_per_run", fallback=0)
                limit_per_min = self.config.getint("SENDERS", f"{prefix}_limit_per_min", fallback=0)
                limit_per_hour = self.config.getint("SENDERS", f"{prefix}_limit_per_hour", fallback=0)
                per_run_gap = self.config.getint("SENDERS", f"{prefix}_per_run_gap", fallback=0)
                per_run_gap_randomizer = self.config.getint("SENDERS", f"{prefix}_per_run_gap_randomizer", fallback=0)

                senders.append({
                    "email": email,
                    "password": password,
                    "smtp_id": smtp_id,
                    "total_limit_per_run": total_limit_per_run,
                    "limit_per_min": limit_per_min,
                    "limit_per_hour": limit_per_hour,
                    "per_run_gap": per_run_gap,
                    "per_run_gap_randomizer": per_run_gap_randomizer
                })
        return senders

    def get_smtp_settings(self):
        return {
            "host": self.get("SMTP", "host"),
            "port": self.getint("SMTP", "port"),
            "use_tls": self.getboolean("SMTP", "use_tls")
        }

    def get_smtp_configs(self):
        """Returns all SMTP configurations."""
        smtp_configs = {}
        
        # Add default SMTP config
        smtp_configs["default"] = self.get_smtp_settings()
        
        # Parse SMTP_CONFIGS section
        if self.config.has_section("SMTP_CONFIGS"):
            # Find all unique prefixes by looking for _host keys
            prefixes = set()
            for key in self.config.options("SMTP_CONFIGS"):
                if key.endswith("_host"):
                    prefix = key.replace("_host", "")
                    prefixes.add(prefix)
            
            # Create config for each prefix using prefix as the smtp_id
            for prefix in prefixes:
                smtp_configs[prefix] = {
                    "host": self.get("SMTP_CONFIGS", f"{prefix}_host"),
                    "port": self.getint("SMTP_CONFIGS", f"{prefix}_port"),
                    "use_tls": self.getboolean("SMTP_CONFIGS", f"{prefix}_use_tls")
                }
        
        return smtp_configs

    def get_smtp_config_by_id(self, smtp_id):
        """Returns SMTP configuration for a specific ID."""
        smtp_configs = self.get_smtp_configs()
        return smtp_configs.get(smtp_id, smtp_configs.get("default"))

    def get_rate_limiter_settings(self):
        """Returns rate limiter settings."""
        return {
            "global_limit": self.getint("RATE_LIMITER", "global_limit", fallback=0)
        }

    def get_retry_settings(self):
        """Returns retry settings."""
        return {
            "max_retries_per_sender": self.getint("RETRY_SETTINGS", "max_retries_per_sender", fallback=3),
            "retry_delay": self.getint("RETRY_SETTINGS", "retry_delay", fallback=5),
            "max_retries_per_recipient": self.getint("RETRY_SETTINGS", "max_retries_per_recipient", fallback=5)
        }

    def get_failure_tracking_settings(self):
        """Returns failure tracking settings."""
        return {
            "max_failures_before_block": self.getint("FAILURE_TRACKING", "max_failures_before_block", fallback=5),
            "cooldown_period": self.getint("FAILURE_TRACKING", "cooldown_period", fallback=300),
            "failure_window": self.getint("FAILURE_TRACKING", "failure_window", fallback=3600),
            "reset_failures_after": self.getint("FAILURE_TRACKING", "reset_failures_after", fallback=7200)
        }

    def get_fallback_settings(self):
        """Returns fallback settings."""
        return {
            "enable_fallback": self.getboolean("FALLBACK_SETTINGS", "enable_fallback", fallback=True),
            "max_fallback_attempts": self.getint("FALLBACK_SETTINGS", "max_fallback_attempts", fallback=3)
        }

    def get_application_settings(self):
        return {
            "sender_strategy": self.get("APPLICATION", "sender_strategy")
        }

    def get_queue_management_settings(self):
        """Returns queue management settings with auto-calculated batch size."""
        max_queue_size = self.getint("QUEUE_MANAGEMENT", "max_queue_size_per_sender", fallback=30)
        num_senders = len(self.get_senders())

        # Auto-calculate batch size or allow manual override
        batch_size_config = self.get("QUEUE_MANAGEMENT", "batch_processing_size", fallback="auto")
        if batch_size_config == "auto":
            batch_size = max_queue_size * num_senders
        else:
            batch_size = int(batch_size_config)

        return {
            "max_queue_size_per_sender": max_queue_size,
            "batch_processing_size": batch_size,
            "refill_threshold": self.getint("QUEUE_MANAGEMENT", "refill_threshold", fallback=10),
            "queue_calculation_method": self.get("QUEUE_MANAGEMENT", "queue_calculation_method", fallback="smart"),
            "overflow_strategy": self.get("QUEUE_MANAGEMENT", "overflow_strategy", fallback="wait_shortest"),
            "enable_queue_balancing": self.getboolean("QUEUE_MANAGEMENT", "enable_queue_balancing", fallback=True),
            "queue_balance_interval": self.getint("QUEUE_MANAGEMENT", "queue_balance_interval", fallback=30),
            "max_wait_time_threshold": self.getint("QUEUE_MANAGEMENT", "max_wait_time_threshold", fallback=300)
        }

    def get_email_content_settings(self):
        return {
            "subject": self.get("EMAIL_CONTENT", "subject"),
            "body_html_file": self.get("EMAIL_CONTENT", "body_html_file"),
            "attachment_dir": self.get("EMAIL_CONTENT", "attachment_dir")
        }

    def get_recipients_settings(self):
        """Returns recipients settings."""
        settings = {
            "recipients_from": self.get("RECIPIENTS", "recipients_from", fallback="csv"),
            "recipients_path": self.get("RECIPIENTS", "recipients_path", fallback="recipients.csv"),
            "db_table": self.get("RECIPIENTS", "db_table", fallback=""),
            "db_email_column": self.get("RECIPIENTS", "db_email_column", fallback="email"),
            "db_id_column": self.get("RECIPIENTS", "db_id_column", fallback="id"),
            "filter_columns": self._parse_filter_columns()
        }
        return settings

    def _parse_filter_columns(self):
        """Parse filter_columns configuration into a structured format."""
        filter_string = self.get("RECIPIENTS", "filter_columns", fallback="")
        if not filter_string.strip():
            return {}
        
        filters = {}
        try:
            # Split by semicolon for multiple column filters
            for column_filter in filter_string.split(';'):
                column_filter = column_filter.strip()
                if ':' not in column_filter:
                    continue
                    
                column_name, values_str = column_filter.split(':', 1)
                column_name = column_name.strip()
                values_str = values_str.strip()
                
                # Check if it's a NOT filter
                is_not_filter = values_str.startswith('NOT:')
                if is_not_filter:
                    values_str = values_str[4:]  # Remove 'NOT:' prefix
                
                # Split values by comma and clean them
                values = [v.strip() for v in values_str.split(',') if v.strip()]
                
                filters[column_name] = {
                    'values': values,
                    'is_not_filter': is_not_filter
                }
        except Exception as e:
            # If parsing fails, return empty dict to avoid breaking the system
            print(f"Warning: Error parsing filter_columns: {e}")
            return {}
        
        return filters

    def get_email_personalization_settings(self):
        """Get email personalization configuration."""
        settings = {
            "enable_personalization": self.get("EMAIL_PERSONALIZATION", "enable_personalization", fallback="false").lower() == "true",
            "personalization_mappings": {}
        }

        # Load all personalization mappings from config
        if self.config.has_section("EMAIL_PERSONALIZATION"):
            for key, value in self.config.items("EMAIL_PERSONALIZATION"):
                if key != "enable_personalization":
                    settings["personalization_mappings"][key] = value

        return settings

    def get_email_anti_spam_settings(self):
        """Get email anti-spam configuration."""
        settings = {
            "enable_html_obfuscation": self.get("EMAIL_ANTI_SPAM", "enable_html_obfuscation", fallback="false").lower() == "true",
            "html_obfuscation_intensity": self.get("EMAIL_ANTI_SPAM", "html_obfuscation_intensity", fallback="medium"),
            "enable_manual_randomization": self.get("EMAIL_ANTI_SPAM", "enable_manual_randomization", fallback="true").lower() == "true"
        }

        return settings

    def get_email_attachments_settings(self):
        """Get email attachments configuration with CID mappings."""
        settings = {
            "attachments": {}
        }

        # Load all attachment mappings from config
        if self.config.has_section("EMAIL_ATTACHMENTS"):
            for key, value in self.config.items("EMAIL_ATTACHMENTS"):
                try:
                    # Parse format: file_path:content_id
                    if ':' in value:
                        file_path, content_id = value.split(':', 1)

                        # Convert relative paths to absolute
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(self.base_dir, file_path)

                        settings["attachments"][key] = {
                            "file_path": file_path,
                            "content_id": content_id
                        }
                    else:
                        # Invalid format, skip with warning
                        print(f"Warning: Invalid attachment format for '{key}': {value}")

                except Exception as e:
                    print(f"Warning: Error parsing attachment '{key}': {e}")

        return settings

    def get_recipients_file(self):
        return self.get("RECIPIENTS", "recipients_path")


