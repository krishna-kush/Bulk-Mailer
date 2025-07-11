import threading
import time
from collections import deque
from typing import Dict, Optional, Any
from modules.core.email_task import EmailTask

class EmailQueue:
    """Thread-safe email queue for a specific sender."""
    
    def __init__(self, sender_email: str):
        self.sender_email = sender_email
        self.queue = deque()
        self.lock = threading.Lock()
        self._stats = {
            'total_processed': 0,
            'total_failed': 0,
            'total_succeeded': 0,
            'last_activity': None
        }
    
    def put(self, email_task: EmailTask) -> None:
        """Add an email task to the queue."""
        with self.lock:
            email_task.set_queued(self.sender_email)
            self.queue.append(email_task)
    
    def get(self) -> Optional[EmailTask]:
        """Get the next email task from the queue."""
        with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None
    
    def peek(self) -> Optional[EmailTask]:
        """Peek at the next email task without removing it."""
        with self.lock:
            if self.queue:
                return self.queue[0]
            return None
    
    def size(self) -> int:
        """Get the current queue size."""
        return len(self.queue)
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self.queue) == 0
    
    def remove_expired(self, max_age_seconds: int = 3600) -> int:
        """Remove expired email tasks from the queue."""
        removed_count = 0
        with self.lock:
            # Create new deque with non-expired items
            new_queue = deque()
            while self.queue:
                task = self.queue.popleft()
                if not task.is_expired(max_age_seconds):
                    new_queue.append(task)
                else:
                    removed_count += 1
            self.queue = new_queue
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self.lock:
            return {
                'sender_email': self.sender_email,
                'queue_size': len(self.queue),
                'total_processed': self._stats['total_processed'],
                'total_failed': self._stats['total_failed'],
                'total_succeeded': self._stats['total_succeeded'],
                'last_activity': self._stats['last_activity'],
                'oldest_task_age': self._get_oldest_task_age()
            }
    
    def _get_oldest_task_age(self) -> Optional[float]:
        """Get age of oldest task in queue."""
        if self.queue:
            oldest_task = min(self.queue, key=lambda t: t.created_at)
            return time.time() - oldest_task.created_at
        return None
    
    def record_result(self, success: bool) -> None:
        """Record the result of processing an email."""
        with self.lock:
            self._stats['total_processed'] += 1
            self._stats['last_activity'] = time.time()
            if success:
                self._stats['total_succeeded'] += 1
            else:
                self._stats['total_failed'] += 1
