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
import re

def get_project_root():
    """Returns the absolute path to the project root directory."""
    return os.path.dirname(os.path.abspath(__file__))

def _is_likely_company_name(name_part):
    """
    Determine if a name part is likely a company name rather than a person name.
    Only returns True if we're confident it's a company name based on patterns and indicators.

    Args:
        name_part (str): The name part to analyze

    Returns:
        bool: True if likely a company name, False if likely a person name or uncertain
    """
    if not name_part:
        return False

    name_lower = name_part.lower()

    # Strong company indicators - comprehensive list of business terms
    strong_company_indicators = {
        # Legal entity types
        'corp', 'corporation', 'inc', 'incorporated', 'ltd', 'limited', 'llc', 'llp', 'lp',
        'company', 'co', 'plc', 'sa', 'srl', 'gmbh', 'ag', 'spa', 'bv', 'nv', 'oy', 'ab',
        'as', 'aps', 'kft', 'zrt', 'sro', 'spol', 'doo', 'ood', 'eood', 'ad', 'ead',

        # Business types and structures
        'enterprises', 'enterprise', 'industries', 'industry', 'international', 'global',
        'worldwide', 'group', 'groups', 'holding', 'holdings', 'conglomerate', 'consortium',
        'federation', 'alliance', 'union', 'association', 'organization', 'foundation',
        'institute', 'institution', 'center', 'centre', 'bureau', 'office', 'department',

        # Professional services
        'consulting', 'consultancy', 'advisory', 'advisors', 'partners', 'partnership',
        'associates', 'firm', 'practice', 'services', 'service', 'solutions', 'solution',
        'specialists', 'experts', 'professionals', 'consultants', 'advisers',

        # Technology and software
        'tech', 'technology', 'technologies', 'software', 'systems', 'system', 'digital',
        'cyber', 'data', 'analytics', 'intelligence', 'automation', 'robotics', 'ai',
        'artificial', 'machine', 'learning', 'cloud', 'computing', 'networks', 'network',
        'internet', 'web', 'online', 'platform', 'platforms', 'app', 'apps', 'mobile',
        'development', 'programming', 'coding', 'engineering', 'innovation', 'innovations',

        # Finance and investment
        'capital', 'ventures', 'venture', 'investments', 'investment', 'fund', 'funds',
        'financial', 'finance', 'banking', 'bank', 'credit', 'loan', 'mortgage', 'insurance',
        'securities', 'trading', 'equity', 'asset', 'assets', 'wealth', 'portfolio',
        'private', 'public', 'mutual', 'hedge', 'pension', 'retirement',

        # Manufacturing and production
        'manufacturing', 'production', 'factory', 'plant', 'mill', 'works', 'industrial',
        'machinery', 'equipment', 'tools', 'automotive', 'aerospace', 'defense', 'energy',
        'power', 'electric', 'electronics', 'semiconductor', 'chemical', 'pharmaceutical',
        'biotech', 'medical', 'healthcare', 'hospital', 'clinic', 'laboratory', 'labs',

        # Retail and commerce
        'retail', 'wholesale', 'trading', 'commerce', 'commercial', 'business', 'market',
        'marketplace', 'store', 'shop', 'mall', 'outlet', 'chain', 'franchise', 'brand',
        'brands', 'products', 'goods', 'merchandise', 'sales', 'distribution', 'logistics',
        'supply', 'procurement', 'sourcing', 'import', 'export', 'shipping', 'transport',

        # Media and communications
        'media', 'communications', 'broadcasting', 'publishing', 'press', 'news', 'radio',
        'television', 'tv', 'film', 'cinema', 'entertainment', 'gaming', 'games', 'music',
        'records', 'production', 'studio', 'studios', 'creative', 'design', 'advertising',
        'marketing', 'agency', 'agencies', 'public', 'relations', 'pr', 'branding',

        # Real estate and construction
        'real', 'estate', 'property', 'properties', 'development', 'construction', 'building',
        'builders', 'contractors', 'architecture', 'engineering', 'infrastructure', 'housing',
        'residential', 'commercial', 'industrial', 'land', 'investment', 'management',

        # Education and research
        'university', 'college', 'school', 'academy', 'institute', 'education', 'educational',
        'training', 'learning', 'research', 'laboratory', 'science', 'scientific', 'study',
        'studies', 'academic', 'scholarship', 'knowledge', 'library', 'museum',

        # Transportation and logistics
        'transportation', 'transport', 'logistics', 'shipping', 'freight', 'cargo', 'delivery',
        'courier', 'express', 'airlines', 'aviation', 'railway', 'trucking', 'maritime',
        'automotive', 'vehicles', 'fleet', 'mobility', 'travel', 'tourism', 'hospitality',

        # Utilities and infrastructure
        'utilities', 'utility', 'water', 'gas', 'electricity', 'telecommunications', 'telecom',
        'communications', 'infrastructure', 'municipal', 'public', 'government', 'federal',
        'state', 'county', 'city', 'municipal', 'authority', 'commission', 'board',

        # Specialized industries
        'agriculture', 'farming', 'food', 'beverage', 'restaurant', 'catering', 'hospitality',
        'hotel', 'resort', 'spa', 'fitness', 'gym', 'sports', 'recreation', 'leisure',
        'fashion', 'clothing', 'textile', 'jewelry', 'cosmetics', 'beauty', 'wellness',
        'security', 'safety', 'protection', 'surveillance', 'investigation', 'legal', 'law',
        'accounting', 'audit', 'tax', 'compliance', 'regulatory', 'environmental', 'green',
        'renewable', 'sustainable', 'recycling', 'waste', 'cleaning', 'maintenance',

        # Modern business terms
        'startup', 'startups', 'innovation', 'incubator', 'accelerator', 'coworking', 'shared',
        'collaborative', 'cooperative', 'social', 'impact', 'nonprofit', 'charity', 'ngo',
        'foundation', 'trust', 'community', 'network', 'platform', 'ecosystem', 'marketplace',
        'ecommerce', 'fintech', 'healthtech', 'edtech', 'proptech', 'insurtech', 'regtech',
        'blockchain', 'crypto', 'cryptocurrency', 'bitcoin', 'ethereum', 'defi', 'nft',
        'metaverse', 'virtual', 'augmented', 'reality', 'vr', 'ar', 'iot', 'saas', 'paas',
        'iaas', 'api', 'sdk', 'devops', 'agile', 'scrum', 'lean', 'mvp', 'b2b', 'b2c',
        'b2g', 'p2p', 'marketplace', 'aggregator', 'disruptor', 'unicorn', 'decacorn'
    }

    # Check if the name contains strong company indicators as whole words or clear patterns
    # Split the name into words using common separators
    import re
    words = re.split(r'[.\-_\s]+', name_lower)

    # Only check for exact word matches - no suffix/prefix matching for strong indicators
    # This prevents false positives like "Francisco" matching "co"
    for indicator in strong_company_indicators:
        if indicator in words:
            return True

    # Only do suffix/prefix matching for very specific, longer business terms
    # that are unlikely to be part of person names
    safe_suffix_indicators = {
        'corp', 'corporation', 'company', 'enterprises', 'solutions', 'systems',
        'technologies', 'consulting', 'software', 'services'
    }

    for indicator in safe_suffix_indicators:
        for word in words:
            if len(word) > len(indicator) + 3:  # More conservative length check
                if word.endswith(indicator) and len(indicator) > 4:  # Only longer indicators
                    return True
                if word.startswith(indicator) and len(indicator) > 4:  # Only longer indicators
                    return True

    # Check if it's all uppercase (common for company abbreviations like IBM, NASA)
    if name_part.isupper() and len(name_part) > 2:
        return True

    # Check for patterns that suggest company names
    words = name_part.lower().split()

    # Multiple words with business-like patterns
    if len(words) > 2:
        # Long multi-word names are often companies
        return True

    # Check for number patterns (companies often have numbers)
    if any(char.isdigit() for char in name_part):
        return True

    # Check for typical company name patterns and prefixes/suffixes
    business_patterns = {
        # Technology patterns
        'tech', 'soft', 'sys', 'net', 'web', 'data', 'info', 'digital', 'cyber', 'cloud',
        'app', 'dev', 'code', 'prog', 'auto', 'smart', 'intel', 'micro', 'nano', 'mega',
        'ultra', 'super', 'hyper', 'meta', 'neo', 'next', 'future', 'advanced', 'pro',

        # Business patterns
        'biz', 'corp', 'comm', 'serv', 'prod', 'manu', 'dist', 'mark', 'sales', 'trade',
        'fin', 'bank', 'invest', 'fund', 'cap', 'asset', 'wealth', 'prop', 'real', 'build',

        # Industry patterns
        'med', 'health', 'bio', 'pharma', 'chem', 'agri', 'food', 'auto', 'aero', 'energy',
        'power', 'oil', 'gas', 'mining', 'steel', 'metal', 'plastic', 'textile', 'fashion',

        # Service patterns
        'consult', 'advis', 'legal', 'account', 'audit', 'tax', 'insur', 'secur', 'clean',
        'maint', 'repair', 'install', 'design', 'create', 'innov', 'research', 'develop',

        # Scale indicators
        'global', 'world', 'inter', 'multi', 'mega', 'macro', 'micro', 'mini', 'max', 'plus',
        'prime', 'elite', 'premium', 'deluxe', 'standard', 'basic', 'express', 'rapid',

        # Modern business
        'startup', 'scale', 'growth', 'venture', 'angel', 'seed', 'series', 'round', 'exit',
        'ipo', 'merger', 'acquisition', 'partnership', 'joint', 'strategic', 'alliance'
    }

    # Use conservative word-boundary logic for business patterns
    for pattern in business_patterns:
        # Check for exact word matches only
        if pattern in words:
            return True

        # Only do suffix/prefix matching for longer, safer patterns
        if len(pattern) > 4:  # Only longer patterns to avoid false positives
            for word in words:
                if len(word) > len(pattern) + 3:  # More conservative length check
                    if word.endswith(pattern) or word.startswith(pattern):
                        return True

    # Default to person name if we can't determine (conservative approach)
    # This means we assume it's a person unless we have strong evidence it's a company
    return False

