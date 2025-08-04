# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Enterprise-grade email campaign management system designed for
#              professional bulk email campaigns with advanced queue management,
#              intelligent rate limiting, and robust error handling.
#
# Components: - Multi-Provider SMTP Management (Gmail, Outlook, Yahoo, Custom)
#             - Intelligent Queue Management & Load Balancing
#             - Advanced Rate Limiting & Throttling Control
#             - Professional HTML Template System with Personalization
#             - Retry Mechanisms with Exponential Backoff
#             - Real-time Monitoring & Comprehensive Logging
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

import os
import csv
import time
import threading
from config.config_loader import ConfigLoader
from modules.logger.logger import AppLogger
from modules.mailer.email_sender import EmailSender
from modules.mailer.unified_email_sender import UnifiedEmailSender
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
    anti_spam_settings = config.get_email_anti_spam_settings()
    attachments_settings = config.get_email_attachments_settings()

    # Load browser automation settings
    browser_automation_settings = config.get_browser_automation_settings()
    browser_providers_settings = config.get_browser_providers_settings()
    sending_mode = app_settings.get("sending_mode", "smtp")

    email_composer = EmailComposer(logger, personalization_settings, config.base_dir, anti_spam_settings)

    # Use unified email sender that supports both SMTP and browser automation
    email_sender = UnifiedEmailSender(
        smtp_configs=smtp_configs,
        browser_config=browser_automation_settings,
        providers_config=browser_providers_settings,
        sending_mode=sending_mode,
        logger=logger,
        email_composer=email_composer,
        base_dir=config.base_dir
    )
    sender_manager = SenderManager(
        senders_data,
        app_settings["sender_strategy"]
    )
    rate_limiter = RateLimiter(senders_data, rate_limiter_settings["global_limit"], logger)
    failure_tracker = SenderFailureTracker(failure_tracking_settings, logger)
    retry_handler = EmailRetryHandler(retry_settings, logger)

    logger.info(f"Initialized email system with strategy: {app_settings['sender_strategy']}")
    logger.info(f"Email sending mode: {sending_mode}")
    logger.info(f"Fallback enabled: {fallback_settings['enable_fallback']}")
    logger.info(f"Max fallback attempts: {fallback_settings['max_fallback_attempts']}")
    logger.info(f"Global email limit: {rate_limiter_settings['global_limit']}")
    logger.info(f"Loaded {len(senders_data)} senders")

    # Validate sender configurations for the current mode
    valid_senders = []
    for sender in senders_data:
        if email_sender.validate_sender_configuration(sender):
            valid_senders.append(sender)
        else:
            logger.warning(f"Skipping invalid sender configuration: {sender.get('email')}")

    if not valid_senders:
        logger.error("No valid senders found for current sending mode. Please check your configuration.")
        return

    logger.info(f"Validated {len(valid_senders)} senders for {sending_mode} mode")
    senders_data = valid_senders  # Use only valid senders

    # Prepare senders for browser automation mode
    if sending_mode == "browser":
        logger.info("Preparing senders for browser automation...")
        prepared_senders = []
        for sender in senders_data:
            if email_sender.prepare_sender(sender):
                prepared_senders.append(sender)
                logger.info(f"✓ Prepared sender: {sender['email']}")
            else:
                logger.warning(f"✗ Failed to prepare sender: {sender['email']}")

        if not prepared_senders:
            logger.error("No senders could be prepared for browser automation. Check cookies and configurations.")
            return

        logger.info(f"Successfully prepared {len(prepared_senders)} senders for browser automation")
        senders_data = prepared_senders

    # Initialize recipient manager
    recipient_manager = RecipientManager(recipients_settings, config.base_dir, logger)
    
    # Load recipients with global limit consideration
    try:
        global_limit = rate_limiter_settings['global_limit']
        max_recipients_needed = min(global_limit * 2, 1000) if global_limit > 0 else 1000  # Load 2x global limit as buffer

        recipients = recipient_manager.get_recipients(limit=max_recipients_needed)
        logger.info(f"Loaded {len(recipients)} recipients from {recipients_settings['recipients_from']} source (limited by global_limit: {global_limit})")
        
        # Show statistics for database source
        if recipients_settings['recipients_from'] == 'db':
            stats = recipient_manager.get_recipient_statistics()
            logger.info(f"Recipient statistics: {stats}")
            
    except Exception as e:
        logger.error(f"Error loading recipients: {e}")
        return

    # Load email body content (HTML or plain text)
    content_type = email_content_settings.get("content_type", "html").lower()
    body_content = ""

    if content_type == "plain":
        # Load plain text template
        body_text_file = email_content_settings.get("body_text_file", "templates/email_templates/plain_text_message.txt")
        body_text_path = os.path.join(config.base_dir, body_text_file)
        if os.path.exists(body_text_path):
            with open(body_text_path, "r") as f:
                body_content = f.read()
            logger.info(f"Loaded plain text template: {body_text_file}")
        else:
            logger.warning(f"Email text template not found: {body_text_path}. Using empty text body.")
    else:
        # Load HTML template (default)
        body_html_path = os.path.join(config.base_dir, email_content_settings["body_html_file"])
        if os.path.exists(body_html_path):
            with open(body_html_path, "r") as f:
                body_content = f.read()
            logger.info(f"Loaded HTML template: {email_content_settings['body_html_file']}")
        else:
            logger.warning(f"Email HTML template not found: {body_html_path}. Using empty HTML body.")

    # For backward compatibility, keep body_html variable
    body_html = body_content

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

                # Process email through personalizer (handles personalization and anti-spam features)
                if email_composer.personalizer:
                    try:
                        personalized_body_html = email_composer.personalizer.personalize_email(
                            body_html, recipient
                        )
                        personalized_subject = email_composer.personalizer.personalize_email(
                            email_content_settings["subject"], recipient
                        )
                        logger.debug(f"Processed email for {recipient_email} (personalization + anti-spam)")
                    except Exception as e:
                        logger.warning(f"Email processing failed for {recipient_email}: {e}")
                        # Fallback to legacy personalization
                        recipient_name = extract_name_from_email(recipient_email)
                        if content_type == "plain":
                            # Plain text personalization
                            personalized_body_html = body_html.replace('{{recipient_name}}', recipient_name)
                        else:
                            # HTML personalization
                            personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                        personalized_subject = email_content_settings["subject"]
                else:
                    # Legacy personalization only
                    recipient_name = extract_name_from_email(recipient_email)
                    if content_type == "plain":
                        # Plain text personalization
                        personalized_body_html = body_html.replace('{{recipient_name}}', recipient_name)
                    else:
                        # HTML personalization
                        personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                    personalized_subject = email_content_settings["subject"]

                # Create email task
                email_task = EmailTask(
                    recipient_data=recipient,
                    subject=personalized_subject,
                    body_content=personalized_body_html,
                    attachments=attachments,
                    cid_attachments=cid_attachments,
                    max_attempts=fallback_settings["max_fallback_attempts"],
                    content_type=content_type
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
                    if content_type == "plain":
                        # Plain text personalization
                        personalized_body_html = body_html.replace('{{recipient_name}}', recipient_name)
                    else:
                        # HTML personalization
                        personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
                    personalized_subject = email_content_settings["subject"]
            else:
                # Legacy personalization
                recipient_name = extract_name_from_email(recipient)
                if content_type == "plain":
                    # Plain text personalization
                    personalized_body_html = body_html.replace('{{recipient_name}}', recipient_name)
                else:
                    # HTML personalization
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
                    body_content=personalized_body_html,
                    attachments=attachments,
                    cid_attachments=cid_attachments,
                    content_type=content_type
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

    # Cleanup browser automation resources
    try:
        email_sender.close()
        logger.info("Email sender resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during email sender cleanup: {e}")

if __name__ == "__main__":
    main()


