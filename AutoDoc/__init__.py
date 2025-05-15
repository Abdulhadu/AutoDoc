"""AutoDoc: AI-powered documentation generator for Python projects."""

import os
from typing import Dict, List, Optional, Union, Tuple

from autodoc.config import load_config
from autodoc.parser import CodeParser
from autodoc.ai import AIDocGenerator
from autodoc.renderer import DocumentationRenderer

__version__ = "0.1.0"


class AutoDoc:
    """Main class for the AutoDoc documentation generator."""

    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        config_file: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the AutoDoc generator.

        Args:
            source_dir: Path to the source code directory
            output_dir: Path where documentation will be generated
            config_file: Path to configuration file (YAML/JSON)
            api_key: Google AI API key (falls back to GOOGLE_API_KEY env var)
        """
        self.source_dir = os.path.abspath(source_dir)
        self.output_dir = os.path.abspath(output_dir)
        
        # Load configuration
        self.config = load_config(config_file) if config_file else {}
        
        # Use provided API key or fall back to environment variable
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key is required. Provide it as a parameter or "
                "set the GOOGLE_API_KEY environment variable."
            )
        
        # Initialize components
        self.parser = CodeParser(
            source_dir=self.source_dir,
            exclude_dirs=self.config.get("source", {}).get("exclude", []),
        )
        
        self.ai_generator = AIDocGenerator(
            api_key=self.api_key,
            model_name=self.config.get("ai", {}).get("model", "models/gemini-1.5-flash"),
            temperature=self.config.get("ai", {}).get("temperature", 0.2),
            max_output_tokens=self.config.get("ai", {}).get("max_output_tokens", 8192),
        )
        
        self.renderer = DocumentationRenderer(
            output_dir=self.output_dir,
            format=self.config.get("output", {}).get("format", "markdown"),
            index_title=self.config.get("output", {}).get("index_title", "API Documentation"),
            group_by=self.config.get("output", {}).get("group_by", "module"),
        )
    
    def generate(self, generate_pdf: bool = False, non_tech: bool = False) -> Dict[str, str]:
        """
        Generate documentation for the source code.
        
        Args:
            generate_pdf: Whether to also generate a PDF version
            non_tech: Whether to generate non-technical documentation
            
        Returns:
            Dictionary with paths to the generated files
        """
        # Parse the code
        code_units = self.parser.parse()
        
        # Generate documentation with AI
        docs = self.ai_generator.generate_docs(code_units, non_tech=non_tech)
        
        # Determine output filename based on documentation type
        base_name = "non_tech_documentation" if non_tech else "consolidated_documentation"
        
        # Render the documentation
        md_path = self.renderer.render(docs, base_name=base_name)
        
        result = {"markdown": md_path}
        
        # Generate PDF if requested
        if generate_pdf:
            from autodoc.pdf_converter import convert_markdown_to_pdf
            pdf_path = os.path.join(self.output_dir, f"{base_name}.pdf")
            if convert_markdown_to_pdf(md_path, pdf_path):
                result["pdf"] = pdf_path
        
        return result

    def generate_all(self) -> Tuple[str, str]:
        """
        Generate both Markdown and PDF documentation for the source code.
        
        Returns:
            Tuple of (markdown_path, pdf_path)
        """
        # Parse the code
        code_units = self.parser.parse()
        
        # Generate documentation with AI
        docs = self.ai_generator.generate_docs(code_units)
        
        # Render both formats
        md_path, pdf_path = self.renderer.render_all(docs)
        
        return md_path, pdf_path
