import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

class SenderFailureTracker:
    """Tracks sender failures and manages blocking/cooldown periods."""

    def __init__(self, failure_settings, logger=None):
        self.failure_settings = failure_settings
        self.logger = logger
        
        # Track failures per sender
        self.failure_counts = defaultdict(int)  # Current failure count per sender
        self.failure_timestamps = defaultdict(deque)  # Timestamps of failures
        self.blocked_until = defaultdict(float)  # When each sender will be unblocked
        self.last_failure_reset = defaultdict(float)  # Last time failure count was reset
        
        self.logger.info("SenderFailureTracker initialized with settings: "
                        f"max_failures={failure_settings['max_failures_before_block']}, "
                        f"cooldown={failure_settings['cooldown_period']}s, "
                        f"window={failure_settings['failure_window']}s")

    def is_sender_blocked(self, sender_email):
        """Check if a sender is currently blocked."""
        current_time = time.time()
        
        # Check if sender is in cooldown period
        if sender_email in self.blocked_until:
            if current_time < self.blocked_until[sender_email]:
                remaining_time = self.blocked_until[sender_email] - current_time
                self.logger.debug(f"Sender '{sender_email}' is blocked for {remaining_time:.1f} more seconds")
                return True
            else:
                # Cooldown period expired, unblock sender
                del self.blocked_until[sender_email]
                self.logger.info(f"Sender '{sender_email}' cooldown period expired, unblocking")
        
        return False

    def record_failure(self, sender_email, error_message=""):
        """Record a failure for a sender."""
        current_time = time.time()
        
        # Clean old failures outside the tracking window
        self._clean_old_failures(sender_email, current_time)
        
        # Add new failure
        self.failure_counts[sender_email] += 1
        self.failure_timestamps[sender_email].append(current_time)
        
        self.logger.warning(f"Failure recorded for sender '{sender_email}': {error_message}. "
                           f"Total failures in window: {self.failure_counts[sender_email]}")
        
        # Check if sender should be blocked
        if self.failure_counts[sender_email] >= self.failure_settings['max_failures_before_block']:
            self._block_sender(sender_email, current_time)

    def record_success(self, sender_email):
        """Record a successful send for a sender."""
        current_time = time.time()
        
        # Reset failure count on success (this means consecutive failures are required for blocking)
        if sender_email in self.failure_counts:
            old_count = self.failure_counts[sender_email]
            self.failure_counts[sender_email] = 0
            self.failure_timestamps[sender_email].clear()
            
            if old_count > 0:
                self.logger.info(f"Success recorded for sender '{sender_email}', "
                               f"reset failure count from {old_count} to 0")

    def _block_sender(self, sender_email, current_time):
        """Block a sender for the cooldown period."""
        block_until = current_time + self.failure_settings['cooldown_period']
        self.blocked_until[sender_email] = block_until
        
        block_time_str = datetime.fromtimestamp(block_until).strftime("%Y-%m-%d %H:%M:%S")
        self.logger.error(f"Sender '{sender_email}' BLOCKED due to {self.failure_counts[sender_email]} "
                         f"failures. Blocked until {block_time_str} "
                         f"({self.failure_settings['cooldown_period']} seconds)")

    def _clean_old_failures(self, sender_email, current_time):
        """Remove failures outside the tracking window."""
        window_start = current_time - self.failure_settings['failure_window']
        
        # Remove old timestamps
        timestamps = self.failure_timestamps[sender_email]
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()
            self.failure_counts[sender_email] -= 1
        
        # Reset failure count periodically if configured
        if self.failure_settings['reset_failures_after'] > 0:
            last_reset = self.last_failure_reset[sender_email]
            if current_time - last_reset > self.failure_settings['reset_failures_after']:
                if self.failure_counts[sender_email] > 0:
                    self.logger.info(f"Resetting failure count for sender '{sender_email}' "
                                   f"(periodic reset after {self.failure_settings['reset_failures_after']}s)")
                self.failure_counts[sender_email] = 0
                self.failure_timestamps[sender_email].clear()
                self.last_failure_reset[sender_email] = current_time

    def get_sender_status(self, sender_email):
        """Get current status of a sender."""
        current_time = time.time()
        self._clean_old_failures(sender_email, current_time)
        
        is_blocked = self.is_sender_blocked(sender_email)
        failure_count = self.failure_counts[sender_email]
        
        status = {
            'is_blocked': is_blocked,
            'failure_count': failure_count,
            'max_failures': self.failure_settings['max_failures_before_block'],
            'remaining_failures': max(0, self.failure_settings['max_failures_before_block'] - failure_count)
        }
        
        if is_blocked:
            status['blocked_until'] = datetime.fromtimestamp(self.blocked_until[sender_email]).strftime("%Y-%m-%d %H:%M:%S")
            status['remaining_block_time'] = max(0, self.blocked_until[sender_email] - current_time)
        
        return status

    def get_stats(self):
        """Get statistics for all tracked senders."""
        current_time = time.time()
        stats = {}
        
        # Get all senders that have been tracked
        all_senders = set(self.failure_counts.keys()) | set(self.blocked_until.keys())
        
        for sender_email in all_senders:
            stats[sender_email] = self.get_sender_status(sender_email)
        
        # Add summary
        blocked_count = sum(1 for status in stats.values() if status['is_blocked'])
        total_failures = sum(status['failure_count'] for status in stats.values())
        
        stats['_summary'] = {
            'total_senders_tracked': len(all_senders),
            'currently_blocked': blocked_count,
            'total_active_failures': total_failures
        }
        
        return stats
