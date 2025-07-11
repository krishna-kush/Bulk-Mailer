import threading
import time
from typing import Dict, List, Optional, Any, Tuple
from modules.core.email_task import EmailTask
from .email_queue import EmailQueue


class SmartQueueManager:
    """
    Manages email queues across multiple senders with intelligent distribution.
    Handles batch processing, optimal sender selection, and overflow management.
    """
    
    def __init__(self, senders: List[Dict[str, Any]], queue_settings: Dict[str, Any], 
                 rate_limiter, failure_tracker, logger):
        """
        Initialize the smart queue manager.
        
        Args:
            senders: List of sender configurations
            queue_settings: Queue management settings from config
            rate_limiter: RateLimiter instance
            failure_tracker: SenderFailureTracker instance
            logger: Logger instance
        """
        self.senders = senders
        self.queue_settings = queue_settings
        self.rate_limiter = rate_limiter
        self.failure_tracker = failure_tracker
        self.logger = logger
        
        # Create per-sender queues
        self.sender_queues: Dict[str, EmailQueue] = {}
        for sender in senders:
            sender_email = sender['email']
            self.sender_queues[sender_email] = EmailQueue(sender_email)
        
        # Queue management state
        self.current_batch_offset = 0
        self.last_balance_time = time.time()
        self.total_emails_processed = 0
        
        # Thread safety
        self.manager_lock = threading.Lock()
        
        self.logger.info(f"SmartQueueManager initialized with {len(senders)} senders")
        self.logger.info(f"Queue settings: {queue_settings}")
    
    def calculate_sender_availability(self, sender_email: str) -> float:
        """
        Calculate when sender will be available for new email.
        Returns total wait time in seconds.
        """
        # Current gap remaining
        gap_remaining = self.rate_limiter.get_gap_wait_time(sender_email)
        
        # Time to process current queue
        queue_size = self.sender_queues[sender_email].size()
        sender_gap_time = self._get_sender_gap_time(sender_email)
        queue_processing_time = queue_size * sender_gap_time
        
        # Total availability time
        total_wait = gap_remaining + queue_processing_time
        
        return total_wait
    
    def find_optimal_sender(self, email_task: EmailTask) -> Optional[str]:
        """
        Find the optimal sender for an email task based on availability and constraints.
        
        Args:
            email_task: The email task to be queued
            
        Returns:
            Sender email address or None if no suitable sender found
        """
        calculation_method = self.queue_settings.get('queue_calculation_method', 'smart')
        
        available_senders = []
        
        for sender in self.senders:
            sender_email = sender['email']
            
            # Skip if sender has been tried already
            if not email_task.can_try_sender(sender_email):
                continue
                
            # Skip if sender is blocked
            if self.failure_tracker.is_sender_blocked(sender_email):
                continue
                
            # Skip if sender has reached rate limits (excluding gap)
            if not self.rate_limiter.can_send_ignoring_gap(sender_email):
                continue
            
            # Skip if queue is at max capacity
            if self.sender_queues[sender_email].size() >= self.queue_settings['max_queue_size_per_sender']:
                continue
            
            if calculation_method == 'smart':
                wait_time = self.calculate_sender_availability(sender_email)
                available_senders.append((sender_email, wait_time))
            elif calculation_method == 'simple':
                queue_size = self.sender_queues[sender_email].size()
                available_senders.append((sender_email, queue_size))
            elif calculation_method == 'round_robin':
                # For round-robin, we'll just return the first available
                return sender_email
        
        if not available_senders:
            return None
        
        # Sort by wait time/queue size and return the best option
        available_senders.sort(key=lambda x: x[1])
        return available_senders[0][0]
    
    def queue_email(self, email_task: EmailTask) -> bool:
        """
        Queue an email task to the optimal sender.
        
        Args:
            email_task: The email task to queue
            
        Returns:
            True if successfully queued, False otherwise
        """
        optimal_sender = self.find_optimal_sender(email_task)
        
        if optimal_sender:
            self.sender_queues[optimal_sender].put(email_task)
            self.logger.debug(f"Queued email to {email_task.recipient_email} in {optimal_sender} queue")
            return True
        else:
            # Handle overflow based on strategy
            return self._handle_overflow(email_task)
    
    def _handle_overflow(self, email_task: EmailTask) -> bool:
        """Handle email when all queues are full or no senders available."""
        strategy = self.queue_settings.get('overflow_strategy', 'wait_shortest')
        
        if strategy == 'wait_shortest':
            # Find sender with shortest total wait time, even if queue is full
            best_sender = None
            min_wait = float('inf')
            
            for sender in self.senders:
                sender_email = sender['email']
                if email_task.can_try_sender(sender_email):
                    wait_time = self.calculate_sender_availability(sender_email)
                    if wait_time < min_wait:
                        min_wait = wait_time
                        best_sender = sender_email
            
            if best_sender:
                self.sender_queues[best_sender].put(email_task)
                self.logger.warning(f"Overflow: Queued {email_task.recipient_email} to {best_sender} "
                                  f"(queue size: {self.sender_queues[best_sender].size()})")
                return True
        
        elif strategy == 'expand_queue':
            # Temporarily exceed max queue size
            optimal_sender = self.find_optimal_sender(email_task)
            if optimal_sender:
                self.sender_queues[optimal_sender].put(email_task)
                self.logger.warning(f"Overflow: Expanded {optimal_sender} queue for {email_task.recipient_email}")
                return True
        
        # If all strategies fail
        self.logger.error(f"Failed to queue email to {email_task.recipient_email} - no available senders")
        return False
    
    def _get_sender_gap_time(self, sender_email: str) -> float:
        """Get the gap time for a specific sender."""
        for sender in self.senders:
            if sender['email'] == sender_email:
                return sender.get('per_run_gap', 0)
        return 0
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all queues."""
        stats = {
            'total_senders': len(self.senders),
            'total_emails_processed': self.total_emails_processed,
            'queue_settings': self.queue_settings,
            'sender_queues': {}
        }
        
        total_queued = 0
        for sender_email, queue in self.sender_queues.items():
            queue_stats = queue.get_stats()
            stats['sender_queues'][sender_email] = queue_stats
            total_queued += queue_stats['queue_size']
        
        stats['total_queued'] = total_queued
        stats['last_balance_time'] = self.last_balance_time

        return stats

    def get_next_email_for_sender(self, sender_email: str) -> Optional[EmailTask]:
        """
        Get the next email task for a specific sender.

        Args:
            sender_email: Email address of the sender

        Returns:
            EmailTask or None if queue is empty
        """
        if sender_email in self.sender_queues:
            return self.sender_queues[sender_email].get()
        return None

    def requeue_failed_email(self, email_task: EmailTask, failed_sender: str, error: str) -> bool:
        """
        Requeue a failed email to a different sender.

        Args:
            email_task: The failed email task
            failed_sender: Sender that failed to send the email
            error: Error message from the failed attempt

        Returns:
            True if successfully requeued, False if no more attempts possible
        """
        # Record the failure
        email_task.record_attempt(failed_sender, success=False, error=error)

        # Check if we should retry
        if not email_task.should_retry():
            self.logger.error(f"Email to {email_task.recipient_email} failed permanently after "
                            f"{email_task.attempt_count} attempts")
            return False

        # Try to queue to a different sender
        if self.queue_email(email_task):
            self.logger.info(f"Requeued failed email to {email_task.recipient_email} "
                           f"(attempt {email_task.attempt_count}/{email_task.max_attempts})")
            return True
        else:
            self.logger.error(f"Failed to requeue email to {email_task.recipient_email} - no available senders")
            email_task.status = 'failed'
            return False

    def record_successful_send(self, email_task: EmailTask, sender_email: str) -> None:
        """
        Record a successful email send.

        Args:
            email_task: The email task that was sent successfully
            sender_email: Sender that successfully sent the email
        """
        email_task.record_attempt(sender_email, success=True)
        self.sender_queues[sender_email].record_result(success=True)
        self.total_emails_processed += 1

        self.logger.debug(f"Successfully sent email to {email_task.recipient_email} using {sender_email}")

    def should_rebalance_queues(self) -> bool:
        """Check if queues should be rebalanced."""
        if not self.queue_settings.get('enable_queue_balancing', True):
            return False

        # Check time interval
        balance_interval = self.queue_settings.get('queue_balance_interval', 30)
        if time.time() - self.last_balance_time < balance_interval:
            return False

        # Check if any email has been waiting too long
        max_wait_threshold = self.queue_settings.get('max_wait_time_threshold', 300)

        for queue in self.sender_queues.values():
            stats = queue.get_stats()
            if stats['oldest_task_age'] and stats['oldest_task_age'] > max_wait_threshold:
                return True

        return False

    def rebalance_queues(self) -> int:
        """
        Rebalance emails across queues for optimal performance.

        Returns:
            Number of emails moved during rebalancing
        """
        if not self.queue_settings.get('enable_queue_balancing', True):
            return 0

        moved_count = 0
        max_wait_threshold = self.queue_settings.get('max_wait_time_threshold', 300)

        with self.manager_lock:
            # Find overloaded queues (emails waiting too long)
            overloaded_queues = []

            for sender_email, queue in self.sender_queues.items():
                stats = queue.get_stats()
                if stats['oldest_task_age'] and stats['oldest_task_age'] > max_wait_threshold:
                    overloaded_queues.append(sender_email)

            # Move emails from overloaded queues to better options
            for overloaded_sender in overloaded_queues:
                queue = self.sender_queues[overloaded_sender]

                # Try to move some emails to better queues
                emails_to_move = []
                while queue.size() > 0 and len(emails_to_move) < 5:  # Move max 5 at a time
                    email_task = queue.get()
                    if email_task and email_task.can_try_sender(overloaded_sender):
                        emails_to_move.append(email_task)
                    else:
                        # Put it back if we can't move it
                        if email_task:
                            queue.put(email_task)
                        break

                # Try to requeue moved emails
                for email_task in emails_to_move:
                    better_sender = self.find_optimal_sender(email_task)
                    if better_sender and better_sender != overloaded_sender:
                        self.sender_queues[better_sender].put(email_task)
                        moved_count += 1
                        self.logger.debug(f"Rebalanced: moved {email_task.recipient_email} "
                                        f"from {overloaded_sender} to {better_sender}")
                    else:
                        # Put it back in original queue
                        queue.put(email_task)

            self.last_balance_time = time.time()

        if moved_count > 0:
            self.logger.info(f"Queue rebalancing completed: moved {moved_count} emails")

        return moved_count

    def cleanup_expired_emails(self) -> int:
        """Remove expired emails from all queues."""
        total_removed = 0
        max_age = self.queue_settings.get('max_wait_time_threshold', 300) * 2  # 2x threshold

        for sender_email, queue in self.sender_queues.items():
            removed = queue.remove_expired(max_age)
            total_removed += removed
            if removed > 0:
                self.logger.warning(f"Removed {removed} expired emails from {sender_email} queue")

        return total_removed
