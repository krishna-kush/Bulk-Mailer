import time
from typing import Set, Optional, Dict, Any

class EmailTask:
    """
    Represents an email task with tracking for attempts, failures, and retry logic.
    Each email task maintains its own state for sender attempts and failure tracking.
    """
    
    def __init__(self, recipient_data: Dict[str, Any], subject: str, body_html: str,
                 attachments: list = None, cid_attachments: dict = None, max_attempts: int = 3):
        """
        Initialize an email task.
        
        Args:
            recipient_data: Dictionary containing recipient information (email, row_id, etc.)
            subject: Email subject line
            body_html: HTML body content
            attachments: List of attachment file paths
            cid_attachments: Dict of CID attachments {content_id: file_path}
            max_attempts: Maximum total attempts across all senders
        """
        # Email content
        self.recipient_data = recipient_data
        self.recipient_email = recipient_data.get('email', '')
        self.subject = subject
        self.body_html = body_html
        self.attachments = attachments or []
        self.cid_attachments = cid_attachments or {}
        
        # Tracking fields
        self.attempted_senders: Set[str] = set()
        self.failed_senders: Set[str] = set()
        self.successful_sender: Optional[str] = None
        self.attempt_count = 0
        self.max_attempts = max_attempts
        self.last_error: Optional[str] = None
        self.created_at = time.time()
        self.last_attempt_at: Optional[float] = None
        self.status = 'pending'  # pending, retrying, sent, failed
        
        # Queue tracking
        self.current_queue: Optional[str] = None
        self.queue_entry_time: Optional[float] = None
    
    def can_try_sender(self, sender_email: str) -> bool:
        """Check if we can attempt sending with the given sender."""
        return sender_email not in self.attempted_senders
    
    def record_attempt(self, sender_email: str, success: bool, error: str = None) -> None:
        """
        Record an attempt to send this email.
        
        Args:
            sender_email: Email address of the sender that attempted to send
            success: Whether the send was successful
            error: Error message if the send failed
        """
        self.attempted_senders.add(sender_email)
        self.attempt_count += 1
        self.last_attempt_at = time.time()
        
        if success:
            self.successful_sender = sender_email
            self.status = 'sent'
        else:
            self.failed_senders.add(sender_email)
            self.last_error = error
            if self.should_retry():
                self.status = 'retrying'
            else:
                self.status = 'failed'
    
    def should_retry(self) -> bool:
        """Check if this email should be retried."""
        return (
            self.status != 'sent' and
            self.attempt_count < self.max_attempts and
            len(self.attempted_senders) < self.get_total_available_senders()
        )
    
    def get_total_available_senders(self) -> int:
        """Get total number of available senders (to be set by queue manager)."""
        # This will be set by the queue manager when it knows the sender count
        return getattr(self, '_total_senders', 3)  # Default fallback
    
    def set_total_available_senders(self, count: int) -> None:
        """Set the total number of available senders."""
        self._total_senders = count
    
    def get_untried_senders(self, available_senders: list) -> list:
        """Get list of senders that haven't been tried yet."""
        return [
            sender for sender in available_senders 
            if sender['email'] not in self.attempted_senders
        ]
    
    def get_wait_time_in_queue(self) -> float:
        """Get how long this email has been waiting in the current queue."""
        if self.queue_entry_time:
            return time.time() - self.queue_entry_time
        return 0.0
    
    def set_queued(self, sender_email: str) -> None:
        """Mark this email as queued to a specific sender."""
        self.current_queue = sender_email
        self.queue_entry_time = time.time()
    
    def is_expired(self, max_age_seconds: int = 3600) -> bool:
        """Check if this email task has expired (been pending too long)."""
        return (time.time() - self.created_at) > max_age_seconds
    
    def get_priority_score(self) -> float:
        """
        Calculate priority score for queue ordering.
        Lower score = higher priority.
        """
        base_score = self.created_at  # Older emails have higher priority
        
        # Increase priority for emails that have been retried
        retry_bonus = -60 * self.attempt_count  # 1 minute bonus per retry
        
        # Decrease priority for emails that have been waiting too long in queue
        queue_penalty = self.get_wait_time_in_queue() * 0.1
        
        return base_score + retry_bonus + queue_penalty
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert email task to dictionary for logging/debugging."""
        return {
            'recipient_email': self.recipient_email,
            'status': self.status,
            'attempt_count': self.attempt_count,
            'max_attempts': self.max_attempts,
            'attempted_senders': list(self.attempted_senders),
            'failed_senders': list(self.failed_senders),
            'successful_sender': self.successful_sender,
            'last_error': self.last_error,
            'created_at': self.created_at,
            'last_attempt_at': self.last_attempt_at,
            'current_queue': self.current_queue,
            'queue_wait_time': self.get_wait_time_in_queue(),
            'priority_score': self.get_priority_score()
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        return (f"EmailTask(to={self.recipient_email}, status={self.status}, "
                f"attempts={self.attempt_count}/{self.max_attempts}, "
                f"queue={self.current_queue})")
    
    def __repr__(self) -> str:
        return self.__str__()
