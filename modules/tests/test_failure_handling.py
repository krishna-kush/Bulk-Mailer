#!/usr/bin/env python3
"""
Test script to demonstrate failure handling in the queue system.
This script simulates email sending failures to show how the queue system
handles retries and moves emails between sender queues.
"""

import time
import random
from config import Config
from smart_queue_manager import SmartQueueManager
from email_task import EmailTask
from rate_limiter import RateLimiter
from sender_failure_tracker import SenderFailureTracker
import logging

class MockEmailSender:
    """Mock email sender that simulates failures for testing."""
    
    def __init__(self, failure_rate=0.3):
        self.failure_rate = failure_rate
        self.send_count = 0
        
    def send_email(self, sender_email, sender_password, recipient_email, 
                   subject, body_html, attachments, smtp_id):
        """Simulate email sending with controlled failure rate."""
        self.send_count += 1
        
        # Simulate different failure patterns for different senders
        if sender_email == "krishnakumarkush@gmail.com":
            # First sender fails 40% of the time
            should_fail = random.random() < 0.4
        else:
            # Second sender fails 20% of the time  
            should_fail = random.random() < 0.2
            
        if should_fail:
            print(f"❌ SIMULATED FAILURE: {sender_email} → {recipient_email}")
            return False
        else:
            print(f"✅ SUCCESS: {sender_email} → {recipient_email}")
            return True

def test_failure_handling():
    """Test the failure handling and requeuing mechanism."""
    
    # Setup
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config = Config(base_dir)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Get settings
    senders_data = config.get_senders()
    rate_limiter_settings = config.get_rate_limiter_settings()
    failure_tracking_settings = config.get_failure_tracking_settings()
    queue_management_settings = config.get_queue_management_settings()
    
    # Initialize components
    rate_limiter = RateLimiter(senders_data, rate_limiter_settings["global_limit"], logger)
    failure_tracker = SenderFailureTracker(failure_tracking_settings, logger)
    mock_email_sender = MockEmailSender(failure_rate=0.3)
    
    # Initialize queue manager
    queue_manager = SmartQueueManager(
        senders=senders_data,
        queue_settings=queue_management_settings,
        rate_limiter=rate_limiter,
        failure_tracker=failure_tracker,
        logger=logger
    )
    
    print("🚀 Starting Failure Handling Test")
    print("=" * 60)
    print(f"Senders: {len(senders_data)}")
    print(f"Max attempts per email: 3")
    print(f"Expected failure rate: ~30%")
    print("=" * 60)
    
    # Create test emails
    test_emails = [
        {"email": "test1@example.com", "row_id": 1},
        {"email": "test2@example.com", "row_id": 2}, 
        {"email": "test3@example.com", "row_id": 3},
        {"email": "test4@example.com", "row_id": 4},
        {"email": "test5@example.com", "row_id": 5},
    ]
    
    # Queue all emails
    for recipient in test_emails:
        email_task = EmailTask(
            recipient_data=recipient,
            subject="Test Email",
            body_html="<h1>Test</h1>",
            attachments=[],
            max_attempts=3
        )
        email_task.set_total_available_senders(len(senders_data))
        
        if queue_manager.queue_email(email_task):
            print(f"📧 Queued: {recipient['email']}")
        else:
            print(f"❌ Failed to queue: {recipient['email']}")
    
    print("\n" + "=" * 60)
    print("📊 Initial Queue Stats:")
    stats = queue_manager.get_queue_stats()
    for sender_email, sender_stats in stats['sender_queues'].items():
        print(f"  {sender_email}: {sender_stats['queue_size']} emails")
    
    print("\n🔄 Processing emails with failure simulation...")
    print("=" * 60)
    
    # Process emails and track failures
    total_attempts = 0
    successful_sends = 0
    failed_permanently = 0
    
    # Process until all queues are empty
    while True:
        all_empty = True
        
        for sender in senders_data:
            sender_email = sender['email']
            
            # Get next email from this sender's queue
            email_task = queue_manager.get_next_email_for_sender(sender_email)
            if email_task:
                all_empty = False
                total_attempts += 1
                
                print(f"\n📤 Attempt {email_task.attempt_count + 1}: {sender_email} → {email_task.recipient_email}")
                
                # Simulate sending
                success = mock_email_sender.send_email(
                    sender_email=sender_email,
                    sender_password="dummy",
                    recipient_email=email_task.recipient_email,
                    subject=email_task.subject,
                    body_html=email_task.body_html,
                    attachments=email_task.attachments,
                    smtp_id="default"
                )
                
                if success:
                    queue_manager.record_successful_send(email_task, sender_email)
                    successful_sends += 1
                    print(f"   ✅ SUCCESS - Email sent!")
                else:
                    # Try to requeue
                    if queue_manager.requeue_failed_email(email_task, sender_email, "Simulated failure"):
                        print(f"   🔄 REQUEUED - Moved to different sender (attempt {email_task.attempt_count}/{email_task.max_attempts})")
                    else:
                        failed_permanently += 1
                        print(f"   💀 FAILED PERMANENTLY - No more retries")
                
                # Show current queue state
                stats = queue_manager.get_queue_stats()
                queue_summary = ", ".join([f"{email}: {stats['sender_queues'][email]['queue_size']}" 
                                         for email in stats['sender_queues']])
                print(f"   📊 Queue sizes: {queue_summary}")
                
                # Small delay to see the flow
                time.sleep(0.5)
        
        if all_empty:
            break
    
    print("\n" + "=" * 60)
    print("📈 FINAL RESULTS:")
    print("=" * 60)
    print(f"Total attempts: {total_attempts}")
    print(f"Successful sends: {successful_sends}")
    print(f"Failed permanently: {failed_permanently}")
    print(f"Success rate: {(successful_sends / len(test_emails)) * 100:.1f}%")
    
    # Final queue stats
    final_stats = queue_manager.get_queue_stats()
    print(f"\n📊 Final Queue Stats:")
    for sender_email, sender_stats in final_stats['sender_queues'].items():
        print(f"  {sender_email}: {sender_stats['queue_size']} emails remaining")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_failure_handling()
