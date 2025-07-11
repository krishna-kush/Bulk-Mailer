import re
import os
from datetime import datetime
from typing import Dict, Any, Optional
from modules.core.utils import extract_name_from_email

try:
    from jinja2 import Template, Environment, FileSystemLoader, meta
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

class EmailPersonalizer:
    """
    Advanced email personalization system with Jinja2 template engine support.
    Supports multiple data sources and graceful fallback for missing data.
    """
    
    def __init__(self, config_settings: Dict, base_dir: str, logger):
        """
        Initialize email personalizer.
        
        Args:
            config_settings: Personalization configuration
            base_dir: Base directory for template files
            logger: Logger instance
        """
        self.config = config_settings
        self.base_dir = base_dir
        self.logger = logger
        
        # Initialize Jinja2 environment if available
        if JINJA2_AVAILABLE:
            template_dir = os.path.join(base_dir, "templates", "email_templates")
            self.jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=True,  # Auto-escape HTML for security
                trim_blocks=True,
                lstrip_blocks=True
            )
            self.logger.info("Jinja2 template engine initialized")
        else:
            self.jinja_env = None
            self.logger.warning("Jinja2 not available, falling back to basic string replacement")
        
        # Default personalization mappings
        self.default_mappings = {
            'recipient_name': 'email_extraction',
            'sender_name': 'static:[SENDER_NAME]',
            'sender_title': 'static:[SENDER_TITLE]',
            'company_name': 'database_column:company_name',
            'current_date': 'dynamic:current_date',
            'current_year': 'dynamic:current_year',
            'industry': 'database_column:industry',
            'website': 'database_column:website'
        }
        
        # Load custom mappings from config
        self.personalization_mappings = self._load_personalization_config()
    
    def _load_personalization_config(self) -> Dict[str, str]:
        """Load personalization mappings from configuration."""
        mappings = self.default_mappings.copy()
        
        # Override with config settings if available
        config_mappings = self.config.get('personalization_mappings', {})
        if config_mappings:
            mappings.update(config_mappings)
            self.logger.debug(f"Loaded {len(config_mappings)} custom personalization mappings")
        
        return mappings
    
    def personalize_email(self, template_content: str, recipient_data: Dict, 
                         template_filename: Optional[str] = None) -> str:
        """
        Personalize email content with recipient-specific data.
        
        Args:
            template_content: Raw HTML template content
            recipient_data: Recipient information dictionary
            template_filename: Optional template filename for Jinja2 loading
            
        Returns:
            Personalized HTML content
        """
        try:
            # Extract personalization data
            personalization_data = self._extract_personalization_data(recipient_data)
            
            # Use Jinja2 if available and template has Jinja2 syntax
            if JINJA2_AVAILABLE and self._has_jinja2_syntax(template_content):
                return self._personalize_with_jinja2(template_content, personalization_data, template_filename)
            else:
                # Fallback to basic string replacement
                return self._personalize_with_replacement(template_content, personalization_data)
                
        except Exception as e:
            self.logger.error(f"Error personalizing email: {e}")
            # Return original content if personalization fails
            return template_content
    
    def _extract_personalization_data(self, recipient_data: Dict) -> Dict[str, Any]:
        """Extract personalization data from recipient information."""
        data = {}
        
        for placeholder, source in self.personalization_mappings.items():
            try:
                value = self._get_value_from_source(source, recipient_data)
                if value is not None:
                    data[placeholder] = value
                else:
                    # Log warning for missing data but continue
                    self.logger.warning(f"No data found for placeholder '{placeholder}' from source '{source}'")
                    data[placeholder] = f"[{placeholder.upper()}]"  # Fallback placeholder
                    
            except Exception as e:
                self.logger.warning(f"Error extracting data for '{placeholder}': {e}")
                data[placeholder] = f"[{placeholder.upper()}]"
        
        return data
    
    def _get_value_from_source(self, source: str, recipient_data: Dict) -> Optional[str]:
        """Get value from specified data source."""
        if source == 'email_extraction':
            # Extract name from email address
            email = recipient_data.get('email', '')
            return extract_name_from_email(email) if email else None
            
        elif source.startswith('static:'):
            # Static value
            return source[7:]  # Remove 'static:' prefix
            
        elif source.startswith('database_column:'):
            # Database column value
            column_name = source[16:]  # Remove 'database_column:' prefix
            return recipient_data.get(column_name)
            
        elif source.startswith('dynamic:'):
            # Dynamic value generation
            dynamic_type = source[8:]  # Remove 'dynamic:' prefix
            return self._generate_dynamic_value(dynamic_type)
            
        else:
            # Direct key lookup in recipient data
            return recipient_data.get(source)
    
    def _generate_dynamic_value(self, dynamic_type: str) -> Optional[str]:
        """Generate dynamic values like dates, etc."""
        now = datetime.now()
        
        if dynamic_type == 'current_date':
            return now.strftime('%B %d, %Y')  # e.g., "July 11, 2025"
        elif dynamic_type == 'current_year':
            return str(now.year)
        elif dynamic_type == 'current_month':
            return now.strftime('%B')  # e.g., "July"
        elif dynamic_type == 'current_day':
            return str(now.day)
        else:
            return None
    
    def _has_jinja2_syntax(self, content: str) -> bool:
        """Check if content contains Jinja2 template syntax."""
        jinja2_patterns = [
            r'\{\{.*?\}\}',  # {{ variable }}
            r'\{%.*?%\}',    # {% tag %}
            r'\{#.*?#\}'     # {# comment #}
        ]
        
        for pattern in jinja2_patterns:
            if re.search(pattern, content):
                return True
        return False
    
    def _personalize_with_jinja2(self, template_content: str, data: Dict[str, Any], 
                                template_filename: Optional[str] = None) -> str:
        """Personalize using Jinja2 template engine."""
        try:
            if template_filename and os.path.exists(os.path.join(self.base_dir, "templates", "email_templates", template_filename)):
                # Load template from file
                template = self.jinja_env.get_template(template_filename)
            else:
                # Create template from string
                template = Template(template_content, environment=self.jinja_env)
            
            # Render template with data
            rendered = template.render(**data)
            
            # Check for undefined variables
            undefined_vars = self._find_undefined_variables(template_content, data)
            if undefined_vars:
                self.logger.warning(f"Undefined template variables: {', '.join(undefined_vars)}")
            
            return rendered
            
        except Exception as e:
            self.logger.error(f"Jinja2 rendering error: {e}")
            # Fallback to string replacement
            return self._personalize_with_replacement(template_content, data)
    
    def _personalize_with_replacement(self, template_content: str, data: Dict[str, Any]) -> str:
        """Fallback personalization using string replacement."""
        content = template_content
        
        # Replace Jinja2-style placeholders: {{ placeholder }}
        for placeholder, value in data.items():
            jinja2_pattern = f"{{{{{placeholder}}}}}"
            if jinja2_pattern in content:
                content = content.replace(jinja2_pattern, str(value))
        
        # Replace legacy placeholders: <strong>Name</strong>
        legacy_replacements = {
            '<strong>Name</strong>': f"<strong>{data.get('recipient_name', 'Name')}</strong>",
            'Hi <strong>Name</strong>,': f"Hi <strong>{data.get('recipient_name', 'Name')}</strong>,",
            '{{Name}}': data.get('recipient_name', 'Name'),
            '{{name}}': data.get('recipient_name', 'Name')
        }
        
        for old, new in legacy_replacements.items():
            if old in content:
                content = content.replace(old, new)
                self.logger.debug(f"Replaced legacy placeholder: {old}")
        
        return content
    
    def _find_undefined_variables(self, template_content: str, data: Dict[str, Any]) -> list:
        """Find undefined variables in template."""
        if not JINJA2_AVAILABLE:
            return []
        
        try:
            # Parse template to find all variables
            ast = self.jinja_env.parse(template_content)
            template_vars = meta.find_undeclared_variables(ast)
            
            # Find variables not in data
            undefined = [var for var in template_vars if var not in data]
            return undefined
            
        except Exception:
            return []
    
    def get_available_placeholders(self) -> Dict[str, str]:
        """Get list of available placeholders and their sources."""
        return self.personalization_mappings.copy()
    
    def validate_template(self, template_content: str) -> Dict[str, Any]:
        """Validate template and return analysis."""
        analysis = {
            'has_jinja2_syntax': self._has_jinja2_syntax(template_content),
            'jinja2_available': JINJA2_AVAILABLE,
            'placeholders_found': [],
            'undefined_variables': [],
            'legacy_placeholders': []
        }
        
        # Find Jinja2 placeholders
        if analysis['has_jinja2_syntax']:
            jinja2_vars = re.findall(r'\{\{(.*?)\}\}', template_content)
            analysis['placeholders_found'] = [var.strip() for var in jinja2_vars]
        
        # Find legacy placeholders
        legacy_patterns = ['<strong>Name</strong>', '{{Name}}', '{{name}}']
        for pattern in legacy_patterns:
            if pattern in template_content:
                analysis['legacy_placeholders'].append(pattern)
        
        return analysis
