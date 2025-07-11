import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

class RateLimiter:
    """Manages sending rates per sender to avoid exceeding limits."""

    def __init__(self, senders_data, global_limit=0, logger=None):
        self.senders_data = senders_data
        self.global_limit = global_limit
        self.logger = logger
        
        # Track counts and timings per sender
        self.sent_counts = defaultdict(int)  # Total sent per run for each sender
        self.sent_timestamps = defaultdict(deque)  # Timestamps for minute/hour tracking
        self.last_sent_time = defaultdict(float)  # Last sent time for gap control
        
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
                'per_run_gap': sender.get('per_run_gap', 0)
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
        # Check global limit first
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
        per_run_gap = limits['per_run_gap']

        if per_run_gap > 0:
            time_since_last = current_time - self.last_sent_time[sender_email]
            return time_since_last >= per_run_gap

        return True

    def get_gap_wait_time(self, sender_email, current_time=None):
        """Get the remaining wait time for a sender's gap period."""
        if current_time is None:
            current_time = time.time()

        if sender_email not in self.rate_limits:
            return 0.0

        limits = self.rate_limits[sender_email]
        per_run_gap = limits['per_run_gap']

        if per_run_gap > 0:
            time_since_last = current_time - self.last_sent_time[sender_email]
            if time_since_last < per_run_gap:
                return per_run_gap - time_since_last

        return 0.0
    
    def wait_if_needed(self, sender_email):
        """Wait if needed based on the gap settings for the sender."""
        wait_time = self.get_gap_wait_time(sender_email)

        if wait_time > 0:
            if self.logger:
                self.logger.debug(f"Sender '{sender_email}' gap control: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
    
    def record_sent(self, sender_email):
        """Record that an email was sent using the specified sender."""
        current_time = time.time()
        
        # Update counters
        self.sent_counts[sender_email] += 1
        self.sent_timestamps[sender_email].append(current_time)
        self.last_sent_time[sender_email] = current_time
        
        # Increment global counter
        self.global_sent_count += 1
        
        if self.logger:
            self.logger.debug(f"Sender '{sender_email}' email sent. Total this run: {self.sent_counts[sender_email]}, "
                             f"Global total: {self.global_sent_count}")
    
    def is_global_limit_reached(self):
        """Check if the global email limit has been reached."""
        return self.global_limit > 0 and self.global_sent_count >= self.global_limit
    
    def get_stats(self):
        """Get statistics for all senders."""
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


