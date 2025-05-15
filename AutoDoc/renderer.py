"""Documentation rendering module for AutoDoc that produces a single consolidated file."""

import os
import re
import html
from typing import Dict, List, Any, Optional
from collections import defaultdict
import jinja2


# Template for consolidated documentation
CONSOLIDATED_TEMPLATE = """# {{ title }}

Generated documentation for the project.

{% for group_name, group_docs in grouped_docs.items() %}
## {{ group_name }}

{% for doc in group_docs %}
{{ doc.documentation | safe }}

---

{% endfor %}
{% endfor %}
"""


class DocumentationRenderer:
    """Renderer for creating a single consolidated documentation file from AI-generated content."""

    def __init__(
        self,
        output_dir: str,
        format: str = "markdown",
        index_title: str = "API Documentation",
        group_by: str = "module",
    ):
        """
        Initialize the documentation renderer.

        Args:
            output_dir: Directory where to save the documentation
            format: Output format ("markdown" or "html")
            index_title: Title for the index page
            group_by: How to group the documentation ("module", "type", or "flat")
        """
        self.output_dir = output_dir
        self.format = format.lower()
        self.index_title = index_title
        self.group_by = group_by
        
        # Create Jinja2 environment with HTML escaping disabled for markdown
        self.jinja_env = jinja2.Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def render(self, docs: List[Dict[str, Any]], base_name: str = "consolidated_documentation") -> str:
        """
        Render documentation to a single consolidated file.
        
        Args:
            docs: List of documentation dictionaries from AIDocGenerator
            base_name: Base name for the output file
            
        Returns:
            Path to the consolidated documentation file
        """
        # Group documentation by specified criteria
        grouped_docs = self._group_docs(docs)
        
        # Create the consolidated file
        consolidated_path = self._render_consolidated(grouped_docs, base_name)
        
        return consolidated_path
    
    def _group_docs(self, docs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group documentation according to the specified strategy."""
        grouped = defaultdict(list)
        
        for doc in docs:
            code_unit = doc["unit"]
            
            # Group by the specified criteria
            if self.group_by == "type":
                group_key = code_unit.type.capitalize()
            elif self.group_by == "module":
                group_key = code_unit.module_path
            else:  # flat
                group_key = "All"
                
            grouped[group_key].append(doc)
        
        # Sort entries within each group
        for group in grouped.values():
            group.sort(key=lambda d: d["unit"].name)
            
        # Sort groups
        return dict(sorted(grouped.items()))
    
    def _clean_html_entities(self, text: str) -> str:
        """Clean HTML entities from text."""
        return html.unescape(text)
    
    def _render_consolidated(self, grouped_docs: Dict[str, List[Dict[str, Any]]], 
                            base_name: str = "consolidated_documentation") -> str:
        """Render a consolidated documentation file."""
        template = self.jinja_env.from_string(CONSOLIDATED_TEMPLATE)
        
        # Clean HTML entities from documentation
        for group in grouped_docs.values():
            for doc in group:
                doc["documentation"] = self._clean_html_entities(doc["documentation"])
        
        rendered = template.render(
            title=self.index_title,
            grouped_docs=grouped_docs
        )
        
        # Save the consolidated file
        consolidated_path = os.path.join(self.output_dir, f"{base_name}.md")
        with open(consolidated_path, "w", encoding="utf-8") as f:
            f.write(rendered)
        
        return consolidated_path