import os
import csv
import time
import threading
from config.config_loader import ConfigLoader
from modules.logger.logger import AppLogger
from modules.mailer.email_sender import EmailSender
from modules.sender.sender_manager import SenderManager
from modules.mailer.email_composer import EmailComposer
from modules.rate_limiter.rate_limiter import RateLimiter
from modules.sender.sender_failure_tracker import SenderFailureTracker
from modules.retry.email_retry_handler import EmailRetryHandler
from modules.recipient.recipient_manager import RecipientManager
from modules.queue.smart_queue_manager import SmartQueueManager
from modules.queue.queue_worker import QueueWorker
from modules.core.email_task import EmailTask
from modules.core.utils import extract_name_from_email
from modules.scheduler.batch_scheduler import BatchScheduler

# BASE_DIR is now handled by the Config class

def process_queued_emails(queue_manager, email_sender, rate_limiter, failure_tracker, logger, config=None):
    """
    Process emails from all sender queues concurrently using QueueWorker.

    Returns:
        Number of successfully sent emails
    """
    # Create worker threads for each sender
    workers = []
    threads = []

    for sender_info in queue_manager.senders:
        worker = QueueWorker(
            sender_info=sender_info,
            queue_manager=queue_manager,
            email_sender=email_sender,
            rate_limiter=rate_limiter,
            failure_tracker=failure_tracker,
            logger=logger,
            config=config
        )
        workers.append(worker)

        # Start worker thread
        thread = threading.Thread(target=worker.run, daemon=True)
        thread.start()
        threads.append(thread)

    # Wait for all workers to complete
    for thread in threads:
        thread.join()

    # Collect results from all workers
    total_successful = sum(worker.emails_succeeded for worker in workers)
    total_failed = sum(worker.emails_failed for worker in workers)

    # Perform queue rebalancing if needed
    if queue_manager.should_rebalance_queues():
        moved_count = queue_manager.rebalance_queues()
        if moved_count > 0:
            logger.info(f"Rebalanced queues: moved {moved_count} emails")

    # Clean up expired emails
    expired_count = queue_manager.cleanup_expired_emails()
    if expired_count > 0:
        logger.warning(f"Cleaned up {expired_count} expired emails")

    # Log worker statistics
    logger.info("Worker Statistics:")
    for worker in workers:
        stats = worker.get_stats()
        logger.info(f"  {stats['sender_email']}: {stats['emails_succeeded']} sent, "
                   f"{stats['emails_failed']} failed, {stats['success_rate']:.1f}% success rate")

    return total_successful

