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
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta

class RateLimiter:
    """Manages sending rates per sender to avoid exceeding limits."""

    def __init__(self, senders_data, global_limit=0, logger=None):
        self.senders_data = senders_data
        self.global_limit = global_limit
        self.logger = logger

        # Thread safety for concurrent access
        self._lock = threading.Lock()

        # Track counts and timings per sender
        self.sent_counts = defaultdict(int)  # Total sent per run for each sender
        self.sent_timestamps = defaultdict(deque)  # Timestamps for minute/hour tracking
        self.last_sent_time = defaultdict(float)  # Last sent time for gap control
        self.next_gap_time = defaultdict(float)  # Store next randomized gap for each sender
        
        # Global counter for all emails sent
        self.global_sent_count = 0
        
        # Parse rate limit settings from senders_data
        self.rate_limits = self._parse_rate_limits()
    
    def _parse_rate_limits(self):
        """Parse rate limit settings from sender configurations."""
        rate_limits = {}

        for sender in self.senders_data:
            sender_email = sender['email']
            rate_limits[sender_email] = {
                'total_limit_per_run': sender.get('total_limit_per_run', 0),
                'limit_per_min': sender.get('limit_per_min', 0),
                'limit_per_hour': sender.get('limit_per_hour', 0),
                'per_email_gap_sec': sender.get('per_email_gap_sec', 0),
                'per_email_gap_sec_randomizer': sender.get('per_email_gap_sec_randomizer', 0)
            }

        return rate_limits
    
    def can_send(self, sender_email):
        """Check if we can send an email with the given sender (including gap control)."""
        # First check basic rate limits
        if not self.can_send_ignoring_gap(sender_email):
            return False

        # Then check gap control
        return self.is_gap_satisfied(sender_email)

    def can_send_ignoring_gap(self, sender_email):
        """Check if we can send an email with the given sender (ignoring gap control)."""
        # Check global limit first (thread-safe)
        with self._lock:
            if self.global_limit > 0 and self.global_sent_count >= self.global_limit:
                if self.logger:
                    self.logger.warning(f"Global limit reached ({self.global_limit} emails). Cannot send more emails.")
                return False

        if sender_email not in self.rate_limits:
            return True

        limits = self.rate_limits[sender_email]

        # Check total limit per run
        if limits['total_limit_per_run'] > 0:
            if self.sent_counts[sender_email] >= limits['total_limit_per_run']:
                if self.logger:
                    self.logger.warning(f"Sender '{sender_email}' has reached total limit per run ({limits['total_limit_per_run']})")
                return False

        # Check per minute limit
        if limits['limit_per_min'] > 0:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)

            # Remove old timestamps
            timestamps = self.sent_timestamps[sender_email]
            while timestamps and datetime.fromtimestamp(timestamps[0]) < minute_ago:
                timestamps.popleft()

            if len(timestamps) >= limits['limit_per_min']:
                if self.logger:
                    self.logger.warning(f"Sender '{sender_email}' has reached per minute limit ({limits['limit_per_min']})")
                return False

        # Check per hour limit
        if limits['limit_per_hour'] > 0:
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)

            # Count emails sent in the last hour
            timestamps = self.sent_timestamps[sender_email]
            emails_last_hour = sum(1 for ts in timestamps if datetime.fromtimestamp(ts) >= hour_ago)

            if emails_last_hour >= limits['limit_per_hour']:
                if self.logger:
                    self.logger.warning(f"Sender '{sender_email}' has reached per hour limit ({limits['limit_per_hour']})")
                return False

        return True

    def is_gap_satisfied(self, sender_email, current_time=None):
        """Check if the gap period has been satisfied for a sender."""
        if current_time is None:
            current_time = time.time()

        if sender_email not in self.rate_limits:
            return True

        limits = self.rate_limits[sender_email]
        per_email_gap_sec = limits['per_email_gap_sec']

        if per_email_gap_sec > 0:
            time_since_last = current_time - self.last_sent_time[sender_email]
            # Use the randomized gap time if available, otherwise use base gap
            required_gap = self.next_gap_time.get(sender_email, per_email_gap_sec)
            return time_since_last >= required_gap

        return True

    def get_gap_wait_time(self, sender_email, current_time=None):
        """Get the remaining wait time for a sender's gap period."""
        if current_time is None:
            current_time = time.time()

        if sender_email not in self.rate_limits:
            return 0.0

        limits = self.rate_limits[sender_email]
        per_email_gap_sec = limits['per_email_gap_sec']

        if per_email_gap_sec > 0:
            time_since_last = current_time - self.last_sent_time[sender_email]
            # Use the randomized gap time if available, otherwise use base gap
            required_gap = self.next_gap_time.get(sender_email, per_email_gap_sec)
            if time_since_last < required_gap:
                return required_gap - time_since_last

        return 0.0
    
    def wait_if_needed(self, sender_email):
        """Wait if needed based on the gap settings for the sender."""
        wait_time = self.get_gap_wait_time(sender_email)

        if wait_time > 0:
            if self.logger:
                self.logger.debug(f"Sender '{sender_email}' gap control: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)

    def wait_with_randomized_gap(self, sender_email):
        """
        Wait for the randomized gap time after sending an email.
        This should be called after a successful email send.

        Args:
            sender_email: Email address of the sender
        """
        randomized_gap = self.get_randomized_gap_time(sender_email)

        if randomized_gap > 0:
            if self.logger:
                self.logger.debug(f"Sender '{sender_email}' randomized gap: waiting {randomized_gap:.2f} seconds")
            time.sleep(randomized_gap)

    def get_randomized_gap_time(self, sender_email):
        """
        Calculate a randomized gap time for a sender.

        Args:
            sender_email: Email address of the sender

        Returns:
            float: Randomized gap time in seconds
        """
        if sender_email not in self.rate_limits:
            return 0.0

        limits = self.rate_limits[sender_email]
        base_gap = limits['per_email_gap_sec']
        randomizer = limits['per_email_gap_sec_randomizer']

        if base_gap <= 0:
            return 0.0

        if randomizer <= 0:
            # No randomization, return base gap
            return float(base_gap)

        # Calculate randomized gap: base_gap ± randomizer
        # Use uniform distribution within the range
        min_gap = max(1.0, base_gap - randomizer)  # Ensure minimum 1 second
        max_gap = base_gap + randomizer

        randomized_gap = random.uniform(min_gap, max_gap)

        if self.logger:
            self.logger.debug(f"Sender '{sender_email}' randomized gap: {randomized_gap:.2f}s "
                            f"(base: {base_gap}s, randomizer: ±{randomizer}s, range: {min_gap:.1f}-{max_gap:.1f}s)")

        return randomized_gap

    def get_average_gap_time(self, sender_email):
        """
        Get the average gap time for a sender (used for queue calculations).

        Args:
            sender_email: Email address of the sender

        Returns:
            float: Average gap time in seconds
        """
        if sender_email not in self.rate_limits:
            return 0.0

        limits = self.rate_limits[sender_email]
        base_gap = limits['per_email_gap_sec']

        # For queue calculations, use the base gap time as the average
        # since randomization averages out to the base value over time
        return float(base_gap) if base_gap > 0 else 0.0

    def try_reserve_send_slot(self, sender_email):
        """
        Atomically check if we can send and reserve a slot if possible.
        This prevents race conditions in concurrent environments.

        Returns:
            bool: True if slot was reserved, False if limits would be exceeded
        """
        with self._lock:
            # Check global limit first
            if self.global_limit > 0 and self.global_sent_count >= self.global_limit:
                if self.logger:
                    self.logger.warning(f"Global limit reached ({self.global_limit} emails). Cannot send more emails.")
                return False

            # Check sender-specific limits
            if sender_email not in self.rate_limits:
                # No limits for this sender, reserve slot
                self.global_sent_count += 1
                return True

            sender_limits = self.rate_limits[sender_email]

            # Check total limit per run
            if sender_limits['total_limit_per_run'] > 0:
                if self.sent_counts[sender_email] >= sender_limits['total_limit_per_run']:
                    if self.logger:
                        self.logger.warning(f"Sender '{sender_email}' has reached total limit per run ({sender_limits['total_limit_per_run']})")
                    return False

            # All checks passed, reserve the slot
            self.global_sent_count += 1
            self.sent_counts[sender_email] += 1
            return True

    def record_sent(self, sender_email):
        """
        Record that an email was sent using the specified sender.
        Note: If using try_reserve_send_slot(), counters are already incremented.
        This method only updates timestamps and gap timing.
        """
        current_time = time.time()

        # Update timestamps and timing (thread-safe)
        with self._lock:
            self.sent_timestamps[sender_email].append(current_time)
            self.last_sent_time[sender_email] = current_time

            # Generate next randomized gap time for this sender
            self.next_gap_time[sender_email] = self.get_randomized_gap_time(sender_email)

            if self.logger:
                self.logger.debug(f"Sender '{sender_email}' email sent. Total this run: {self.sent_counts[sender_email]}, "
                                 f"Global total: {self.global_sent_count}, Next gap: {self.next_gap_time[sender_email]:.2f}s")

    def record_sent_legacy(self, sender_email):
        """
        Legacy method that increments counters. Use this if not using try_reserve_send_slot().
        """
        current_time = time.time()

        # Update counters (thread-safe)
        with self._lock:
            self.sent_counts[sender_email] += 1
            self.sent_timestamps[sender_email].append(current_time)
            self.last_sent_time[sender_email] = current_time

            # Generate next randomized gap time for this sender
            self.next_gap_time[sender_email] = self.get_randomized_gap_time(sender_email)

            # Increment global counter
            self.global_sent_count += 1

            if self.logger:
                self.logger.debug(f"Sender '{sender_email}' email sent. Total this run: {self.sent_counts[sender_email]}, "
                                 f"Global total: {self.global_sent_count}, Next gap: {self.next_gap_time[sender_email]:.2f}s")
    
    def is_global_limit_reached(self):
        """Check if the global email limit has been reached."""
        with self._lock:
            return self.global_limit > 0 and self.global_sent_count >= self.global_limit
    
    def get_stats(self):
        """Get statistics for all senders."""
        with self._lock:
            stats = {
                'global': {
                    'total_sent': self.global_sent_count,
                    'global_limit': self.global_limit,
                    'remaining': max(0, self.global_limit - self.global_sent_count) if self.global_limit > 0 else 'unlimited'
                }
            }

            for sender_email in self.rate_limits:
                stats[sender_email] = {
                    'total_sent_this_run': self.sent_counts[sender_email],
                    'total_limit_per_run': self.rate_limits[sender_email]['total_limit_per_run'],
                    'remaining_this_run': max(0, self.rate_limits[sender_email]['total_limit_per_run'] - self.sent_counts[sender_email]) if self.rate_limits[sender_email]['total_limit_per_run'] > 0 else 'unlimited'
                }
        return stats


