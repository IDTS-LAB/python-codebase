from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


class EmailTemplateRenderer:
    """Renders HTML email templates with variables"""

    def __init__(self, template_dir: str = "templates/emails"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render an HTML template with context variables.

        Args:
            template_name: Name of the template file (e.g., 'verification.html')
            context: Dictionary of variables to inject into the template

        Returns:
            Rendered HTML string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
