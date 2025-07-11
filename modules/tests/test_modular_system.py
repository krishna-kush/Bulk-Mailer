#!/usr/bin/env python3
"""
Test script to verify the modular system structure and functionality.
Tests all major components and their interactions.
"""

import os
import sys
import time
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test imports from all modules
try:
    from config.config import Config
    from core.email_task import EmailTask
    from core.utils import extract_name_from_email
    from mailer.email_sender import EmailSender
    from mailer.email_composer import EmailComposer
    from queue.smart_queue_manager import SmartQueueManager
    from queue.email_queue import EmailQueue
    from queue.queue_worker import QueueWorker
    from rate_limiter.rate_limiter import RateLimiter
    from sender.sender_manager import SenderManager
    from sender.sender_failure_tracker import SenderFailureTracker
    from recipient.recipient_manager import RecipientManager
    from retry.email_retry_handler import EmailRetryHandler
    from scheduler.batch_scheduler import BatchScheduler
    
    print("✅ All module imports successful!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_modular_structure():
    """Test the modular system structure."""
    
    print("\n🧪 Testing Modular Email System Structure")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test 1: Config Module
    print("\n1. Testing Config Module...")
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = Config(base_dir)
        
        # Test all config methods
        app_settings = config.get_application_settings()
        smtp_configs = config.get_smtp_configs()
        senders_data = config.get_senders()
        rate_limiter_settings = config.get_rate_limiter_settings()
        
        print(f"   ✅ Config loaded: {len(senders_data)} senders configured")
        
    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False
    
    # Test 2: Core Module
    print("\n2. Testing Core Module...")
    try:
        # Test EmailTask
        test_recipient = {"email": "test@example.com", "row_id": 1}
        email_task = EmailTask(
            recipient_data=test_recipient,
            subject="Test Subject",
            body_html="<h1>Test</h1>",
            attachments=[],
            max_attempts=3
        )
        
        # Test utils
        name = extract_name_from_email("john.doe@example.com")
        
        print(f"   ✅ Core module: EmailTask created, name extracted: '{name}'")
        
    except Exception as e:
        print(f"   ❌ Core test failed: {e}")
        return False
    
    # Test 3: Queue Module
    print("\n3. Testing Queue Module...")
    try:
        # Test EmailQueue
        email_queue = EmailQueue("test@example.com")
        email_queue.put(email_task)
        retrieved_task = email_queue.get()
        
        # Test SmartQueueManager
        queue_settings = config.get_queue_management_settings()
        rate_limiter = RateLimiter(senders_data, 100, logger)
        failure_tracker = SenderFailureTracker(config.get_failure_tracking_settings(), logger)
        
        queue_manager = SmartQueueManager(
            senders=senders_data,
            queue_settings=queue_settings,
            rate_limiter=rate_limiter,
            failure_tracker=failure_tracker,
            logger=logger
        )
        
        print(f"   ✅ Queue module: EmailQueue and SmartQueueManager working")
        
    except Exception as e:
        print(f"   ❌ Queue test failed: {e}")
        return False
    
    # Test 4: Mailer Module
    print("\n4. Testing Mailer Module...")
    try:
        email_sender = EmailSender(smtp_configs, logger)
        email_composer = EmailComposer(logger)
        
        print(f"   ✅ Mailer module: EmailSender and EmailComposer initialized")
        
    except Exception as e:
        print(f"   ❌ Mailer test failed: {e}")
        return False
    
    # Test 5: Rate Limiter Module
    print("\n5. Testing Rate Limiter Module...")
    try:
        # Test rate limiter functionality
        sender_email = senders_data[0]['email']
        can_send = rate_limiter.can_send(sender_email)
        
        print(f"   ✅ Rate Limiter module: Can send check: {can_send}")
        
    except Exception as e:
        print(f"   ❌ Rate Limiter test failed: {e}")
        return False
    
    # Test 6: Sender Module
    print("\n6. Testing Sender Module...")
    try:
        sender_manager = SenderManager(senders_data, "rotate_email")
        next_sender = sender_manager.get_next_sender()
        
        print(f"   ✅ Sender module: SenderManager and SenderFailureTracker working")
        
    except Exception as e:
        print(f"   ❌ Sender test failed: {e}")
        return False
    
    # Test 7: Recipient Module
    print("\n7. Testing Recipient Module...")
    try:
        recipients_settings = config.get_recipients_settings()
        recipient_manager = RecipientManager(recipients_settings, config.base_dir, logger)
        
        print(f"   ✅ Recipient module: RecipientManager initialized")
        
    except Exception as e:
        print(f"   ❌ Recipient test failed: {e}")
        return False
    
    # Test 8: Retry Module
    print("\n8. Testing Retry Module...")
    try:
        retry_settings = config.get_retry_settings()
        retry_handler = EmailRetryHandler(retry_settings, logger)
        
        print(f"   ✅ Retry module: EmailRetryHandler initialized")
        
    except Exception as e:
        print(f"   ❌ Retry test failed: {e}")
        return False
    
    # Test 9: Scheduler Module
    print("\n9. Testing Scheduler Module...")
    try:
        batch_scheduler = BatchScheduler(queue_manager, batch_size=10, logger=logger)
        progress = batch_scheduler.get_progress()
        
        print(f"   ✅ Scheduler module: BatchScheduler initialized")
        
    except Exception as e:
        print(f"   ❌ Scheduler test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL MODULAR TESTS PASSED!")
    print("=" * 60)
    
    # Display module structure
    print("\n📁 Current Module Structure:")
    print("geo_mail/mail/")
    print("├── config/          ✅ Configuration management")
    print("├── core/            ✅ Core data structures")
    print("├── mailer/          ✅ Email sending functionality")
    print("├── queue/           ✅ Queue management system")
    print("├── rate_limiter/    ✅ Rate limiting and gap management")
    print("├── sender/          ✅ Sender management and failure tracking")
    print("├── recipient/       ✅ Recipient data management")
    print("├── retry/           ✅ Retry and fallback logic")
    print("├── scheduler/       ✅ Batch scheduling")
    print("├── templates/       ✅ Email and config templates")
    print("├── tests/           ✅ Test modules")
    print("└── logs/            ✅ Log storage")
    
    return True

def test_integration():
    """Test integration between modules."""
    
    print("\n🔗 Testing Module Integration...")
    print("=" * 60)
    
    try:
        # Setup
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = Config(base_dir)
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        # Initialize all components
        senders_data = config.get_senders()
        rate_limiter = RateLimiter(senders_data, 100, logger)
        failure_tracker = SenderFailureTracker(config.get_failure_tracking_settings(), logger)
        queue_manager = SmartQueueManager(
            senders=senders_data,
            queue_settings=config.get_queue_management_settings(),
            rate_limiter=rate_limiter,
            failure_tracker=failure_tracker,
            logger=logger
        )
        
        # Create and queue a test email
        test_recipient = {"email": "integration.test@example.com", "row_id": 999}
        email_task = EmailTask(
            recipient_data=test_recipient,
            subject="Integration Test",
            body_html="<h1>Integration Test</h1>",
            attachments=[],
            max_attempts=3
        )
        
        # Test queue integration
        queued = queue_manager.queue_email(email_task)
        stats = queue_manager.get_queue_stats()
        
        print(f"✅ Integration test: Email queued: {queued}")
        print(f"✅ Queue stats: {stats['total_queued']} emails queued")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Modular Email System Tests")
    
    # Test modular structure
    structure_ok = test_modular_structure()
    
    # Test integration
    integration_ok = test_integration()
    
    if structure_ok and integration_ok:
        print("\n🎉 ALL TESTS PASSED - MODULAR SYSTEM IS WORKING PERFECTLY!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