def _is_very_likely_company_name(name_part):
    """
    More strict version of company detection for multi-word names.
    Only returns True for very obvious company patterns.
    """
    if not name_part:
        return False

    name_lower = name_part.lower()

    # Very strong company indicators only
    very_strong_indicators = {
        'corp', 'corporation', 'inc', 'incorporated', 'ltd', 'limited', 'llc', 'company',
        'enterprises', 'solutions', 'systems', 'technologies', 'consulting', 'services'
    }

    # Check if the name contains very strong company indicators as whole words
    import re
    words = re.split(r'[.\-_\s]+', name_lower)

    for indicator in very_strong_indicators:
        # Check for exact word matches only (be very strict)
        if indicator in words:
            return True

    # Check if it's all uppercase (common for company abbreviations)
    if name_part.isupper() and len(name_part) > 3:
        return True

    return False

def extract_name_from_email(email, no_company=False, name_to_return_when_company_name="There"):
    """
    Extract a name from an email address for personalization.

    Args:
        email (str): Email address to extract name from
        no_company (bool): If True, return fallback name instead of company names
        name_to_return_when_company_name (str): Fallback name when company detected and no_company=True

    Examples:
    - info@company.com -> Company (or "There" if no_company=True)
    - rahul@company.com -> Rahul
    - john.doe@example.com -> John Doe
    - support@techcorp.com -> Techcorp (or "There" if no_company=True)
    """
    if not email or '@' not in email:
        return "there"
    
    # Split email into local part and domain
    local_part, domain = email.split('@', 1)
    
    # Common generic email prefixes that should use company name instead
    generic_prefixes = {
        'info', 'contact', 'support', 'admin', 'sales', 'help', 'service',
        'hello', 'hi', 'team', 'office', 'mail', 'email', 'noreply', 'no-reply',
        'welcome', 'accounts', 'billing', 'hr', 'marketing', 'press', 'media',
        'careers', 'jobs', 'recruitment', 'recruiter', 'hiring', 'techsupport',
        'webmaster', 'postmaster', 'hostmaster', 'abuse', 'security', 'privacy',
        'legal', 'compliance', 'finance', 'accounting', 'operations', 'it',
        'tech', 'technical', 'developer', 'dev', 'api', 'system', 'sysadmin',
        # Executive and leadership roles
        'ceo', 'cto', 'cfo', 'coo', 'cmo', 'cso', 'cpo', 'cdo', 'cio', 'cro',
        'president', 'vp', 'director', 'manager', 'head', 'lead', 'chief',
        'founder', 'cofounder', 'owner', 'partner', 'principal', 'executive',
        # Department heads
        'engineering', 'product', 'design', 'research', 'strategy', 'business',
        'partnerships', 'alliances', 'relations', 'communications', 'public',
        'investor', 'board', 'advisory', 'consultant', 'specialist',
        # Legal entity abbreviations when used as email prefixes
        'co', 'inc', 'ltd', 'llc', 'corp', 'company'
    }
    
    # Clean and normalize local part
    local_clean = local_part.lower().strip()
    
    # If it's a generic email, extract company name from domain
    if local_clean in generic_prefixes:
        # If no_company is True, return the fallback name instead of company name
        if no_company:
            return name_to_return_when_company_name

        # Extract company name from domain (handle international domains)
        domain_parts = domain.split('.')

        # Skip 'www' if present
        if domain_parts[0].lower() == 'www':
            domain_parts = domain_parts[1:]

        # For domains like company.co.za, company.com.au, etc.
        # Take the first part as the company name
        if domain_parts:
            company_part = domain_parts[0]
            if company_part:
                return company_part.capitalize()
    
    # For personal emails, try to extract name from local part
    # Remove common separators and numbers
    name_part = re.sub(r'[._\-+]+', ' ', local_part)
    name_part = re.sub(r'\d+', '', name_part)  # Remove numbers
    name_part = name_part.strip()

    if name_part:
        # Split by spaces and capitalize each word
        words = name_part.split()
        if words:
            # Handle common name patterns
            if len(words) == 1:
                extracted_name = words[0].capitalize()
                # Only use fallback if we're confident this is a company name AND no_company is True
                # But be more lenient for single words that could be person names
                if no_company and _is_likely_company_name(extracted_name) and len(extracted_name) > 4:
                    return name_to_return_when_company_name
                return extracted_name
            elif len(words) >= 2:
                # Take first two words as first and last name
                extracted_name = ' '.join(word.capitalize() for word in words[:2])
                # For multi-word names, be even more conservative - likely person names
                # Only trigger company detection for very obvious company patterns
                if no_company and _is_very_likely_company_name(extracted_name):
                    return name_to_return_when_company_name
                return extracted_name
    
    # Fallback to company name if we can't extract a good name
    if no_company:
        # If no_company is True, return the fallback name instead of trying company name
        return name_to_return_when_company_name

    domain_parts = domain.split('.')

    # Skip 'www' if present
    if domain_parts[0].lower() == 'www':
        domain_parts = domain_parts[1:]

    # For domains like company.co.za, company.com.au, etc.
    # Take the first part as the company name
    if domain_parts:
        company_part = domain_parts[0]
        if company_part:
            return company_part.capitalize()

    # Ultimate fallback
    return name_to_return_when_company_name


