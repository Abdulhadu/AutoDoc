"""Command-line interface for AutoDoc."""

import os
import sys
import time
from typing import Optional, List
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import print as rprint

from autodoc import AutoDoc
from autodoc.config import save_default_config


app = typer.Typer(
    name="autodoc",
    help="AI-powered documentation generator for Python projects",
    add_completion=False,
)
console = Console()


@app.command("generate")
def generate_docs(
    source: str = typer.Option(
        ".",
        "--source", "-s",
        help="Path to the source code directory",
    ),
    output: str = typer.Option(
        "./docs",
        "--output", "-o",
        help="Path where documentation will be generated",
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config", "-c",
        help="Path to configuration file (YAML/JSON)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key", "-k",
        help="Google AI API key (defaults to GOOGLE_API_KEY env var)",
        envvar="GOOGLE_API_KEY", 
    ),
    pdf: bool = typer.Option(
        False,
        "--pdf",
        help="Also generate PDF documentation",
    ),
    non_tech: bool = typer.Option(
        False,
        "--non-tech",
        help="Generate non-technical documentation for end users",
    ),
):
    """Generate documentation for a Python project."""
    start_time = time.time()
    
    # Welcome message
    rprint(Panel(
        "[bold green]AutoDoc[/bold green] - AI-powered documentation generator",
        expand=False
    ))
    
    # Validate source directory
    if not os.path.isdir(source):
        console.print(f"[bold red]Error:[/bold red] Source directory '{source}' does not exist.")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(output, exist_ok=True)
    
    # Validate API key
    if not api_key and not os.environ.get("GOOGLE_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] Google API key is required. "
            "Provide it with --api-key or set the GOOGLE_API_KEY environment variable."
        )
        sys.exit(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            # Initialize AutoDoc
            task = progress.add_task("Initializing...", total=None)
            doc_generator = AutoDoc(
                source_dir=source,
                output_dir=output,
                config_file=config,
                api_key=api_key,
            )
            
            # Generate documentation
            progress.update(task, description="Generating documentation...")
            result = doc_generator.generate(
                generate_pdf=pdf,
                non_tech=non_tech
            )
            
            progress.update(task, description="Documentation generated!", completed=True)
    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)
    
    # Completion message
    elapsed = time.time() - start_time
    rprint(Panel(
        f"[bold green]Documentation generated successfully![/bold green]\n\n"
        f"Output directory: [bold]{output}[/bold]\n"
        f"Markdown file: [bold]{os.path.basename(result['markdown'])}[/bold]\n"
        + (f"PDF file: [bold]{os.path.basename(result['pdf'])}[/bold]\n" if 'pdf' in result else "")
        + f"Time taken: [bold]{elapsed:.2f}[/bold] seconds",
        title="Complete",
        expand=False
    ))


@app.command("init-config")
def init_config(
    output: str = typer.Option(
        "autodoc.yaml",
        "--output", "-o",
        help="Path where to save the configuration file",
    ),
):
    """Generate a default configuration file."""
    try:
        config_path = save_default_config(output)
        rprint(f"[bold green]Configuration file created:[/bold green] {config_path}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command("version")
def version():
    """Display version information."""
    from autodoc import __version__
    rprint(f"[bold]AutoDoc[/bold] version [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()
