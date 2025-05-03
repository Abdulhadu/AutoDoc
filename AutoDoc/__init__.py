"""AutoDoc: AI-powered documentation generator for Python projects."""

import os
from typing import Dict, List, Optional, Union

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
    
    def generate(self) -> str:
        """
        Generate documentation for the source code.
        
        Returns:
            Path to the generated documentation index file
        """
        # Parse the code
        code_units = self.parser.parse()
        
        # Generate documentation with AI
        docs = self.ai_generator.generate_docs(code_units)
        
        # Render the documentation
        index_path = self.renderer.render(docs)
        
        return index_path
