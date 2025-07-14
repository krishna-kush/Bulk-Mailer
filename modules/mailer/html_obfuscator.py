# ================================================================================
# BULK_MAILER - Professional Email Campaign Manager
# ================================================================================
#
# Author: Krishna Kushwaha
# GitHub: https://github.com/krishna-kush
# Project: BULK_MAILER - Enterprise Email Campaign Management System
# Repository: https://github.com/krishna-kush/Bulk-Mailer
#
# Description: HTML template obfuscator to prevent spam detection by making
#              subtle variations in HTML structure without changing appearance
#
# Components: - Random whitespace injection
#             - CSS property reordering
#             - HTML attribute shuffling
#             - Comment insertion
#             - Class name variations
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
import string
from typing import Dict, List, Optional

class HTMLObfuscator:
    """
    HTML template obfuscator that makes subtle variations to HTML structure
    without changing the visual appearance or functionality.
    """
    
    def __init__(self, logger=None):
        """
        Initialize HTML obfuscator.
        
        Args:
            logger: Logger instance for debugging
        """
        self.logger = logger
        
        # Obfuscation techniques configuration
        self.techniques = {
            'whitespace_injection': True,
            'css_reordering': True,
            'css_class_reordering': True,
            'attribute_shuffling': True,
            'comment_insertion': True,
            'class_variations': True,
            'style_formatting': True
        }
    
    def obfuscate_html(self, html_content: str, intensity: str = 'medium') -> str:
        """
        Obfuscate HTML content with specified intensity.
        
        Args:
            html_content: Original HTML content
            intensity: Obfuscation intensity ('light', 'medium', 'heavy')
            
        Returns:
            Obfuscated HTML content
        """
        if not html_content:
            return html_content
            
        try:
            # Set obfuscation intensity
            self._set_intensity(intensity)
            
            # Apply obfuscation techniques
            obfuscated = html_content
            
            if self.techniques['whitespace_injection']:
                obfuscated = self._inject_whitespace(obfuscated)
            
            if self.techniques['css_reordering']:
                obfuscated = self._reorder_css_properties(obfuscated)

            # CSS class reordering temporarily disabled to prevent CSS loss
            # if self.techniques['css_class_reordering']:
            #     obfuscated = self._reorder_css_classes(obfuscated)

            if self.techniques['attribute_shuffling']:
                obfuscated = self._shuffle_attributes(obfuscated)
            
            if self.techniques['comment_insertion']:
                obfuscated = self._insert_comments(obfuscated)
            
            if self.techniques['class_variations']:
                obfuscated = self._vary_class_names(obfuscated)
            
            if self.techniques['style_formatting']:
                obfuscated = self._vary_style_formatting(obfuscated)
            
            if self.logger:
                self.logger.debug(f"HTML obfuscated with {intensity} intensity")
            
            return obfuscated
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"HTML obfuscation failed: {e}")
            return html_content  # Return original on error
    
    def _set_intensity(self, intensity: str):
        """Set obfuscation intensity level."""
        if intensity == 'light':
            self.techniques.update({
                'whitespace_injection': True,
                'css_reordering': False,
                'css_class_reordering': False,
                'attribute_shuffling': False,
                'comment_insertion': True,
                'class_variations': False,
                'style_formatting': True
            })
        elif intensity == 'medium':
            self.techniques.update({
                'whitespace_injection': True,
                'css_reordering': True,
                'css_class_reordering': False,  # Disabled - can break complex CSS
                'attribute_shuffling': True,
                'comment_insertion': True,
                'class_variations': True,
                'style_formatting': True
            })
        elif intensity == 'heavy':
            self.techniques.update({
                'whitespace_injection': True,
                'css_reordering': True,
                'css_class_reordering': True,  # Re-enabled for heavy mode
                'attribute_shuffling': True,
                'comment_insertion': True,
                'class_variations': True,
                'style_formatting': True
            })
    
    def _inject_whitespace(self, html: str) -> str:
        """Inject random whitespace in safe locations."""
        # Add random spaces/tabs around HTML tags
        html = re.sub(r'(<[^>]+>)', lambda m: self._add_random_whitespace(m.group(1)), html)
        
        # Add random line breaks in safe locations
        html = re.sub(r'(</div>|</p>|</span>)', lambda m: m.group(1) + self._random_newlines(), html)
        
        return html
    
    def _add_random_whitespace(self, tag: str) -> str:
        """Add random whitespace around a tag."""
        if random.random() < 0.3:  # 30% chance
            spaces = ' ' * random.randint(0, 2)
            return spaces + tag + spaces
        return tag
    
    def _random_newlines(self) -> str:
        """Generate random newlines."""
        if random.random() < 0.4:  # 40% chance
            return '\n' * random.randint(1, 2)
        return ''
    
    def _reorder_css_properties(self, html: str) -> str:
        """Randomly reorder CSS properties in style attributes."""
        def reorder_style(match):
            style_content = match.group(1)
            properties = [prop.strip() for prop in style_content.split(';') if prop.strip()]
            
            # Shuffle properties randomly
            random.shuffle(properties)
            
            return f'style="{"; ".join(properties)}"'
        
        return re.sub(r'style="([^"]*)"', reorder_style, html)

    def _reorder_css_classes(self, html: str) -> str:
        """
        Reorder CSS class definitions and shuffle properties within each class.
        This implements the technique you suggested: changing the order of CSS classes
        and shuffling properties within each class definition.
        """
        # Find the <style> section(s)
        def reorder_style_section(match):
            style_content = match.group(1)

            # Extract individual CSS class definitions (excludes system selectors)
            css_classes = self._extract_css_class_definitions(style_content)

            # Extract non-class CSS rules (*, body, @media, etc.) to preserve them
            non_class_rules = self._extract_non_class_rules(style_content)

            if len(css_classes) < 2:
                return match.group(0)  # Not enough classes to reorder

            # Shuffle the order of CSS class definitions
            random.shuffle(css_classes)

            # Shuffle properties within each class and add random spacing
            reordered_classes = []
            for class_def in css_classes:
                reordered_class = self._shuffle_class_properties(class_def)
                reordered_classes.append(reordered_class)

            # Reconstruct the style section with random spacing
            reconstructed = self._reconstruct_style_section(reordered_classes, non_class_rules)

            return f'<style>{reconstructed}</style>'

        # Apply to all <style> sections
        return re.sub(r'<style[^>]*>(.*?)</style>', reorder_style_section, html, flags=re.DOTALL)

    def _extract_css_class_definitions(self, style_content: str) -> list:
        """Extract individual CSS class definitions from style content."""

        # Extract ALL CSS class definitions without removing any content
        # This ensures we don't lose any CSS rules
        pattern = r'(\.[a-zA-Z][a-zA-Z0-9_-]*\s*\{[^}]*\})'
        matches = re.findall(pattern, style_content, re.DOTALL)

        # Filter and clean matches
        filtered_matches = []
        system_selectors = ['*', 'body', 'html', 'hover', 'focus', 'active', 'visited', 'before', 'after']

        for match in matches:
            match = match.strip()
            if not match:
                continue

            # Extract the selector part (before the opening brace)
            selector_match = re.match(r'(\.[a-zA-Z][a-zA-Z0-9_-]*)', match)
            if not selector_match:
                continue

            selector = selector_match.group(1)
            class_name = selector[1:]  # Remove the dot

            # Skip system selectors and pseudo-classes
            if class_name in system_selectors:
                continue
            if ':' in class_name or '@' in class_name:  # Skip pseudo-classes and at-rules
                continue

            filtered_matches.append(match)

        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in filtered_matches:
            # Extract class name for duplicate checking
            selector_match = re.match(r'(\.[a-zA-Z][a-zA-Z0-9_-]*)', match)
            if selector_match:
                class_name = selector_match.group(1)
                if class_name not in seen:
                    seen.add(class_name)
                    unique_matches.append(match)

        return unique_matches

    def _extract_non_class_rules(self, style_content: str) -> list:
        """Extract non-class CSS rules (*, body, @media, etc.) that should be preserved."""
        non_class_rules = []

        # Handle media queries (they can contain nested rules)
        media_pattern = r'(@media[^{]*\{(?:[^{}]*\{[^}]*\}[^{}]*)*\})'
        media_matches = re.findall(media_pattern, style_content, re.DOTALL | re.IGNORECASE)
        for match in media_matches:
            if match.strip():
                non_class_rules.append(match.strip())

        # Handle keyframes (they can contain nested rules)
        keyframes_pattern = r'(@keyframes[^{]*\{(?:[^{}]*\{[^}]*\}[^{}]*)*\})'
        keyframes_matches = re.findall(keyframes_pattern, style_content, re.DOTALL | re.IGNORECASE)
        for match in keyframes_matches:
            if match.strip():
                non_class_rules.append(match.strip())

        # Handle simple patterns
        patterns = [
            r'(\*\s*\{[^}]*\})',  # Universal selector
            r'(body\s*\{[^}]*\})',  # Body selector
            r'(html\s*\{[^}]*\})',  # HTML selector
            r'(@import[^;]*;)',  # Import statements
            r'(@font-face\s*\{[^}]*\})',  # Font face
        ]

        for pattern in patterns:
            matches = re.findall(pattern, style_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                if match.strip():
                    non_class_rules.append(match.strip())

        return non_class_rules

    def _shuffle_class_properties(self, class_definition: str) -> str:
        """Shuffle CSS properties within a single class definition."""
        # Extract class name and properties
        match = re.match(r'(\.[a-zA-Z][a-zA-Z0-9_-]*)\s*\{([^}]*)\}', class_definition, re.DOTALL)

        if not match:
            return class_definition

        class_name = match.group(1)
        properties_content = match.group(2)

        # Split properties and clean them
        properties = []
        for prop in properties_content.split(';'):
            prop = prop.strip()
            if prop:  # Skip empty properties
                properties.append(prop)

        if len(properties) > 1:
            # Shuffle the properties
            random.shuffle(properties)

        # Add random spacing and formatting
        formatted_properties = []
        for prop in properties:
            # Add random spacing around colons
            if ':' in prop:
                if random.random() < 0.5:
                    prop = prop.replace(':', ': ')
                else:
                    prop = prop.replace(':', ':')
            formatted_properties.append(prop)

        # Reconstruct with random indentation and line breaks
        if len(formatted_properties) > 2 and random.random() < 0.7:
            # Multi-line format with random indentation
            indent = ' ' * random.randint(8, 16)
            properties_str = f'\n{indent}' + f';\n{indent}'.join(formatted_properties)
            if properties_str.strip():
                properties_str += ';\n        '  # Add final semicolon and closing indent
        else:
            # Single line format
            properties_str = '; '.join(formatted_properties)
            if properties_str:
                properties_str += ';'

        return f'{class_name} {{{properties_str}}}'

    def _reconstruct_style_section(self, css_classes: list, non_class_rules: list = None) -> str:
        """Reconstruct the style section with random spacing between classes."""
        if not css_classes and not non_class_rules:
            return ''

        all_rules = []

        # Add non-class rules first (*, body, @media, etc.)
        if non_class_rules:
            all_rules.extend(non_class_rules)

        # Add class rules
        if css_classes:
            all_rules.extend(css_classes)

        if not all_rules:
            return ''

        # Add random spacing between rule definitions
        result_parts = []
        for i, rule in enumerate(all_rules):
            result_parts.append(rule)

            # Add random spacing between rules (except after the last one)
            if i < len(all_rules) - 1:
                spacing = '\n' * random.randint(1, 3)
                result_parts.append(spacing)

        return '\n        ' + '\n        '.join(result_parts) + '\n    '
    
    def _shuffle_attributes(self, html: str) -> str:
        """Randomly shuffle HTML attributes (except critical ones) - SAFER VERSION."""
        def shuffle_attrs(match):
            tag_content = match.group(1)

            # Extract tag name and attributes
            parts = tag_content.split()
            if len(parts) < 3:  # Need at least tag + 2 attributes to shuffle
                return match.group(0)

            tag_name = parts[0]
            attrs = parts[1:]

            # Don't shuffle critical attributes that can break functionality
            critical_attrs = []
            safe_attrs = []

            for attr in attrs:
                # Keep critical attributes in original position
                if any(attr.startswith(critical) for critical in [
                    'src=', 'href=', 'id=', 'name=', 'alt=', 'class=', 'style=', 'type=', 'value='
                ]):
                    critical_attrs.append(attr)
                else:
                    # Only shuffle very safe attributes
                    if any(attr.startswith(safe) for safe in ['title=', 'data-', 'aria-']):
                        safe_attrs.append(attr)
                    else:
                        critical_attrs.append(attr)  # Treat as critical if unsure

            # Only shuffle if we have safe attributes to shuffle
            if len(safe_attrs) > 1:
                random.shuffle(safe_attrs)

            # Reconstruct tag
            all_attrs = critical_attrs + safe_attrs
            return f'<{tag_name} {" ".join(all_attrs)}>'

        return re.sub(r'<(\w+[^>]*)>', shuffle_attrs, html)
    
    def _insert_comments(self, html: str) -> str:
        """Insert random HTML comments that look natural."""
        # More natural, less revealing comments
        comments = [
            '<!-- Main content area -->',
            '<!-- Section wrapper -->',
            '<!-- Content block -->',
            '<!-- Layout container -->',
            '<!-- Display section -->',
            '<!-- Information panel -->',
            '<!-- Contact details -->',
            '<!-- Header section -->',
            '<!-- Footer area -->',
            '<!-- Navigation block -->',
            '<!-- Media content -->',
            '<!-- Text content -->',
            '<!-- Button group -->',
            '<!-- Link section -->',
            '<!-- Image container -->',
            '<!-- Form elements -->',
            '<!-- Data section -->',
            '<!-- Content wrapper -->',
            '<!-- Display block -->',
            '<!-- Interface element -->'
        ]

        # Insert comments before major sections with higher frequency
        insertion_points = ['<div', '<p', '<table', '<style', '<a', '<img', '<span']

        for point in insertion_points:
            if random.random() < 0.4:  # 40% chance (increased from 20%)
                comment = random.choice(comments)
                html = html.replace(point, f'{comment}\n{point}', 1)

        return html
    
    def _vary_class_names(self, html: str) -> str:
        """Consistently rename CSS classes throughout the document."""
        # Extract all class names from CSS and HTML
        class_mappings = self._generate_class_mappings(html)

        if not class_mappings:
            return html

        # Apply mappings to both CSS definitions and HTML usage
        modified_html = html

        for original_class, new_class in class_mappings.items():
            # Replace in CSS definitions (e.g., .email-container { ... })
            modified_html = re.sub(
                rf'\.{re.escape(original_class)}\b',
                f'.{new_class}',
                modified_html
            )

            # Replace in HTML class attributes
            modified_html = re.sub(
                rf'\bclass="([^"]*\b){re.escape(original_class)}\b([^"]*)"',
                rf'class="\1{new_class}\2"',
                modified_html
            )

            # Handle multiple classes in same attribute
            modified_html = re.sub(
                rf'\bclass="([^"]*\s){re.escape(original_class)}\b(\s[^"]*)"',
                rf'class="\1{new_class}\2"',
                modified_html
            )

            # Handle single class attributes
            modified_html = re.sub(
                rf'\bclass="{re.escape(original_class)}"',
                f'class="{new_class}"',
                modified_html
            )

        return modified_html

    def _generate_class_mappings(self, html: str) -> dict:
        """Generate consistent random mappings for CSS class names."""
        # Find all CSS class definitions
        css_classes = set()

        # Extract from CSS definitions (.class-name) - exclude system selectors
        css_class_pattern = r'\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{'
        css_matches = re.findall(css_class_pattern, html)

        # Filter out system selectors and pseudo-classes
        system_selectors = ['*', 'body', 'html', 'hover', 'focus', 'active', 'visited', 'before', 'after']
        for match in css_matches:
            # Skip system selectors and pseudo-classes
            if match not in system_selectors and ':' not in match and '@' not in match:
                css_classes.add(match)

        # Extract from HTML class attributes
        html_class_pattern = r'class="([^"]+)"'
        html_matches = re.findall(html_class_pattern, html)
        for match in html_matches:
            # Split multiple classes
            classes = match.split()
            for cls in classes:
                # Only add valid class names (no system selectors)
                if cls and cls not in system_selectors and ':' not in cls and '@' not in cls:
                    css_classes.add(cls)

        # Generate consistent random mappings
        mappings = {}
        for class_name in css_classes:
            if class_name:  # Skip empty strings
                if self.techniques.get('class_variations', False):
                    # Check if we're in heavy mode by looking at other techniques
                    is_heavy_mode = (
                        self.techniques.get('whitespace_injection', False) and
                        self.techniques.get('css_reordering', False) and
                        self.techniques.get('attribute_shuffling', False) and
                        self.techniques.get('comment_insertion', False) and
                        self.techniques.get('style_formatting', False)
                    )

                    if is_heavy_mode:
                        # HEAVY MODE: Generate completely random class names
                        # Use 6-8 character random strings starting with a letter
                        length = random.randint(6, 8)
                        first_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                        remaining_chars = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=length-1))
                        mappings[class_name] = f"{first_char}{remaining_chars}"
                    else:
                        # MEDIUM MODE: Append random suffix to preserve readability
                        suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=2))
                        mappings[class_name] = f"{class_name}-{suffix}"
                else:
                    # No class variations
                    mappings[class_name] = class_name

        return mappings
    
    def _vary_style_formatting(self, html: str) -> str:
        """Vary CSS formatting (spacing, quotes, etc.)."""
        # Randomly add/remove spaces around colons and semicolons
        def vary_css_spacing(match):
            style_content = match.group(1)
            
            # Vary spacing around colons
            if random.random() < 0.5:
                style_content = re.sub(r':\s*', ': ', style_content)
            else:
                style_content = re.sub(r':\s*', ':', style_content)
            
            # Vary spacing around semicolons
            if random.random() < 0.5:
                style_content = re.sub(r';\s*', '; ', style_content)
            else:
                style_content = re.sub(r';\s*', ';', style_content)
            
            return f'style="{style_content}"'
        
        return re.sub(r'style="([^"]*)"', vary_css_spacing, html)
