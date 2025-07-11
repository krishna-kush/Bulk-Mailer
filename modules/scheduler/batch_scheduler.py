import time
import threading
from typing import List, Dict, Any, Callable, Optional
from modules.core.email_task import EmailTask

class BatchScheduler:
    """
    Manages batch processing of emails with intelligent scheduling.
    Handles batch sizing, timing, and coordination between multiple workers.
    """
    
    def __init__(self, queue_manager, batch_size: int = 60, 
                 batch_interval: int = 30, logger=None):
        """
        Initialize batch scheduler.
        
        Args:
            queue_manager: SmartQueueManager instance
            batch_size: Number of emails to process per batch
            batch_interval: Minimum seconds between batches
            logger: Logger instance
        """
        self.queue_manager = queue_manager
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.logger = logger
        
        # Scheduling state
        self.is_running = False
        self.current_batch = 0
        self.total_batches = 0
        self.last_batch_time = 0
        self.scheduler_thread = None
        
        # Batch statistics
        self.batch_stats = {
            'total_batches_processed': 0,
            'total_emails_queued': 0,
            'total_emails_processed': 0,
            'average_batch_time': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Callbacks
        self.on_batch_start: Optional[Callable] = None
        self.on_batch_complete: Optional[Callable] = None
        self.on_all_batches_complete: Optional[Callable] = None
    
    def schedule_batches(self, recipients: List[Dict], email_template: Dict,
                        process_batch_callback: Callable) -> None:
        """
        Schedule and process email batches.
        
        Args:
            recipients: List of recipient dictionaries
            email_template: Email template configuration
            process_batch_callback: Function to call for processing each batch
        """
        if self.is_running:
            if self.logger:
                self.logger.warning("Batch scheduler is already running")
            return
        
        self.is_running = True
        self.batch_stats['start_time'] = time.time()
        
        # Calculate total batches
        self.total_batches = (len(recipients) + self.batch_size - 1) // self.batch_size
        
        if self.logger:
            self.logger.info(f"Scheduling {len(recipients)} emails in {self.total_batches} batches "
                           f"(batch size: {self.batch_size})")
        
        try:
            for batch_num in range(self.total_batches):
                if not self.is_running:
                    break
                
                # Calculate batch range
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(recipients))
                batch_recipients = recipients[start_idx:end_idx]
                
                # Wait for batch interval if needed
                self._wait_for_batch_interval()
                
                # Process batch
                batch_start_time = time.time()
                self.current_batch = batch_num + 1
                
                if self.logger:
                    self.logger.info(f"Processing batch {self.current_batch}/{self.total_batches}: "
                                   f"emails {start_idx + 1}-{end_idx} of {len(recipients)}")
                
                # Call batch start callback
                if self.on_batch_start:
                    self.on_batch_start(batch_num + 1, batch_recipients)
                
                # Process the batch
                batch_result = process_batch_callback(batch_recipients, email_template)
                
                # Update statistics
                batch_time = time.time() - batch_start_time
                self._update_batch_stats(len(batch_recipients), batch_time, batch_result)
                
                # Call batch complete callback
                if self.on_batch_complete:
                    self.on_batch_complete(batch_num + 1, batch_result)
                
                self.last_batch_time = time.time()
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in batch scheduler: {e}")
        finally:
            self.is_running = False
            self.batch_stats['end_time'] = time.time()
            
            # Call completion callback
            if self.on_all_batches_complete:
                self.on_all_batches_complete(self.batch_stats)
            
            if self.logger:
                self._log_final_stats()
    
    def schedule_batches_async(self, recipients: List[Dict], email_template: Dict,
                              process_batch_callback: Callable) -> threading.Thread:
        """
        Schedule batches asynchronously in a separate thread.
        
        Returns:
            Thread object for the scheduler
        """
        self.scheduler_thread = threading.Thread(
            target=self.schedule_batches,
            args=(recipients, email_template, process_batch_callback),
            daemon=True
        )
        self.scheduler_thread.start()
        return self.scheduler_thread
    
    def stop_scheduling(self) -> None:
        """Stop the batch scheduler."""
        self.is_running = False
        if self.logger:
            self.logger.info("Batch scheduler stop requested")
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for batch scheduling to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if completed, False if timed out
        """
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout)
            return not self.scheduler_thread.is_alive()
        return True
    
    def _wait_for_batch_interval(self) -> None:
        """Wait for the minimum batch interval if needed."""
        if self.last_batch_time > 0:
            elapsed = time.time() - self.last_batch_time
            if elapsed < self.batch_interval:
                wait_time = self.batch_interval - elapsed
                if self.logger:
                    self.logger.debug(f"Waiting {wait_time:.1f}s for batch interval")
                time.sleep(wait_time)
    
    def _update_batch_stats(self, emails_in_batch: int, batch_time: float, 
                           batch_result: Dict) -> None:
        """Update batch processing statistics."""
        self.batch_stats['total_batches_processed'] += 1
        self.batch_stats['total_emails_queued'] += emails_in_batch
        
        if batch_result:
            self.batch_stats['total_emails_processed'] += batch_result.get('processed', 0)
        
        # Update average batch time
        total_batches = self.batch_stats['total_batches_processed']
        current_avg = self.batch_stats['average_batch_time']
        self.batch_stats['average_batch_time'] = (
            (current_avg * (total_batches - 1) + batch_time) / total_batches
        )
    
    def _log_final_stats(self) -> None:
        """Log final batch processing statistics."""
        stats = self.batch_stats
        total_time = stats['end_time'] - stats['start_time']
        
        if self.logger:
            self.logger.info("=" * 50)
            self.logger.info("BATCH SCHEDULER FINAL STATISTICS")
            self.logger.info("=" * 50)
            self.logger.info(f"Total batches processed: {stats['total_batches_processed']}")
            self.logger.info(f"Total emails queued: {stats['total_emails_queued']}")
            self.logger.info(f"Total emails processed: {stats['total_emails_processed']}")
            self.logger.info(f"Average batch time: {stats['average_batch_time']:.2f}s")
            self.logger.info(f"Total processing time: {total_time:.2f}s")
            if stats['total_emails_processed'] > 0:
                rate = stats['total_emails_processed'] / total_time
                self.logger.info(f"Processing rate: {rate:.2f} emails/second")
            self.logger.info("=" * 50)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current batch processing progress."""
        return {
            'current_batch': self.current_batch,
            'total_batches': self.total_batches,
            'progress_percentage': (self.current_batch / max(1, self.total_batches)) * 100,
            'is_running': self.is_running,
            'batch_stats': self.batch_stats.copy()
        }
