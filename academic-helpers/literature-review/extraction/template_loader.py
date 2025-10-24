# extraction/template_loader.py
"""YAML template loader for data extraction."""
import os
import yaml
from typing import Dict, List, Any

class TemplateLoader:
    """Load and manage extraction templates."""

    def __init__(self, templates_dir: str = None):
        """
        Initialize template loader.

        Args:
            templates_dir: Path to templates directory.
                          If None, uses default templates/ directory.
        """
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(__file__),
                '..',
                'templates'
            )

        self.templates_dir = templates_dir
        self._templates_cache = {}

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load a template by name.

        Args:
            template_name: Template name without .yaml extension

        Returns:
            Template dictionary

        Raises:
            FileNotFoundError: If template does not exist
        """
        # Check cache first
        if template_name in self._templates_cache:
            return self._templates_cache[template_name]

        # Load from file
        template_path = os.path.join(
            self.templates_dir,
            f'{template_name}.yaml'
        )

        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Template '{template_name}' not found at {template_path}"
            )

        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)

        # Cache and return
        self._templates_cache[template_name] = template
        return template

    def list_templates(self) -> List[str]:
        """
        List all available templates.

        Returns:
            List of template names (without .yaml extension)
        """
        if not os.path.exists(self.templates_dir):
            return []

        templates = []
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.yaml'):
                templates.append(filename[:-5])  # Remove .yaml extension

        return sorted(templates)

    def validate_template(self, template: Dict[str, Any]) -> List[str]:
        """
        Validate template structure.

        Args:
            template: Template dictionary

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if 'name' not in template:
            errors.append("Template missing 'name' field")

        if 'fields' not in template:
            errors.append("Template missing 'fields' field")
            return errors  # Can't validate further

        for field_name, field_config in template['fields'].items():
            if 'type' not in field_config:
                errors.append(f"Field '{field_name}' missing 'type'")

            if 'prompt' not in field_config:
                errors.append(f"Field '{field_name}' missing 'prompt'")

            field_type = field_config.get('type')
            if field_type == 'select' and 'options' not in field_config:
                errors.append(f"Field '{field_name}' type 'select' requires 'options'")

        return errors