def main():
    # Use the directory where main.py is located (the mail directory)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config = ConfigLoader(base_dir)
    app_logger = AppLogger(config.base_dir, config_path=config.config_path)
    logger = app_logger.get_logger()

    smtp_configs = config.get_smtp_configs()
    senders_data = config.get_senders()
    app_settings = config.get_application_settings()
    rate_limiter_settings = config.get_rate_limiter_settings()
    retry_settings = config.get_retry_settings()
    failure_tracking_settings = config.get_failure_tracking_settings()
    fallback_settings = config.get_fallback_settings()
    email_content_settings = config.get_email_content_settings()
    recipients_settings = config.get_recipients_settings()
    queue_management_settings = config.get_queue_management_settings()
    personalization_settings = config.get_email_personalization_settings()
    attachments_settings = config.get_email_attachments_settings()

    email_sender = EmailSender(smtp_configs, logger)
    sender_manager = SenderManager(
        senders_data,
        app_settings["sender_strategy"]
    )
    email_composer = EmailComposer(logger, personalization_settings, config.base_dir)
    rate_limiter = RateLimiter(senders_data, rate_limiter_settings["global_limit"], logger)
    failure_tracker = SenderFailureTracker(failure_tracking_settings, logger)
    retry_handler = EmailRetryHandler(retry_settings, logger)

    logger.info(f"Initialized email system with strategy: {app_settings['sender_strategy']}")
    logger.info(f"Fallback enabled: {fallback_settings['enable_fallback']}")
    logger.info(f"Max fallback attempts: {fallback_settings['max_fallback_attempts']}")
    logger.info(f"Global email limit: {rate_limiter_settings['global_limit']}")
    logger.info(f"Loaded {len(senders_data)} senders")

    # Initialize recipient manager
    recipient_manager = RecipientManager(recipients_settings, config.base_dir, logger)
    
    # Load recipients
    try:
        recipients = recipient_manager.get_recipients()
        logger.info(f"Loaded {len(recipients)} recipients from {recipients_settings['recipients_from']} source")
        
        # Show statistics for database source
        if recipients_settings['recipients_from'] == 'db':
            stats = recipient_manager.get_recipient_statistics()
            logger.info(f"Recipient statistics: {stats}")
            
    except Exception as e:
        logger.error(f"Error loading recipients: {e}")
        return

    # Load email body HTML
    body_html = ""
    body_html_path = os.path.join(config.base_dir, email_content_settings["body_html_file"])
    if os.path.exists(body_html_path):
        with open(body_html_path, "r") as f:
            body_html = f.read()
    else:
        logger.warning(f"Email HTML template not found: {body_html_path}. Using empty HTML body.")

    # Get regular attachments
    attachment_dir = os.path.join(config.base_dir, email_content_settings["attachment_dir"])
    attachments = []
    if os.path.exists(attachment_dir) and os.path.isdir(attachment_dir):
        for f_name in os.listdir(attachment_dir):
            attachments.append(os.path.join(attachment_dir, f_name))
    logger.info(f"Found {len(attachments)} attachments in {attachment_dir}.")

    # Get CID attachments (inline attachments)
    cid_attachments = {}
    for attachment_name, attachment_config in attachments_settings["attachments"].items():
        file_path = attachment_config["file_path"]
        content_id = attachment_config["content_id"]

        if os.path.exists(file_path):
            cid_attachments[content_id] = file_path
            logger.debug(f"CID attachment configured: {content_id} -> {file_path}")
        else:
            logger.warning(f"CID attachment file not found: {file_path}")

    logger.info(f"Configured {len(cid_attachments)} CID attachments for inline embedding.")

    # Sending logic
    successful_sends = 0
    failed_sends = 0
    
    if app_settings["sender_strategy"] == "rotate_email":
        logger.info("Starting rotate_email strategy with smart queue-based concurrent processing")

        # Initialize the smart queue manager
        queue_manager = SmartQueueManager(
            senders=senders_data,
            queue_settings=queue_management_settings,
            rate_limiter=rate_limiter,
            failure_tracker=failure_tracker,
            logger=logger
        )

        # Process emails in batches using the queue system
        batch_size = queue_management_settings['batch_processing_size']
        processed_count = 0

        logger.info(f"Queue system initialized - batch size: {batch_size}, max queue per sender: {queue_management_settings['max_queue_size_per_sender']}")

        while processed_count < len(recipients):
            # Load next batch of recipients
            batch_end = min(processed_count + batch_size, len(recipients))
            current_batch = recipients[processed_count:batch_end]

            logger.info(f"Processing batch {processed_count//batch_size + 1}: "
                       f"emails {processed_count + 1}-{batch_end} of {len(recipients)}")

            # Create email tasks and queue them
            queued_in_batch = 0
            for recipient in current_batch:
                # Check if global limit has been reached
                if rate_limiter.is_global_limit_reached():
                    logger.info("Global email limit reached. Stopping email processing.")
                    break

                recipient_email = recipient['email']

                # Personalize the email using the new personalization system
                if personalization_settings["enable_personalization"]:
                    try:
                        personalized_body_html = email_composer.personalizer.personalize_email(
                            body_html, recipient
                        )
                        personalized_subject = email_composer.personalizer.personalize_email(
                            email_content_settings["subject"], recipient
                        )
                        logger.debug(f"Personalized email for {recipient_email}")
                    except Exception as e:
                        logger.warning(f"Personalization failed for {recipient_email}: {e}")
                        # Fallback to legacy personalization
                        recipient_name = extract_name_from_email(recipient_email)
                        personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                        personalized_subject = email_content_settings["subject"]
                else:
                    # Legacy personalization
                    recipient_name = extract_name_from_email(recipient_email)
                    personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                    personalized_subject = email_content_settings["subject"]

                # Create email task
                email_task = EmailTask(
                    recipient_data=recipient,
                    subject=personalized_subject,
                    body_html=personalized_body_html,
                    attachments=attachments,
                    cid_attachments=cid_attachments,
                    max_attempts=fallback_settings["max_fallback_attempts"]
                )

                # Set total available senders for retry logic
                email_task.set_total_available_senders(len(senders_data))

                # Queue the email task
                if queue_manager.queue_email(email_task):
                    queued_in_batch += 1
                    logger.debug(f"Queued email for {recipient_email}")
                else:
                    logger.error(f"Failed to queue email for {recipient_email}")
                    failed_sends += 1
                    recipient_manager.update_recipient_status(recipient, 'error')

            logger.info(f"Queued {queued_in_batch} emails in current batch")

            # Process queued emails concurrently
            batch_successful = process_queued_emails(
                queue_manager=queue_manager,
                email_sender=email_sender,
                rate_limiter=rate_limiter,
                failure_tracker=failure_tracker,
                logger=logger,
                config=config
            )

            successful_sends += batch_successful
            logger.info(f"Batch completed: {batch_successful} emails sent successfully")

            processed_count = batch_end

            # Check if we should stop due to global limit
            if rate_limiter.is_global_limit_reached():
                logger.info("Global email limit reached. Stopping batch processing.")
                break

        # Get final statistics
        queue_stats = queue_manager.get_queue_stats()
        logger.info(f"Queue processing completed. Final stats: {queue_stats}")

        # Calculate failed sends from remaining queued emails
        for sender_email, queue_stat in queue_stats['sender_queues'].items():
            failed_sends += queue_stat['queue_size']  # Remaining emails in queues

    elif app_settings["sender_strategy"] == "duplicate_send":
        logger.info("Starting duplicate_send strategy with retry support")
        
        for recipient in recipients:
            # Check if global limit has been reached
            if rate_limiter.is_global_limit_reached():
                logger.info("Global email limit reached. Stopping email processing.")
                break
                
            logger.info(f"Processing recipient: {recipient} (will attempt with all available senders)")
            recipient_success = False
            senders_used = 0
            
            # Personalize the email using the new personalization system
            recipient_data = {'email': recipient}  # Create recipient data dict for fallback
            if personalization_settings["enable_personalization"]:
                try:
                    personalized_body_html = email_composer.personalizer.personalize_email(
                        body_html, recipient_data
                    )
                    personalized_subject = email_composer.personalizer.personalize_email(
                        email_content_settings["subject"], recipient_data
                    )
                except Exception as e:
                    logger.warning(f"Personalization failed for {recipient}: {e}")
                    # Fallback to legacy personalization
                    recipient_name = extract_name_from_email(recipient)
                    personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                    personalized_subject = email_content_settings["subject"]
            else:
                # Legacy personalization
                recipient_name = extract_name_from_email(recipient)
                personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                personalized_subject = email_content_settings["subject"]

            for sender in senders_data:
                # Check if global limit has been reached
                if rate_limiter.is_global_limit_reached():
                    logger.info("Global email limit reached. Stopping sender processing.")
                    break
                    
                sender_email = sender["email"]
                
                # Check if sender is blocked
                if failure_tracker.is_sender_blocked(sender_email):
                    logger.info(f"Skipping blocked sender '{sender_email}' for {recipient}")
                    continue

                # Check rate limits
                if not rate_limiter.can_send(sender_email):
                    logger.info(f"Skipping rate-limited sender '{sender_email}' for {recipient}")
                    continue

                # Attempt send with retries
                rate_limiter.wait_if_needed(sender_email)
                
                result = retry_handler.attempt_send_with_retries(
                    email_sender=email_sender,
                    sender_info=sender,
                    recipient_email=recipient,
                    subject=personalized_subject,
                    body_html=personalized_body_html,
                    attachments=attachments,
                    cid_attachments=cid_attachments
                )
                
                senders_used += 1
                
                if result['success']:
                    sender_manager.record_sent(sender_email)
                    rate_limiter.record_sent(sender_email)
                    failure_tracker.record_success(sender_email)
                    recipient_success = True
                    logger.info(f"✓ Email sent to {recipient} using {sender_email} "
                               f"(attempts: {result['attempts']})")
                else:
                    failure_tracker.record_failure(sender_email, result['last_error'])
                    logger.warning(f"✗ Failed to send from {sender_email} to {recipient} "
                               f"after {result['attempts']} attempts. Error: {result['last_error']}")
            
            if recipient_success:
                successful_sends += 1
                logger.info(f"✓ Successfully sent to {recipient} using {senders_used} senders")
            else:
                failed_sends += 1
                logger.error(f"✗ Failed to send to {recipient} - no senders were able to deliver")

    logger.info(f"Email sending process completed. Success: {successful_sends}, Failed: {failed_sends}")
    
    # Log comprehensive statistics
    logger.info("=" * 60)
    logger.info("FINAL STATISTICS")
    logger.info("=" * 60)
    
    # Rate limiter statistics
    rate_stats = rate_limiter.get_stats()
    logger.info("Rate Limiter Statistics:")
    global_stats = rate_stats.get('global', {})
    logger.info(f"  Global: {global_stats.get('total_sent', 0)} sent, "
               f"limit: {global_stats.get('global_limit', 0)}, "
               f"remaining: {global_stats.get('remaining', 'unlimited')}")
    
    for sender_email, stat in rate_stats.items():
        if sender_email != 'global':
            logger.info(f"  Sender '{sender_email}': {stat['total_sent_this_run']} sent this run, "
                       f"remaining: {stat['remaining_this_run']}")
    
    # Failure tracker statistics
    logger.info("\nFailure Tracker Statistics:")
    failure_stats = failure_tracker.get_stats()
    summary = failure_stats.get('_summary', {})
    logger.info(f"  Total senders tracked: {summary.get('total_senders_tracked', 0)}")
    logger.info(f"  Currently blocked: {summary.get('currently_blocked', 0)}")
    logger.info(f"  Total active failures: {summary.get('total_active_failures', 0)}")
    
    for sender_email, status in failure_stats.items():
        if sender_email != '_summary':
            if status['is_blocked']:
                logger.warning(f"  Sender '{sender_email}': BLOCKED until {status['blocked_until']} "
                             f"({status['remaining_block_time']:.1f}s remaining)")
            elif status['failure_count'] > 0:
                logger.info(f"  Sender '{sender_email}': {status['failure_count']} failures "
                           f"({status['remaining_failures']} before block)")
    
    # Retry handler statistics
    logger.info("\nRetry Handler Settings:")
    retry_stats = retry_handler.get_stats()
    settings = retry_stats['settings']
    logger.info(f"  Max retries per sender: {settings['max_retries_per_sender']}")
    logger.info(f"  Retry delay: {settings['retry_delay']} seconds")
    logger.info(f"  Max retries per recipient: {settings['max_retries_per_recipient']}")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()


