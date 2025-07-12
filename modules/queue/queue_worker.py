import threading
import time
from typing import Dict, Any
from modules.config.config_loader import ConfigLoader
from modules.recipient.recipient_manager import RecipientManager

class QueueWorker:
    """Worker thread for processing emails from a sender's queue."""
    
    def __init__(self, sender_info: Dict[str, Any], queue_manager, email_sender, 
                 rate_limiter, failure_tracker, logger):
        """
        Initialize queue worker.
        
        Args:
            sender_info: Sender configuration dictionary
            queue_manager: SmartQueueManager instance
            email_sender: EmailSender instance
            rate_limiter: RateLimiter instance
            failure_tracker: SenderFailureTracker instance
            logger: Logger instance
        """
        self.sender_info = sender_info
        self.sender_email = sender_info['email']
        self.queue_manager = queue_manager
        self.email_sender = email_sender
        self.rate_limiter = rate_limiter
        self.failure_tracker = failure_tracker
        self.logger = logger
        
        # Thread-local recipient manager
        self.recipient_manager = None
        self._init_recipient_manager()
        
        # Worker stats
        self.emails_processed = 0
        self.emails_succeeded = 0
        self.emails_failed = 0
        self.start_time = None
        self.stop_time = None
        
    def _init_recipient_manager(self):
        """Initialize thread-local recipient manager."""
        try:
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config = ConfigLoader(base_dir)
            recipients_settings = config.get_recipients_settings()
            self.recipient_manager = RecipientManager(recipients_settings, config.base_dir, self.logger)
        except Exception as e:
            self.logger.error(f"Failed to initialize recipient manager for worker {self.sender_email}: {e}")
    
    def run(self):
        """Main worker loop - processes emails from the sender's queue."""
        self.start_time = time.time()
        self.logger.debug(f"Starting worker for sender: {self.sender_email}")
        
        try:
            while True:
                # Check if global limit reached
                if self.rate_limiter.is_global_limit_reached():
                    self.logger.info(f"Worker {self.sender_email}: Global limit reached, stopping")
                    break
                
                # Get next email from this sender's queue
                email_task = self.queue_manager.get_next_email_for_sender(self.sender_email)
                if not email_task:
                    # No more emails in queue
                    break
                
                # Process the email
                self._process_email(email_task)
                
        except Exception as e:
            self.logger.error(f"Worker {self.sender_email} encountered error: {e}")
        finally:
            self.stop_time = time.time()
            self._log_worker_stats()
    
    def _process_email(self, email_task):
        """Process a single email task."""
        self.emails_processed += 1
        
        # Check if sender is blocked
        if self.failure_tracker.is_sender_blocked(self.sender_email):
            self.logger.warning(f"Sender {self.sender_email} is blocked, requeuing email")
            self.queue_manager.requeue_failed_email(email_task, self.sender_email, "Sender blocked")
            return
        
        # Check rate limits (excluding gap)
        if not self.rate_limiter.can_send_ignoring_gap(self.sender_email):
            self.logger.warning(f"Sender {self.sender_email} rate limited, requeuing email")
            self.queue_manager.requeue_failed_email(email_task, self.sender_email, "Rate limit exceeded")
            return
        
        # Wait for gap if needed
        self.rate_limiter.wait_if_needed(self.sender_email)
        
        # Attempt to send the email
        try:
            success = self.email_sender.send_email(
                sender_email=self.sender_email,
                sender_password=self.sender_info['password'],
                recipient_email=email_task.recipient_email,
                subject=email_task.subject,
                body_html=email_task.body_html,
                attachments=email_task.attachments,
                cid_attachments=email_task.cid_attachments,
                smtp_id=self.sender_info.get('smtp_id', 'default')
            )
            
            if success:
                self._handle_success(email_task)
            else:
                self._handle_failure(email_task, "SMTP send failed")
                
        except Exception as e:
            self._handle_failure(email_task, f"Exception during send: {str(e)}")
    
    def _handle_success(self, email_task):
        """Handle successful email send."""
        # Record successful send
        self.queue_manager.record_successful_send(email_task, self.sender_email)
        self.rate_limiter.record_sent(self.sender_email)
        self.failure_tracker.record_success(self.sender_email)
        
        if self.recipient_manager:
            self.recipient_manager.update_recipient_status(email_task.recipient_data, 'sent')
        
        self.emails_succeeded += 1
        self.logger.info(f"✓ Email sent to {email_task.recipient_email} using {self.sender_email}")
    
    def _handle_failure(self, email_task, error_msg):
        """Handle failed email send."""
        self.emails_failed += 1
        
        # Try to requeue to different sender
        if self.queue_manager.requeue_failed_email(email_task, self.sender_email, error_msg):
            self.logger.warning(f"✗ Failed to send to {email_task.recipient_email} using {self.sender_email}, requeued")
        else:
            self.logger.error(f"✗ Failed to send to {email_task.recipient_email}, no more retries")
            if self.recipient_manager:
                self.recipient_manager.update_recipient_status(email_task.recipient_data, 'error')
        
        self.failure_tracker.record_failure(self.sender_email, error_msg)
    
    def _log_worker_stats(self):
        """Log worker statistics."""
        if self.start_time and self.stop_time:
            duration = self.stop_time - self.start_time
            self.logger.info(f"Worker {self.sender_email} completed: "
                           f"{self.emails_succeeded} sent, {self.emails_failed} failed, "
                           f"{self.emails_processed} total in {duration:.1f}s")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics."""
        duration = None
        if self.start_time:
            end_time = self.stop_time or time.time()
            duration = end_time - self.start_time
            
        return {
            'sender_email': self.sender_email,
            'emails_processed': self.emails_processed,
            'emails_succeeded': self.emails_succeeded,
            'emails_failed': self.emails_failed,
            'success_rate': (self.emails_succeeded / max(1, self.emails_processed)) * 100,
            'duration_seconds': duration,
            'start_time': self.start_time,
            'stop_time': self.stop_time
        }
