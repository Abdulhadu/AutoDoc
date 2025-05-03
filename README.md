# AutoDoc

An AI-powered documentation generator for Python projects using Google's Gemini models via LangChain.

## Features

- Automatically scans Python codebases to generate comprehensive documentation
- Uses Google's Gemini models via LangChain for high-quality documentation
- Generates Markdown/HTML documentation for functions, classes, and modules
- Offers both CLI and Python API interfaces
- Configurable with YAML/JSON configuration files

## Installation

```bash
pip install autodoc
```

For development:

```bash
git clone https://github.com/yourusername/autodoc.git
cd autodoc
pip install -e ".[dev]"
```

## Getting Started

### 1. Set up your API key

First, obtain a Google AI API key from [Google AI Studio](https://ai.google.dev/).

Set it as an environment variable:

```bash
export GOOGLE_API_KEY=""
```

### 2. Using the CLI

Generate documentation for a Python project:

```bash
autodoc generate --source ./my_project --output ./docs
# Or set the api key as an environment variable:
autodoc generate --source ./my_project --output ./docs --api-key ""
```

### 3. Using the Python API

```python
from autodoc import AutoDoc

# Initialize the documentation generator
doc_generator = AutoDoc(
    source_dir="./my_project",
    output_dir="./docs",
    config_file="autodoc.yaml"  # Optional
)

# Generate documentation
doc_generator.generate()
```

## Configuration

Create an `autodoc.yaml` file in your project root:

```yaml
# Source code settings
source:
  directories: 
    - src/
    - lib/
  exclude:
    - tests/
    - examples/

# AI model settings
ai:
  model: "models/gemini-1.5-flash"
  temperature: 0.2
  max_output_tokens: 8192

# Output settings
output:
  format: "markdown"  # or "html"
  index_title: "My Project Documentation"
  group_by: "module"  # or "type" or "flat"
```

## License

MIT License