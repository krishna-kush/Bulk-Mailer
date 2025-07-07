import time
from typing import Dict, Any, Optional

class EmailRetryHandler:
    """Handles email retry logic with configurable settings."""

    def __init__(self, retry_settings, logger=None):
        self.retry_settings = retry_settings
        self.logger = logger
        
        self.logger.info("EmailRetryHandler initialized with settings: "
                        f"max_retries_per_sender={retry_settings['max_retries_per_sender']}, "
                        f"retry_delay={retry_settings['retry_delay']}s, "
                        f"max_retries_per_recipient={retry_settings['max_retries_per_recipient']}")

    def attempt_send_with_retries(self, email_sender, sender_info: Dict[str, Any], 
                                 recipient_email: str, subject: str, body_html: str, 
                                 attachments=None) -> Dict[str, Any]:
        """
        Attempt to send email with retries for a single sender.
        
        Returns:
            Dict with keys: 'success', 'attempts', 'last_error', 'sender_email'
        """
        sender_email = sender_info["email"]
        sender_password = sender_info["password"]
        smtp_id = sender_info.get("smtp_id", "default")
        
        max_retries = self.retry_settings['max_retries_per_sender']
        retry_delay = self.retry_settings['retry_delay']
        
        result = {
            'success': False,
            'attempts': 0,
            'last_error': None,
            'sender_email': sender_email
        }
        
        self.logger.info(f"Starting email send to '{recipient_email}' from '{sender_email}' "
                        f"(max {max_retries} retries)")
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            result['attempts'] = attempt + 1
            
            try:
                self.logger.debug(f"Attempt {attempt + 1}/{max_retries + 1} to send email "
                                f"from '{sender_email}' to '{recipient_email}'")
                
                success = email_sender.send_email(
                    sender_email=sender_email,
                    sender_password=sender_password,
                    recipient_email=recipient_email,
                    subject=subject,
                    body_html=body_html,
                    attachments=attachments,
                    smtp_id=smtp_id
                )
                
                if success:
                    result['success'] = True
                    if attempt > 0:
                        self.logger.info(f"Email successfully sent from '{sender_email}' to '{recipient_email}' "
                                       f"on attempt {attempt + 1}")
                    return result
                else:
                    result['last_error'] = "EmailSender returned False (unknown error)"
                    
            except Exception as e:
                error_msg = str(e)
                result['last_error'] = error_msg
                self.logger.warning(f"Attempt {attempt + 1} failed for '{sender_email}' to '{recipient_email}': {error_msg}")
            
            # Don't wait after the last attempt
            if attempt < max_retries:
                self.logger.debug(f"Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
        
        # All attempts failed
        self.logger.error(f"All {result['attempts']} attempts failed for '{sender_email}' to '{recipient_email}'. "
                         f"Last error: {result['last_error']}")
        return result

    def attempt_send_with_fallbacks(self, email_sender, available_senders, recipient_email: str, 
                                   subject: str, body_html: str, attachments=None, 
                                   rate_limiter=None, failure_tracker=None, 
                                   max_fallback_attempts=None) -> Dict[str, Any]:
        """
        Attempt to send email with fallback to different senders.
        
        Returns:
            Dict with keys: 'success', 'total_attempts', 'successful_sender', 'failed_senders', 'last_error'
        """
        if max_fallback_attempts is None:
            max_fallback_attempts = len(available_senders)
        
        max_recipient_retries = self.retry_settings['max_retries_per_recipient']
        
        result = {
            'success': False,
            'total_attempts': 0,
            'successful_sender': None,
            'failed_senders': [],
            'last_error': None
        }
        
        self.logger.info(f"Starting fallback email send to '{recipient_email}' with {len(available_senders)} "
                        f"available senders (max {max_fallback_attempts} senders, "
                        f"max {max_recipient_retries} total attempts)")
        
        senders_tried = 0
        
        for sender_info in available_senders:
            if senders_tried >= max_fallback_attempts:
                self.logger.info(f"Reached max fallback attempts ({max_fallback_attempts}) for '{recipient_email}'")
                break
                
            if result['total_attempts'] >= max_recipient_retries:
                self.logger.info(f"Reached max recipient retries ({max_recipient_retries}) for '{recipient_email}'")
                break
            
            sender_email = sender_info["email"]
            
            # Check if sender is blocked
            if failure_tracker and failure_tracker.is_sender_blocked(sender_email):
                self.logger.info(f"Skipping blocked sender '{sender_email}' for '{recipient_email}'")
                continue
            
            # Check rate limits
            if rate_limiter and not rate_limiter.can_send(sender_email):
                self.logger.info(f"Skipping rate-limited sender '{sender_email}' for '{recipient_email}'")
                continue
            
            senders_tried += 1
            
            # Apply rate limiter gap
            if rate_limiter:
                rate_limiter.wait_if_needed(sender_email)
            
            # Attempt send with retries for this sender
            send_result = self.attempt_send_with_retries(
                email_sender=email_sender,
                sender_info=sender_info,
                recipient_email=recipient_email,
                subject=subject,
                body_html=body_html,
                attachments=attachments
            )
            
            result['total_attempts'] += send_result['attempts']
            
            if send_result['success']:
                result['success'] = True
                result['successful_sender'] = sender_email
                
                # Record success in tracking systems
                if failure_tracker:
                    failure_tracker.record_success(sender_email)
                if rate_limiter:
                    rate_limiter.record_sent(sender_email)
                
                self.logger.info(f"Email successfully sent to '{recipient_email}' using sender '{sender_email}' "
                               f"after {result['total_attempts']} total attempts")
                return result
            else:
                # Record failure
                result['failed_senders'].append({
                    'sender_email': sender_email,
                    'attempts': send_result['attempts'],
                    'error': send_result['last_error']
                })
                result['last_error'] = send_result['last_error']
                
                # Record failure in tracking system
                if failure_tracker:
                    failure_tracker.record_failure(sender_email, send_result['last_error'])
        
        # All senders failed
        failed_count = len(result['failed_senders'])
        self.logger.error(f"All fallback attempts failed for '{recipient_email}'. "
                         f"Tried {failed_count} senders with {result['total_attempts']} total attempts. "
                         f"Last error: {result['last_error']}")
        
        return result

    def get_stats(self):
        """Get retry handler statistics."""
        return {
            'settings': self.retry_settings,
            'configured_max_retries_per_sender': self.retry_settings['max_retries_per_sender'],
            'configured_retry_delay': self.retry_settings['retry_delay'],
            'configured_max_retries_per_recipient': self.retry_settings['max_retries_per_recipient']
        }
