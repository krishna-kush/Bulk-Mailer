import os
import csv
import sqlite3
from typing import List, Dict, Optional, Tuple


class RecipientManager:
    """Manages recipient data from either CSV files or SQLite database."""
    
    def __init__(self, config_settings: Dict, base_dir: str, logger):
        self.config = config_settings
        self.base_dir = base_dir
        self.logger = logger
        self.db_connection = None
        
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
            
            self.db_connection = sqlite3.connect(db_path)
            self.db_connection.row_factory = sqlite3.Row  # Enable column access by name
            
            # Check if table exists
            cursor = self.db_connection.cursor()
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
                self.db_connection.commit()
                self.logger.info(f"Added 'email_sent' column to table '{self.config['db_table']}'")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
    
    def get_recipients(self) -> List[Dict]:
        """Get list of recipients from configured source."""
        if self.config['recipients_from'] == 'csv':
            return self._get_recipients_from_csv()
        elif self.config['recipients_from'] == 'db':
            return self._get_recipients_from_db()
        else:
            raise ValueError(f"Unsupported recipients_from value: {self.config['recipients_from']}")
    
    def _get_recipients_from_csv(self) -> List[Dict]:
        """Load recipients from CSV file."""
        recipients = []
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
                        recipients.append({
                            'email': email,
                            'row_id': row_num,
                            'source': 'csv'
                        })
            
            self.logger.info(f"Loaded {len(recipients)} recipients from CSV file")
            return recipients
            
        except Exception as e:
            self.logger.error(f"Error reading CSV file {recipients_path}: {e}")
            raise
    
    def _get_recipients_from_db(self) -> List[Dict]:
        """Load recipients from database, excluding already sent emails and applying filters."""
        recipients = []
        
        try:
            cursor = self.db_connection.cursor()
            
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
            
            self.logger.debug(f"Executing query: {query}")
            self.logger.debug(f"With parameters: {filter_params}")
            cursor.execute(query, filter_params)
            rows = cursor.fetchall()
            
            for row in rows:
                recipients.append({
                    'email': row['email'],
                    'row_id': row['id'],  # Now uses the configurable primary key
                    'source': 'db',
                    'status': row['email_sent']
                })
            
            self.logger.info(f"Loaded {len(recipients)} unsent recipients from database")
            if filter_conditions:
                self.logger.info(f"Applied column filters: {filter_conditions}")
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
    
    def update_recipient_status(self, recipient: Dict, status: str) -> bool:
        """Update recipient status in database. Only works for database source."""
        if self.config['recipients_from'] != 'db':
            self.logger.debug(f"Status update skipped for CSV source: {recipient['email']}")
            return True
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(f"""
                UPDATE {self.config['db_table']} 
                SET email_sent = ? 
                WHERE {self.config['db_id_column']} = ?
            """, (status, recipient['row_id']))
            
            self.db_connection.commit()
            
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
            cursor = self.db_connection.cursor()
            
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
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
    
    def __del__(self):
        """Ensure database connection is closed when object is destroyed."""
        self.close()
