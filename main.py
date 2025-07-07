import os
import csv
import time
from config import Config
from logger import AppLogger
from email_sender import EmailSender
from sender_manager import SenderManager
from email_composer import EmailComposer
from rate_limiter import RateLimiter
from sender_failure_tracker import SenderFailureTracker
from email_retry_handler import EmailRetryHandler
from recipient_manager import RecipientManager
from utils import extract_name_from_email

# BASE_DIR is now handled by the Config class

def main():
    config = Config(os.path.dirname(os.path.abspath(__file__)))
    app_logger = AppLogger(config.base_dir, config_path=os.path.join(config.base_dir, "config.ini"))
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

    email_sender = EmailSender(smtp_configs, logger)
    sender_manager = SenderManager(
        senders_data,
        app_settings["sender_strategy"]
    )
    email_composer = EmailComposer(logger)
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

    # Get attachments
    attachment_dir = os.path.join(config.base_dir, email_content_settings["attachment_dir"])
    attachments = []
    if os.path.exists(attachment_dir) and os.path.isdir(attachment_dir):
        for f_name in os.listdir(attachment_dir):
            attachments.append(os.path.join(attachment_dir, f_name))
    logger.info(f"Found {len(attachments)} attachments in {attachment_dir}.")

    # Sending logic
    successful_sends = 0
    failed_sends = 0
    
    if app_settings["sender_strategy"] == "rotate_email":
        logger.info("Starting rotate_email strategy with fallback support")
        
        for recipient in recipients:
            # Check if global limit has been reached
            if rate_limiter.is_global_limit_reached():
                logger.info("Global email limit reached. Stopping email processing.")
                break
                
            recipient_email = recipient['email']
            logger.info(f"Processing recipient: {recipient_email}")
            
            # Personalize the email template for this recipient
            recipient_name = extract_name_from_email(recipient_email)
            personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
            
            if fallback_settings["enable_fallback"]:
                # Use fallback mechanism - try multiple senders if needed
                available_senders = [s for s in senders_data]  # Get all available senders
                
                result = retry_handler.attempt_send_with_fallbacks(
                    email_sender=email_sender,
                    available_senders=available_senders,
                    recipient_email=recipient_email,
                    subject=email_content_settings["subject"],
                    body_html=personalized_body_html,
                    attachments=attachments,
                    rate_limiter=rate_limiter,
                    failure_tracker=failure_tracker,
                    max_fallback_attempts=fallback_settings["max_fallback_attempts"]
                )
                
                if result['success']:
                    successful_sends += 1
                    # Record with sender manager for rotation
                    sender_manager.record_sent(result['successful_sender'])
                    # Update recipient status in database
                    recipient_manager.update_recipient_status(recipient, 'sent')
                    logger.info(f"✓ Email sent to {recipient_email} using {result['successful_sender']} "
                               f"(attempts: {result['total_attempts']})")
                else:
                    failed_sends += 1
                    # Update recipient status in database
                    recipient_manager.update_recipient_status(recipient, 'error')
                    logger.error(f"✗ Failed to send email to {recipient_email} after trying "
                               f"{len(result['failed_senders'])} senders "
                               f"({result['total_attempts']} total attempts)")
            else:
                # Original rotate_email without fallback
                sender = sender_manager.get_next_sender()
                if not sender:
                    logger.error("No available senders left. Stopping email sending.")
                    break

                sender_email = sender["email"]
                
                # Check if sender is blocked
                if failure_tracker.is_sender_blocked(sender_email):
                    logger.warning(f"Assigned sender '{sender_email}' is blocked. Skipping {recipient_email}")
                    failed_sends += 1
                    # Update recipient status in database
                    recipient_manager.update_recipient_status(recipient, 'error')
                    continue

                # Check rate limits
                if not rate_limiter.can_send(sender_email):
                    logger.warning(f"Rate limit reached for sender '{sender_email}'. Skipping {recipient_email}")
                    failed_sends += 1
                    # Update recipient status in database
                    recipient_manager.update_recipient_status(recipient, 'error')
                    continue

                # Attempt send with retries for single sender
                rate_limiter.wait_if_needed(sender_email)
                
                result = retry_handler.attempt_send_with_retries(
                    email_sender=email_sender,
                    sender_info=sender,
                    recipient_email=recipient_email,
                    subject=email_content_settings["subject"],
                    body_html=personalized_body_html,
                    attachments=attachments
                )
                
                if result['success']:
                    successful_sends += 1
                    sender_manager.record_sent(sender_email)
                    rate_limiter.record_sent(sender_email)
                    failure_tracker.record_success(sender_email)
                    # Update recipient status in database
                    recipient_manager.update_recipient_status(recipient, 'sent')
                    logger.info(f"✓ Email sent to {recipient_email} using {sender_email} "
                               f"(attempts: {result['attempts']})")
                else:
                    failed_sends += 1
                    failure_tracker.record_failure(sender_email, result['last_error'])
                    # Update recipient status in database
                    recipient_manager.update_recipient_status(recipient, 'error')
                    logger.error(f"✗ Failed to send email to {recipient_email} using {sender_email} "
                               f"after {result['attempts']} attempts. Error: {result['last_error']}")

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
            
            # Personalize the email template for this recipient
            recipient_name = extract_name_from_email(recipient)
            personalized_body_html = body_html.replace('Hi <strong>Name</strong>,', f'Hi <strong>{recipient_name}</strong>,')
            
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
                    subject=email_content_settings["subject"],
                    body_html=personalized_body_html,
                    attachments=attachments
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


