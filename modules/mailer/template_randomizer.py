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
        # Use a simpler approach that handles most cases
        self.randomization_pattern = re.compile(r'\{([^{}]*(?:\|[^{}]*)+)\}', re.DOTALL)

        # Storage for synchronized randomization values
        self.sync_values = {}
    
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
            # Use custom parser for complex patterns with nested braces
            processed = self._process_with_balanced_braces(template_content)

            if self.logger:
                original_patterns = len(re.findall(r'\{[^}]*\|[^}]*\}', template_content))
                remaining_patterns = len(re.findall(r'\{[^}]*\|[^}]*\}', processed))
                changes = original_patterns - remaining_patterns
                if changes > 0:
                    self.logger.debug(f"Processed {changes} randomization patterns")

            return processed

        except Exception as e:
            if self.logger:
                self.logger.error(f"Template randomization failed: {e}")
            return template_content  # Return original on error

    def _process_with_balanced_braces(self, content: str) -> str:
        """
        Advanced randomization processor with full CSS support.
        Handles complex patterns including CSS properties with nested braces.
        """
        # Clear sync values for each new template processing
        self.sync_values = {}

        # Use regex to find all randomization patterns first
        pattern = re.compile(r'\{([^{}]*\|[^{}]*)\}')

        def replace_pattern(match):
            inner_content = match.group(1)

            # Check for synchronized randomization syntax: @sync_key:option1|option2|option3
            if inner_content.startswith('@'):
                return self._process_synchronized_randomization(inner_content)

            # Determine context based on position
            position = match.start()
            context = 'HTML'  # Default context

            # Check if we're in a CSS context
            if self._is_css_context(content, position):
                context = 'CSS'
                selected = self._process_css_randomization_advanced(inner_content)
            else:
                selected = self._process_html_randomization(inner_content)

            if self.logger:
                self.logger.debug(f"{context} randomization: {selected[:50]}...")

            return selected

        # Replace all randomization patterns
        result = pattern.sub(replace_pattern, content)

        # Apply CSS property shuffling after randomization
        result = self._shuffle_css_properties(result)

        return result

    def _extract_css_blocks(self, content: str) -> list:
        """Extract all CSS blocks from the content for context awareness."""
        css_blocks = []

        # Find all <style> blocks
        style_pattern = r'<style[^>]*>(.*?)</style>'
        matches = re.finditer(style_pattern, content, re.DOTALL | re.IGNORECASE)

        for match in matches:
            css_blocks.append({
                'start': match.start(),
                'end': match.end(),
                'content': match.group(1)
            })

        return css_blocks

    def _extract_randomization_pattern(self, content: str, start_pos: int) -> tuple:
        """
        Extract a complete randomization pattern with proper brace balancing.
        Returns (start, end, inner_content) or None if no valid pattern.
        """
        if content[start_pos] != '{':
            return None

        brace_count = 0
        i = start_pos
        in_string = False
        string_char = None

        while i < len(content):
            char = content[i]

            # Handle string literals (preserve braces inside strings)
            if char in ['"', "'"] and (i == 0 or content[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    in_string = False
                    string_char = None

            # Count braces only when not in strings
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1

                    if brace_count == 0:
                        # Found complete pattern
                        inner_content = content[start_pos + 1:i]
                        return (start_pos, i + 1, inner_content)

            i += 1

        # No matching closing brace found
        return None

    def _determine_context(self, content: str, position: int, css_blocks: list) -> str:
        """Determine if position is in CSS, HTML, or other context."""
        for block in css_blocks:
            if block['start'] <= position <= block['end']:
                return 'CSS'

        return 'HTML'

    def _process_css_randomization_advanced(self, inner_content: str) -> str:
        """
        Advanced CSS randomization that preserves CSS syntax.
        """
        options = [option.strip() for option in inner_content.split('|')]

        if not options:
            return inner_content

        # Select a random option
        selected_option = random.choice(options)

        # For CSS randomization, don't add extra syntax - assume template is properly formatted
        return selected_option.strip()

    def _ensure_css_syntax(self, css_text: str) -> str:
        """
        Ensure CSS text has proper syntax structure.
        """
        css_text = css_text.strip()

        # If it's a complete CSS property (has colon), ensure it ends with semicolon
        # But don't add semicolon if it already has one
        if ':' in css_text and not css_text.endswith(';'):
            css_text += ';'

        return css_text

    def _process_html_randomization(self, inner_content: str) -> str:
        """Process HTML/text randomization."""
        options = [option.strip() for option in inner_content.split('|')]
        return random.choice(options) if options else inner_content

    def _process_synchronized_randomization(self, inner_content: str) -> str:
        """
        Process synchronized randomization patterns.
        Syntax: @sync_key:option1|option2|option3
        All patterns with the same sync_key will use the same selected value.
        """
        # Parse the synchronized pattern
        if ':' not in inner_content:
            # Invalid syntax, treat as regular randomization
            return self._process_html_randomization(inner_content[1:])  # Remove @

        sync_key, options_string = inner_content[1:].split(':', 1)  # Remove @ and split
        options = [option.strip() for option in options_string.split('|')]

        if not options:
            return inner_content

        # Check if we already have a value for this sync key
        if sync_key in self.sync_values:
            selected_value = self.sync_values[sync_key]
            if self.logger:
                self.logger.debug(f"Using cached sync value for '{sync_key}': {selected_value}")
        else:
            # First time seeing this sync key, select a random value
            selected_value = random.choice(options)
            self.sync_values[sync_key] = selected_value
            if self.logger:
                self.logger.debug(f"New sync value for '{sync_key}': {selected_value}")

        return selected_value

    def _fix_css_syntax(self, css_text: str) -> str:
        """
        Fix common CSS syntax issues in randomization options.
        """
        css_text = css_text.strip()

        # Ensure property ends with semicolon if it's a complete property
        if ':' in css_text and not css_text.endswith(';') and not css_text.endswith('}'):
            css_text += ';'

        return css_text

    def _validate_css_property(self, css_text: str) -> bool:
        """
        Validate CSS property syntax.
        """
        css_text = css_text.strip()

        # Allow complete CSS rules (property: value;)
        if ':' in css_text:
            parts = css_text.split(':', 1)
            if len(parts) == 2:
                property_name = parts[0].strip()
                property_value = parts[1].strip().rstrip(';')

                # Basic validation
                if property_name and property_value:
                    # Property name should be valid CSS identifier
                    if re.match(r'^[a-zA-Z-]+$', property_name):
                        return True

        # Allow CSS values (for cases where property is separate)
        if not ':' in css_text:
            # Could be just a value
            return bool(css_text)

        return False

    def _is_css_context(self, content: str, position: int) -> bool:
        """
        Determine if the current position is within a CSS context.
        """
        # Look backwards to find if we're inside a <style> tag
        before_content = content[:position]

        # Find the last <style> and </style> tags
        last_style_open = before_content.rfind('<style')
        last_style_close = before_content.rfind('</style>')

        # If we found a <style> tag and it's after the last </style> tag, we're in CSS
        in_style_tag = last_style_open > last_style_close and last_style_open != -1

        if not in_style_tag:
            return False

        # Additional check: make sure we're actually inside CSS rules, not in HTML attributes
        # Look for CSS selector patterns before this position
        css_content = before_content[last_style_open:]

        # Check if we're inside a CSS rule block (between { and })
        open_braces = css_content.count('{')
        close_braces = css_content.count('}')

        # If we have more opening braces than closing braces, we're inside a CSS rule
        return open_braces > close_braces

    def _process_css_randomization(self, inner_content: str) -> str:
        """
        Process CSS-specific randomization patterns.
        Handles patterns like: color: #333|color: #444|background: white
        """
        options = [option.strip() for option in inner_content.split('|')]

        if not options:
            return inner_content

        # Validate that all options are valid CSS
        valid_options = []
        for option in options:
            if self._is_valid_css_property(option):
                valid_options.append(option)
            else:
                if self.logger:
                    self.logger.warning(f"Invalid CSS option skipped: {option}")

        if valid_options:
            return random.choice(valid_options)
        else:
            # If no valid options, return the first one as fallback
            return options[0] if options else inner_content

    def _is_valid_css_property(self, css_text: str) -> bool:
        """
        Basic validation for CSS property syntax.
        Checks for property: value; format
        """
        css_text = css_text.strip()

        # Check for basic CSS property format: property: value
        if ':' not in css_text:
            return False

        # Split on first colon
        parts = css_text.split(':', 1)
        if len(parts) != 2:
            return False

        property_name = parts[0].strip()
        property_value = parts[1].strip()

        # Basic validation
        if not property_name or not property_value:
            return False

        # Property name should be valid CSS identifier
        if not re.match(r'^[a-zA-Z-]+$', property_name):
            return False

        return True

    def _shuffle_css_properties(self, content: str) -> str:
        """
        Shuffle CSS properties within each CSS rule AND shuffle the order of CSS rules
        for maximum anti-spam protection.
        """
        import re
        import random

        def shuffle_css_rule(match):
            """Shuffle properties within a single CSS rule."""
            selector = match.group(1)
            properties_block = match.group(2)

            # Don't shuffle @media rules or other special selectors
            if selector.strip().startswith('@'):
                return match.group(0)

            # Split properties by semicolon
            properties = [prop.strip() for prop in properties_block.split(';') if prop.strip()]

            # Only shuffle if we have multiple properties
            if len(properties) > 1:
                random.shuffle(properties)

            # Reconstruct the CSS rule
            shuffled_properties = ';\n            '.join(properties)
            if shuffled_properties:
                shuffled_properties += ';'

            return f"{selector} {{\n            {shuffled_properties}\n        }}"

        def shuffle_css_rules(style_content):
            """Shuffle the order of CSS rules while preserving media queries and structure."""
            # Split content into lines for easier processing
            lines = style_content.split('\n')

            # Separate different types of content
            priority_rules = []  # *, body
            regular_rules = []   # other CSS rules
            media_query_content = []  # @media blocks

            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Skip empty lines
                if not line:
                    i += 1
                    continue

                # Handle @media blocks
                if line.startswith('@media'):
                    # Collect entire @media block
                    media_block = [lines[i]]
                    i += 1
                    brace_count = line.count('{') - line.count('}')

                    while i < len(lines) and brace_count > 0:
                        media_block.append(lines[i])
                        brace_count += lines[i].count('{') - lines[i].count('}')
                        i += 1

                    media_query_content.extend(media_block)
                    continue

                # Handle CSS rules
                if '{' in line:
                    # Collect entire CSS rule
                    rule_block = [lines[i]]
                    i += 1
                    brace_count = line.count('{') - line.count('}')

                    while i < len(lines) and brace_count > 0:
                        rule_block.append(lines[i])
                        brace_count += lines[i].count('{') - lines[i].count('}')
                        i += 1

                    # Determine rule type
                    selector = line.split('{')[0].strip()
                    if selector == '*' or selector == 'body':
                        priority_rules.extend(rule_block)
                    else:
                        regular_rules.extend(rule_block)
                    continue

                i += 1

            # Shuffle regular rules (but keep them as complete blocks)
            if regular_rules:
                # Group rules by complete blocks
                rule_blocks = []
                current_block = []

                for line in regular_rules:
                    current_block.append(line)
                    if '}' in line:
                        rule_blocks.append(current_block)
                        current_block = []

                # Shuffle the blocks
                if len(rule_blocks) > 1:
                    random.shuffle(rule_blocks)

                # Flatten back to lines
                regular_rules = []
                for block in rule_blocks:
                    regular_rules.extend(block)

            # Apply property shuffling to all CSS rules
            def shuffle_properties_in_lines(lines):
                """Apply property shuffling to CSS rules in a list of lines."""
                result_lines = []
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if '{' in line and not line.strip().startswith('@'):
                        # This is a CSS rule, collect it and shuffle properties
                        rule_lines = [line]
                        i += 1
                        brace_count = line.count('{') - line.count('}')

                        while i < len(lines) and brace_count > 0:
                            rule_lines.append(lines[i])
                            brace_count += lines[i].count('{') - lines[i].count('}')
                            i += 1

                        # Reconstruct rule and apply shuffling
                        rule_text = '\n'.join(rule_lines)
                        css_rule_pattern = re.compile(r'([^{}]+?)\s*\{\s*([^{}]*?)\s*\}', re.DOTALL)
                        match = css_rule_pattern.match(rule_text)
                        if match:
                            shuffled_rule = shuffle_css_rule(match)
                            result_lines.extend(shuffled_rule.split('\n'))
                        else:
                            result_lines.extend(rule_lines)
                    else:
                        result_lines.append(line)
                        i += 1

                return result_lines

            # Apply property shuffling to all sections
            priority_rules = shuffle_properties_in_lines(priority_rules)
            regular_rules = shuffle_properties_in_lines(regular_rules)
            media_query_content = shuffle_properties_in_lines(media_query_content)

            # Combine all parts: priority + shuffled regular + media queries
            all_lines = priority_rules + regular_rules + media_query_content

            return '\n'.join(all_lines)

        # Only process content within <style> tags
        def process_style_block(style_match):
            style_content = style_match.group(1)

            # Apply rule shuffling and property shuffling
            shuffled_style = shuffle_css_rules(style_content)

            return f"<style>\n        {shuffled_style}\n    </style>"

        # Find and process all <style> blocks
        style_pattern = re.compile(r'<style[^>]*>(.*?)</style>', re.DOTALL | re.IGNORECASE)
        result = style_pattern.sub(process_style_block, content)

        return result

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
