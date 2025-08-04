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
import sqlite3
import threading
import fnmatch
from typing import List, Dict, Optional, Tuple


class RecipientManager:
    """Manages recipient data from either CSV files or SQLite database."""
    
    def __init__(self, config_settings: Dict, base_dir: str, logger):
        self.config = config_settings
        self.base_dir = base_dir
        self.logger = logger
        self.local_data = threading.local()  # Thread-local storage for database connections
        self.db_path = None
        
        # Validate configuration
        self._validate_config()
        
        # Initialize database connection if using db source
        if self.config['recipients_from'] == 'db':
            self._init_database()
    
    def _validate_config(self):
        """Validate recipient configuration settings."""
        recipients_from = self.config.get('recipients_from', '').lower()
        
        if recipients_from not in ['csv', 'db']:
            raise ValueError(f"Invalid recipients_from value: {recipients_from}. Must be 'csv' or 'db'")
        
        if not self.config.get('recipients_path'):
            raise ValueError("recipients_path is required")
        
        if recipients_from == 'db':
            required_fields = ['db_table', 'db_email_column', 'db_id_column']
            for field in required_fields:
                if not self.config.get(field):
                    raise ValueError(f"{field} is required when recipients_from is 'db'")
    
    def _init_database(self):
        """Initialize database connection and ensure email_sent column exists."""
        try:
            db_path = self.config['recipients_path']
            if not os.path.isabs(db_path):
                db_path = os.path.join(self.base_dir, db_path)
            
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")
            
            # Store db_path for thread-local connections
            self.db_path = db_path

            # Test connection and verify table structure
            connection = self._get_db_connection()
            connection.row_factory = sqlite3.Row  # Enable column access by name

            # Check if table exists
            cursor = connection.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (self.config['db_table'],))
            
            if not cursor.fetchone():
                raise ValueError(f"Table '{self.config['db_table']}' does not exist in database")
            
            # Check if required columns exist
            cursor.execute(f"PRAGMA table_info({self.config['db_table']})")
            columns = [column[1] for column in cursor.fetchall()]
            
            if self.config['db_email_column'] not in columns:
                raise ValueError(f"Column '{self.config['db_email_column']}' does not exist in table '{self.config['db_table']}'")
            
            if self.config['db_id_column'] not in columns:
                raise ValueError(f"Primary key column '{self.config['db_id_column']}' does not exist in table '{self.config['db_table']}'")
            
            # Add email_sent column if it doesn't exist
            if 'email_sent' not in columns:
                cursor.execute(f"""
                    ALTER TABLE {self.config['db_table']} 
                    ADD COLUMN email_sent TEXT DEFAULT NULL
                """)
                connection.commit()
                self.logger.info(f"Added 'email_sent' column to table '{self.config['db_table']}'")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

    def _get_db_connection(self):
        """Get thread-local database connection."""
        if not hasattr(self.local_data, 'connection'):
            self.local_data.connection = sqlite3.connect(self.db_path)
            self.local_data.connection.row_factory = sqlite3.Row
        return self.local_data.connection

    def get_recipients(self, limit: int = None) -> List[Dict]:
        """Get list of recipients from configured source."""
        if self.config['recipients_from'] == 'csv':
            return self._get_recipients_from_csv(limit=limit)
        elif self.config['recipients_from'] == 'db':
            return self._get_recipients_from_db(limit=limit)
        else:
            raise ValueError(f"Unsupported recipients_from value: {self.config['recipients_from']}")
    
    def _get_recipients_from_csv(self, limit: int = None) -> List[Dict]:
        """Load recipients from CSV file."""
        recipients = []
        ignored_count = 0
        recipients_path = self.config['recipients_path']

        if not os.path.isabs(recipients_path):
            recipients_path = os.path.join(self.base_dir, recipients_path)

        if not os.path.exists(recipients_path):
            raise FileNotFoundError(f"Recipients file not found: {recipients_path}")

        try:
            with open(recipients_path, mode="r", newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                for row_num, row in enumerate(reader, 1):
                    if row and row[0].strip():  # Skip empty rows
                        email = row[0].strip()

                        # Check if email should be ignored
                        if self._should_ignore_email(email):
                            ignored_count += 1
                            continue

                        recipients.append({
                            'email': email,
                            'row_id': row_num,
                            'source': 'csv'
                        })

                        # Check if we've reached the limit
                        if limit and len(recipients) >= limit:
                            break

            self.logger.info(f"Loaded {len(recipients)} recipients from CSV file")
            if ignored_count > 0:
                self.logger.info(f"Ignored {ignored_count} recipients due to ignore patterns")
            return recipients

        except Exception as e:
            self.logger.error(f"Error reading CSV file {recipients_path}: {e}")
            raise
    
    def _get_recipients_from_db(self, limit: int = None) -> List[Dict]:
        """Load recipients from database, excluding already sent emails and applying filters."""
        recipients = []
        ignored_count = 0

        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()

            # Build the base query
            query = f"""
                SELECT {self.config['db_id_column']} as id, {self.config['db_email_column']} as email, email_sent
                FROM {self.config['db_table']}
                WHERE {self.config['db_email_column']} IS NOT NULL
                AND {self.config['db_email_column']} != ''
                AND (email_sent IS NULL OR email_sent = '')
            """

            # Add column filters if specified
            filter_conditions, filter_params = self._build_filter_conditions()
            if filter_conditions:
                query += f" AND ({filter_conditions})"

            # Add LIMIT clause if specified
            if limit and limit > 0:
                query += f" LIMIT {limit}"

            self.logger.debug(f"Executing query: {query}")
            self.logger.debug(f"With parameters: {filter_params}")
            cursor.execute(query, filter_params)
            rows = cursor.fetchall()

            for row in rows:
                email = row['email']

                # Check if email should be ignored
                if self._should_ignore_email(email):
                    ignored_count += 1
                    continue

                recipients.append({
                    'email': email,
                    'row_id': row['id'],  # Now uses the configurable primary key
                    'source': 'db',
                    'status': row['email_sent']
                })

            self.logger.info(f"Loaded {len(recipients)} unsent recipients from database")
            if filter_conditions:
                self.logger.info(f"Applied column filters: {filter_conditions}")
            if ignored_count > 0:
                self.logger.info(f"Ignored {ignored_count} recipients due to ignore patterns")
            return recipients

        except Exception as e:
            self.logger.error(f"Error reading from database: {e}")
            raise

    def _build_filter_conditions(self) -> Tuple[str, List]:
        """Build SQL WHERE conditions and parameters based on column filters."""
        filter_columns = self.config.get('filter_columns', {})
        if not filter_columns:
            return "", []
        
        conditions = []
        parameters = []
        
        for column_name, filter_config in filter_columns.items():
            values = filter_config['values']
            is_not_filter = filter_config['is_not_filter']
            
            if not values:
                continue
            
            # Build placeholders for SQL IN clause
            placeholders = ','.join(['?' for _ in values])
            
            if is_not_filter:
                # NOT filter: exclude these values
                condition = f"{column_name} NOT IN ({placeholders})"
            else:
                # Regular filter: include only these values
                condition = f"{column_name} IN ({placeholders})"
            
            conditions.append(condition)
            parameters.extend(values)
        
        return ' AND '.join(conditions) if conditions else "", parameters

    def _should_ignore_email(self, email: str) -> bool:
        """
        Check if an email should be ignored based on ignore patterns.

        Args:
            email: Email address to check

        Returns:
            True if email should be ignored, False otherwise
        """
        if not email:
            return True

        ignore_patterns = self.config.get('ignore_patterns', [])
        if not ignore_patterns:
            return False

        email_lower = email.lower().strip()

        for pattern in ignore_patterns:
            if not pattern:
                continue

            # Convert pattern to lowercase for case-insensitive matching
            pattern_lower = pattern.lower().strip()

            # Use fnmatch for wildcard pattern matching
            if fnmatch.fnmatch(email_lower, pattern_lower):
                self.logger.debug(f"Email '{email}' ignored due to pattern '{pattern}'")
                return True

        return False
    
    def update_recipient_status(self, recipient: Dict, status: str) -> bool:
        """Update recipient status in database. Only works for database source."""
        if self.config['recipients_from'] != 'db':
            self.logger.debug(f"Status update skipped for CSV source: {recipient['email']}")
            return True
        
        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()
            cursor.execute(f"""
                UPDATE {self.config['db_table']}
                SET email_sent = ?
                WHERE {self.config['db_id_column']} = ?
            """, (status, recipient['row_id']))

            connection.commit()
            
            if cursor.rowcount > 0:
                self.logger.debug(f"Updated status for {recipient['email']} to '{status}'")
                return True
            else:
                self.logger.warning(f"No rows updated for recipient {recipient['email']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating recipient status: {e}")
            return False
    
    def get_recipient_statistics(self) -> Dict:
        """Get statistics about recipient status. Only works for database source."""
        if self.config['recipients_from'] != 'db':
            return {'message': 'Statistics only available for database source'}
        
        try:
            connection = self._get_db_connection()
            cursor = connection.cursor()
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*) as total 
                FROM {self.config['db_table']} 
                WHERE {self.config['db_email_column']} IS NOT NULL 
                AND {self.config['db_email_column']} != ''
            """)
            total = cursor.fetchone()[0]
            
            # Get sent count
            cursor.execute(f"""
                SELECT COUNT(*) as sent 
                FROM {self.config['db_table']} 
                WHERE email_sent = 'sent'
            """)
            sent = cursor.fetchone()[0]
            
            # Get error count
            cursor.execute(f"""
                SELECT COUNT(*) as errors 
                FROM {self.config['db_table']} 
                WHERE email_sent = 'error'
            """)
            errors = cursor.fetchone()[0]
            
            # Get pending count
            pending = total - sent - errors
            
            return {
                'total': total,
                'sent': sent,
                'errors': errors,
                'pending': pending
            }
            
        except Exception as e:
            self.logger.error(f"Error getting recipient statistics: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close database connection if open."""
        if hasattr(self.local_data, 'connection'):
            self.local_data.connection.close()
            delattr(self.local_data, 'connection')
    
    def __del__(self):
        """Ensure database connection is closed when object is destroyed."""
        self.close()
