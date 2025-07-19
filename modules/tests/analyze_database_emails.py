#!/usr/bin/env python3

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

"""
Analyze emails in the geo-mail database to classify them as personal vs company emails.
"""

import sys
import os
import sqlite3
from collections import defaultdict

# Add parent directories to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.core.utils import extract_name_from_email


def analyze_database_emails():
    """Analyze emails in the geo-mail database."""
    
    # Database path
    db_path = "/home/kay/work/scrape/geo_mail/mail.tech.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🔍 Analyzing emails in geo-mail database...")
    print(f"📁 Database: {db_path}")
    print("="*80)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all emails from the emails table
        cursor.execute("SELECT email FROM emails WHERE email IS NOT NULL AND email != ''")
        emails = cursor.fetchall()
        
        if not emails:
            print("❌ No emails found in the database")
            return
        
        total_emails = len(emails)
        print(f"📊 Total emails found: {total_emails:,}")
        print()
        
        # Analyze each email
        personal_emails = []
        company_emails = []
        analysis_results = defaultdict(int)
        
        print("🔄 Analyzing emails...")
        
        for i, (email,) in enumerate(emails):
            if i % 1000 == 0:
                print(f"   Processed {i:,}/{total_emails:,} emails ({i/total_emails*100:.1f}%)")
            
            # Use our name extraction function to classify
            # If no_company=True returns the same as no_company=False, it's likely a person
            # If they differ, it's likely a company email
            
            name_default = extract_name_from_email(email, no_company=False)
            name_no_company = extract_name_from_email(email, no_company=True, name_to_return_when_company_name="COMPANY_DETECTED")
            
            if name_no_company == "COMPANY_DETECTED":
                # This is a company/generic email
                company_emails.append((email, name_default))
                analysis_results['company'] += 1
            else:
                # This is a personal email
                personal_emails.append((email, name_default))
                analysis_results['personal'] += 1
        
        print(f"   Processed {total_emails:,}/{total_emails:,} emails (100.0%)")
        print()
        
        # Print results
        print("="*80)
        print("📈 ANALYSIS RESULTS")
        print("="*80)
        
        personal_count = analysis_results['personal']
        company_count = analysis_results['company']
        
        print(f"👤 Personal emails: {personal_count:,} ({personal_count/total_emails*100:.1f}%)")
        print(f"🏢 Company emails:  {company_count:,} ({company_count/total_emails*100:.1f}%)")
        print(f"📊 Total analyzed:  {total_emails:,}")
        print()
        
        # Show some examples
        print("="*80)
        print("📋 EXAMPLES")
        print("="*80)
        
        print("👤 Personal Email Examples:")
        for i, (email, name) in enumerate(personal_emails[:10]):
            print(f"   {i+1:2d}. {email:<40} → {name}")
        
        if len(personal_emails) > 10:
            print(f"   ... and {len(personal_emails)-10:,} more personal emails")
        
        print()
        print("🏢 Company Email Examples:")
        for i, (email, name) in enumerate(company_emails[:10]):
            print(f"   {i+1:2d}. {email:<40} → {name}")
        
        if len(company_emails) > 10:
            print(f"   ... and {len(company_emails)-10:,} more company emails")
        
        # Domain analysis
        print()
        print("="*80)
        print("🌐 DOMAIN ANALYSIS")
        print("="*80)
        
        personal_domains = defaultdict(int)
        company_domains = defaultdict(int)
        
        for email, _ in personal_emails:
            domain = email.split('@')[1] if '@' in email else 'unknown'
            personal_domains[domain] += 1
        
        for email, _ in company_emails:
            domain = email.split('@')[1] if '@' in email else 'unknown'
            company_domains[domain] += 1
        
        print("Top Personal Email Domains:")
        for domain, count in sorted(personal_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {domain:<30} {count:,} emails")
        
        print()
        print("Top Company Email Domains:")
        for domain, count in sorted(company_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {domain:<30} {count:,} emails")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    analyze_database_emails()
