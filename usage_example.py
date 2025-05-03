#!/usr/bin/env python3
"""
Example usage of the AutoDoc package.

Make sure to set your GOOGLE_API_KEY environment variable first:
export GOOGLE_API_KEY=your_api_key_here
"""

import os
from autodoc import AutoDoc

# Basic usage
def basic_example():
    """Generate documentation for a project directory."""
    doc_generator = AutoDoc(
        source_dir="./my_project",  # Path to your source code
        output_dir="./docs",        # Where to generate documentation
    )
    
    # Generate the documentation
    index_path = doc_generator.generate()
    print(f"Documentation generated at: {index_path}")


# Advanced usage with custom configuration
def advanced_example():
    """Generate documentation with custom configuration."""
    # Create configuration dictionary
    config = {
        "source": {
            "directories": ["src/", "lib/"],
            "exclude": ["tests/", "examples/"],
        },
        "ai": {
            "model": "models/gemini-1.5-flash",
            "temperature": 0.1,
            "max_output_tokens": 4096,
        },
        "output": {
            "format": "html",
            "index_title": "My Project API Reference",
            "group_by": "type",
        }
    }
    
    # Create temporary configuration file
    import tempfile
    import json
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config, f)
        config_path = f.name
    
    try:
        # Initialize with custom config
        doc_generator = AutoDoc(
            source_dir="./my_project",
            output_dir="./docs",
            config_file=config_path,
        )
        
        # Generate the documentation
        index_path = doc_generator.generate()
        print(f"Documentation generated at: {index_path}")
    finally:
        # Clean up temporary file
        os.unlink(config_path)


if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable is not set.")
        print("Please set it with: export GOOGLE_API_KEY=your_api_key_here")
        exit(1)
    
    # Run examples
    print("Running basic example...")
    basic_example()
    
    print("\nRunning advanced example...")
    advanced_example()
