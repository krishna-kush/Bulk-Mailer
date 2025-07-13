
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

import itertools

class SenderManager:
    """Manages sender accounts and provides methods for sender rotation and duplication."""

    def __init__(self, senders, strategy):
        self.senders = senders
        self.strategy = strategy
        self.sender_iterator = itertools.cycle(self.senders)

    def get_next_sender(self):
        """Returns the next sender based on the rotation strategy."""
        if self.strategy == "rotate_email":
            return next(self.sender_iterator)
        elif self.strategy == "duplicate_send":
            # For duplicate_send, we iterate through all senders for each recipient,
            # but this method is called per recipient, so it will always return the current sender
            # in the iteration. The outer loop (in main.py) will handle iterating through all senders.
            pass # This logic will be handled externally
        return None

    def record_sent(self, sender_email):
        """Records that an email has been sent by a specific sender."""
        # This method is kept for compatibility but rate limiting is now handled by RateLimiter
        pass


