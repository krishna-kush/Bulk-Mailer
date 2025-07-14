# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush/Bulk-Mailer
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: Template randomizer for manual content variations using custom
#              syntax like {Hi|Hello|Hey} to randomly select options
#
# Components: - Custom syntax parsing
#             - Random option selection
#             - Jinja2 integration
#             - Nested randomization support
#
# License: MIT License
# Created: 2025
#
# ================================================================================
# This file is part of the BULK_MAILER project.
# For complete documentation, visit: https://github.com/krishna-kush/Bulk-Mailer
# ================================================================================

import re
import random
from typing import List, Dict, Any

try:
    from jinja2 import Environment
    from jinja2.ext import Extension
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

class TemplateRandomizer:
    """
    Template randomizer that processes custom syntax for manual content variations.
    Supports syntax like {Hi|Hello|Hey} to randomly select from options.
    """
    
    def __init__(self, logger=None):
        """
        Initialize template randomizer.
        
        Args:
            logger: Logger instance for debugging
        """
        self.logger = logger
        
        # Pattern for randomization syntax: {option1|option2|option3}
        self.randomization_pattern = re.compile(r'\{([^{}]+(?:\|[^{}]+)+)\}')
    
    def process_template(self, template_content: str) -> str:
        """
        Process template content and replace randomization syntax with random selections.
        
        Args:
            template_content: Template content with randomization syntax
            
        Returns:
            Processed template with random selections
        """
        if not template_content:
            return template_content
            
        try:
            # Find all randomization patterns
            processed = template_content
            
            # Process each randomization pattern
            def replace_randomization(match):
                options_string = match.group(1)
                options = [option.strip() for option in options_string.split('|')]
                
                if options:
                    selected = random.choice(options)
                    if self.logger:
                        self.logger.debug(f"Randomization: {options} -> {selected}")
                    return selected
                
                return match.group(0)  # Return original if no options
            
            # Replace all randomization patterns
            processed = self.randomization_pattern.sub(replace_randomization, processed)
            
            if self.logger:
                changes = len(self.randomization_pattern.findall(template_content))
                if changes > 0:
                    self.logger.debug(f"Processed {changes} randomization patterns")
            
            return processed
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Template randomization failed: {e}")
            return template_content  # Return original on error
    
    def find_randomization_patterns(self, template_content: str) -> List[Dict[str, Any]]:
        """
        Find all randomization patterns in template content.
        
        Args:
            template_content: Template content to analyze
            
        Returns:
            List of dictionaries with pattern information
        """
        patterns = []
        
        for match in self.randomization_pattern.finditer(template_content):
            options_string = match.group(1)
            options = [option.strip() for option in options_string.split('|')]
            
            patterns.append({
                'full_match': match.group(0),
                'options_string': options_string,
                'options': options,
                'start': match.start(),
                'end': match.end()
            })
        
        return patterns
    
    def validate_syntax(self, template_content: str) -> Dict[str, Any]:
        """
        Validate randomization syntax in template content.
        
        Args:
            template_content: Template content to validate
            
        Returns:
            Validation results
        """
        patterns = self.find_randomization_patterns(template_content)
        
        validation = {
            'valid': True,
            'pattern_count': len(patterns),
            'patterns': patterns,
            'errors': []
        }
        
        # Check for common syntax errors
        for pattern in patterns:
            options = pattern['options']
            
            # Check for empty options
            if any(not option.strip() for option in options):
                validation['valid'] = False
                validation['errors'].append(f"Empty option in pattern: {pattern['full_match']}")
            
            # Check for single option (not really randomization)
            if len(options) < 2:
                validation['errors'].append(f"Pattern has only one option: {pattern['full_match']}")
        
        return validation
    
    def create_jinja2_filter(self):
        """
        Create a Jinja2 filter for randomization.
        
        Returns:
            Jinja2 filter function
        """
        def randomize_filter(value):
            """Jinja2 filter to process randomization syntax."""
            return self.process_template(str(value))
        
        return randomize_filter
    
    def preview_variations(self, template_content: str, count: int = 5) -> List[str]:
        """
        Generate multiple variations of the template for preview.
        
        Args:
            template_content: Template content with randomization syntax
            count: Number of variations to generate
            
        Returns:
            List of template variations
        """
        variations = []
        
        for _ in range(count):
            variation = self.process_template(template_content)
            variations.append(variation)
        
        return variations


class RandomizerExtension(Extension):
    """
    Jinja2 extension for template randomization.
    Adds a 'randomize' filter to Jinja2 environment.
    """
    
    def __init__(self, environment):
        super().__init__(environment)
        self.randomizer = TemplateRandomizer()
        
        # Add the randomize filter
        environment.filters['randomize'] = self.randomizer.create_jinja2_filter()


def setup_jinja2_environment(env: Environment, logger=None) -> Environment:
    """
    Setup Jinja2 environment with randomization support.
    
    Args:
        env: Jinja2 environment
        logger: Logger instance
        
    Returns:
        Enhanced Jinja2 environment
    """
    if not JINJA2_AVAILABLE:
        if logger:
            logger.warning("Jinja2 not available, randomization features disabled")
        return env
    
    try:
        # Add randomizer extension
        env.add_extension(RandomizerExtension)
        
        # Add custom functions
        randomizer = TemplateRandomizer(logger)
        
        def random_choice(options):
            """Jinja2 function to randomly choose from a list."""
            if isinstance(options, str):
                options = [opt.strip() for opt in options.split('|')]
            return random.choice(options) if options else ''
        
        def random_number(min_val=1, max_val=100):
            """Jinja2 function to generate random numbers."""
            return random.randint(min_val, max_val)
        
        # Add functions to environment
        env.globals['random_choice'] = random_choice
        env.globals['random_number'] = random_number
        
        if logger:
            logger.info("Jinja2 environment enhanced with randomization features")
        
        return env
        
    except Exception as e:
        if logger:
            logger.error(f"Failed to setup Jinja2 randomization: {e}")
        return env


# Standalone function for simple randomization without Jinja2
def randomize_content(content: str, logger=None) -> str:
    """
    Standalone function to randomize content without Jinja2 dependency.
    
    Args:
        content: Content with randomization syntax
        logger: Logger instance
        
    Returns:
        Randomized content
    """
    randomizer = TemplateRandomizer(logger)
    return randomizer.process_template(content)
