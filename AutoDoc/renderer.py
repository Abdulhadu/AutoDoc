"""Documentation rendering module for AutoDoc."""

import os
import re
import shutil
from typing import Dict, List, Any, Optional
from collections import defaultdict
import jinja2


# Templates
INDEX_TEMPLATE = """# {{ title }}

Generated documentation for the project.

## Table of Contents

{% for group_name, group_docs in grouped_docs.items() %}
### {{ group_name }}
{% for doc in group_docs %}
- [{{ doc.unit.name }}]({{ doc.page_path }}){% if doc.unit.type == 'method' %} (method in {{ doc.unit.parent }}){% endif %}
{% endfor %}
{% endfor %}
"""

HTML_WRAPPER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        pre {
            background-color: #f5f5f5;
            padding: 12px;
            border-radius: 5px;
            overflow-x: auto;
        }
        code {
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
        }
        h1, h2, h3 {
            margin-top: 24px;
            margin-bottom: 16px;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .breadcrumb {
            margin-bottom: 20px;
            padding: 8px 0;
            border-bottom: 1px solid #eaecef;
        }
    </style>
</head>
<body>
    <div class="breadcrumb">
        <a href="index.html">Home</a> &gt; {{ title }}
    </div>
    
    {{ content }}
</body>
</html>
"""


class DocumentationRenderer:
    """Renderer for creating documentation files from AI-generated content."""

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
        
        # Create Jinja2 environment
        self.jinja_env = jinja2.Environment(
            autoescape=jinja2.select_autoescape(['html']),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def render(self, docs: List[Dict[str, Any]]) -> str:
        """
        Render documentation to files.
        
        Args:
            docs: List of documentation dictionaries from AIDocGenerator
            
        Returns:
            Path to the index file
        """
        # Group documentation by specified criteria
        grouped_docs = self._group_docs(docs)
        
        # Create page for each code unit
        for doc in docs:
            self._render_doc_page(doc)
        
        # Create index page
        index_path = self._render_index(grouped_docs)
        
        return index_path
    
    def _group_docs(self, docs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group documentation according to the specified strategy."""
        grouped = defaultdict(list)
        
        for doc in docs:
            code_unit = doc["unit"]
            
            # Generate file path and URL for each document
            if self.format == "html":
                file_name = f"{self._get_safe_filename(code_unit.name)}.html"
            else:
                file_name = f"{self._get_safe_filename(code_unit.name)}.md"
                
            doc["file_path"] = os.path.join(self.output_dir, file_name)
            doc["page_path"] = file_name
            
            # Group by the specified criteria
            if self.group_by == "type":
                group_key = code_unit.type.capitalize()
            elif self.group_by == "module":
                group_key = code_unit.module_path
            else:  # flat
                group_key = "All"
                
            # Skip module entries in their own modules when grouping by module
            if self.group_by == "module" and code_unit.type == "module":
                continue
                
            grouped[group_key].append(doc)
        
        # Sort entries within each group
        for group in grouped.values():
            group.sort(key=lambda d: d["unit"].name)
            
        # Sort groups
        return dict(sorted(grouped.items()))
    
    def _render_doc_page(self, doc: Dict[str, Any]) -> str:
        """Render a single documentation page."""
        content = doc["documentation"]
        unit = doc["unit"]
        
        # Create file
        with open(doc["file_path"], "w", encoding="utf-8") as f:
            if self.format == "html":
                # Convert markdown to HTML (simple conversion)
                html_content = self._markdown_to_html(content)
                
                # Apply HTML template
                template = self.jinja_env.from_string(HTML_WRAPPER_TEMPLATE)
                rendered = template.render(
                    title=unit.name,
                    content=html_content
                )
                f.write(rendered)
            else:
                # Write markdown directly
                f.write(content)
        
        return doc["file_path"]
    
    def _render_index(self, grouped_docs: Dict[str, List[Dict[str, Any]]]) -> str:
        """Render the index page."""
        template = self.jinja_env.from_string(INDEX_TEMPLATE)
        rendered = template.render(
            title=self.index_title,
            grouped_docs=grouped_docs
        )
        
        if self.format == "html":
            # Convert markdown to HTML
            html_content = self._markdown_to_html(rendered)
            
            # Apply HTML template
            wrapper_template = self.jinja_env.from_string(HTML_WRAPPER_TEMPLATE)
            rendered = wrapper_template.render(
                title=self.index_title,
                content=html_content
            )
            
            # Save as HTML
            index_path = os.path.join(self.output_dir, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(rendered)
        else:
            # Save as markdown
            index_path = os.path.join(self.output_dir, "index.md")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(rendered)
        
        return index_path
    
    def _get_safe_filename(self, name: str) -> str:
        """Convert a name to a safe filename."""
        # Replace invalid characters
        safe_name = re.sub(r'[^\w\-\.]', '_', name)
        return safe_name
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """
        Simple conversion of markdown to HTML.
        
        Note: In a real implementation, you would use a proper markdown parser.
        This is a simplified version for demonstration purposes.
        """
        # Headers
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', markdown_text, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        
        # Code blocks
        def replace_code_block(match):
            language = match.group(1) or ""
            code = match.group(2)
            return f'<pre><code class="language-{language}">{code}</code></pre>'
            
        html = re.sub(r'```(\w+)?\n(.*?)```', replace_code_block, html, flags=re.DOTALL)
        
        # Inline code
        html = re.sub(r'`(.*?)`', r'<code>\1</code>', html)
        
        # Lists
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'(<li>.*?</li>\n?)+', lambda m: f'<ul>{m.group(0)}</ul>', html, flags=re.DOTALL)
        
        # Links
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', html)
        
        # Paragraphs (very basic conversion)
        html = re.sub(r'(?<!</h[1-3]>|</ul>|</pre>)\n{2,}', r'</p><p>', html)
        html = f'<p>{html}</p>'
        
        return html