"""Main script to generate consolidated documentation."""

import os
import sys
from typing import Optional, List, Dict, Any, Tuple

from autodoc import AutoDoc
from autodoc.parser import CodeParser
from autodoc.ai import AIDocGenerator
from consolidated_renderer import ConsolidatedDocumentationRenderer
from pdf_converter import convert_markdown_to_pdf


def generate_consolidated_docs(
    source_dir: str,
    output_dir: str,
    config_file: Optional[str] = None,
    api_key: Optional[str] = None,
    title: str = "Complete API Documentation",
    group_by: str = "module",
    generate_pdf: bool = False
) -> Dict[str, str]:
    """
    Generate consolidated documentation for a Python project.
    
    Args:
        source_dir: Path to the source code directory
        output_dir: Path where documentation will be generated
        config_file: Path to configuration file (YAML/JSON)
        api_key: Google AI API key
        title: Title for the documentation
        group_by: How to group the documentation ("module", "type", or "flat")
        generate_pdf: Whether to also generate a PDF version
        
    Returns:
        Dictionary with paths to the generated files
    """
    # Get API key from environment if not provided
    api_key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Google API key is required. Provide it as a parameter or "
            "set the GOOGLE_API_KEY environment variable."
        )
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize components directly
    parser = CodeParser(
        source_dir=source_dir,
        exclude_dirs=["venv", "env", ".venv", ".env", "__pycache__", ".git", "build", "dist"]
    )
    
    ai_generator = AIDocGenerator(
        api_key=api_key,
        model_name="models/gemini-1.5-flash",
        temperature=0.2,
        max_output_tokens=8192,
    )
    
    renderer = ConsolidatedDocumentationRenderer(
        output_dir=output_dir,
        format="markdown",
        index_title=title,
        group_by=group_by,
    )
    
    # Parse the code
    print("Parsing source code...")
    code_units = parser.parse()
    print(f"Found {len(code_units)} code units")
    
    # Generate documentation with AI
    print("Generating documentation with AI...")
    docs = ai_generator.generate_docs(code_units)
    print(f"Generated documentation for {len(docs)} code units")
    
    # Render the consolidated documentation
    print("Rendering consolidated documentation...")
    md_output_path = renderer.render(docs)
    print(f"Markdown documentation generated at: {md_output_path}")
    
    result = {"markdown": md_output_path}
    
    # Generate PDF if requested
    if generate_pdf:
        pdf_output_path = os.path.join(output_dir, "consolidated_documentation.pdf")
        print("Converting to PDF...")
        pdf_success = convert_markdown_to_pdf(md_output_path, pdf_output_path)
        
        if pdf_success:
            print(f"PDF documentation generated at: {pdf_output_path}")
            result["pdf"] = pdf_output_path
        else:
            print("Failed to generate PDF documentation")
    
    return result


def generate_pdf(
    markdown_file: str,
    output_pdf: Optional[str] = None,
) -> str:
    """
    Generate a PDF from an existing Markdown file.
    
    Args:
        markdown_file: Path to the markdown file
        output_pdf: Path where to save the PDF file (optional)
        
    Returns:
        Path to the generated PDF file
    """
    if not os.path.exists(markdown_file):
        raise FileNotFoundError(f"Markdown file not found: {markdown_file}")
    
    # Generate default output path if not provided
    if not output_pdf:
        output_pdf = os.path.splitext(markdown_file)[0] + ".pdf"
    
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_pdf)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Convert to PDF
    print(f"Converting {markdown_file} to PDF...")
    success = convert_markdown_to_pdf(markdown_file, output_pdf)
    
    if not success:
        raise RuntimeError(f"Failed to convert {markdown_file} to PDF")
    
    return output_pdf


if __name__ == "__main__":
    import argparse
    
    # Create a parent parser for common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--output", "-o", help="Output directory/file")
    
    # Main parser
    parser = argparse.ArgumentParser(description="Documentation tools for Python projects")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Parser for the 'generate' command
    gen_parser = subparsers.add_parser("generate", parents=[parent_parser], 
                                      help="Generate consolidated documentation")
    gen_parser.add_argument("--source", "-s", default=".", help="Source code directory")
    gen_parser.add_argument("--config", "-c", help="Path to configuration file")
    gen_parser.add_argument("--api-key", "-k", help="Google AI API key")
    gen_parser.add_argument("--title", "-t", default="Complete API Documentation", help="Documentation title")
    gen_parser.add_argument("--group-by", "-g", default="module", choices=["module", "type", "flat"], 
                          help="How to group the documentation")
    gen_parser.add_argument("--pdf", action="store_true", help="Also generate PDF documentation")
    
    # Parser for the 'md-to-pdf' command
    pdf_parser = subparsers.add_parser("md-to-pdf", parents=[parent_parser], 
                                      help="Convert an existing Markdown file to PDF")
    pdf_parser.add_argument("input", help="Input Markdown file")
    
    args = parser.parse_args()
    
    try:
        # Handle different commands
        if args.command == "generate":
            output_dir = args.output or "./docs"
            result = generate_consolidated_docs(
                source_dir=args.source,
                output_dir=output_dir,
                config_file=args.config,
                api_key=args.api_key,
                title=args.title,
                group_by=args.group_by,
                generate_pdf=args.pdf
            )
            
            print(f"\nSuccessfully generated documentation:")
            print(f"Markdown: {result['markdown']}")
            if 'pdf' in result:
                print(f"PDF: {result['pdf']}")
                
        elif args.command == "md-to-pdf":
            output_pdf = args.output
            pdf_file = generate_pdf(args.input, output_pdf)
            print(f"\nSuccessfully generated PDF at: {pdf_file}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)