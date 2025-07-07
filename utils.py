import os
import re

def get_project_root():
    """Returns the absolute path to the project root directory."""
    return os.path.dirname(os.path.abspath(__file__))

def extract_name_from_email(email):
    """
    Extract a name from an email address for personalization.
    
    Examples:
    - info@company.com -> Company
    - rahul@company.com -> Rahul  
    - john.doe@example.com -> John Doe
    - support@techcorp.com -> Techcorp
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
        'careers', 'jobs', 'recruitment', 'recruiter', 'hiring'
    }
    
    # Clean and normalize local part
    local_clean = local_part.lower().strip()
    
    # If it's a generic email, extract company name from domain
    if local_clean in generic_prefixes:
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
                return words[0].capitalize()
            elif len(words) >= 2:
                # Take first two words as first and last name
                return ' '.join(word.capitalize() for word in words[:2])
    
    # Fallback to company name if we can't extract a good name
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
    return "there"


