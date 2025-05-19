# AutoDoc

An AI-powered documentation generator and test generator for Python projects using Google's Gemini models via LangChain.


## Features

- Generates comprehensive AI-powered documentation for Python projects
- Consolidates all documentation into a single Markdown file
- Optionally converts documentation to PDF format
- Organizes documentation by module, type, or flat structure
- Uses Google Gemini AI models for high-quality documentation generation
- **No third-party PDF libraries required** - uses system tools for PDF conversion
- Generates non-technical documentation along with technical documentation
- Generates tests for the code using the `pytest` and `unittest` frameworks

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

IN BASH
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

IN POWERSHELL

```powershell
$Env:API_KEY="your-api-key-here"
```

## Usage

The tool provides three main commands:

### 1. Generate Documentation

```bash
autodoc generate --source /path/to/your/code --output /path/to/output/dir --api-key YOUR_GOOGLE_API_KEY --pdf
```
### 2. Generate Tests
```bash
autodoc generate-tests --source /path/to/your/code --output /path/to/output/dir --framework pytest
``` 
### 3. Convert Existing Markdown to PDF

```bash
autodoc md-to-pdf input.md --output output.pdf
```

## Command Line Arguments

### Generate-tests Command
#### Generate-tests Command Options

| Option           | Short | Description                                                                 |
|------------------|--------|-----------------------------------------------------------------------------|
| `--source`       | `-s`   | Path to the source code directory *(default: `.`)*                          |
| `--output`       | `-o`   | Path where test files will be generated *(default: `./tests`)*              |
| `--framework`    | `-f`   | Testing framework to use (`pytest` or `unittest`) *(default: `pytest`)*     |
| `--exclude`      | `-e`   | Directories to exclude from parsing *(default: `None`)*                     |
| `--help`         |        | Show this message and exit  



### Generate Command
#### Generate Command Options

| Option           | Short | Description                                                                                             |
|------------------|--------|-----------------------------------------------------------------------------------------------------|
| `--source`       | `-s`   | Source code directory (default: current directory)                                                    |
| `--output`       | `-o`   | Output directory (default: `./docs`)                                                                  |
| `--config`       | `-c`   | Path to configuration file (optional)                                                                 |
| `--api-key`      | `-k`   | Google AI API key (can also be set via `GOOGLE_API_KEY` environment variable)                          |
| `--title`        | `-t`   | Documentation title (default: "Complete API Documentation")                                           |
| `--group-by`     | `-g`   | How to group the documentation, options: `"module"`, `"type"`, or `"flat"` (default: `"module"`)      |
| `--pdf`          |        | Add this flag to also generate PDF documentation                                                      |
| `--non-tech`     |        | Add this flag to generate non-technical documentation          

### MD-to-PDF Command

- `input`: Input Markdown file
- `--output`, `-o`: Output PDF file path (optional)

### Environment Variables

- `GOOGLE_API_KEY`: Your Google AI API key

## Output

The script generates documentation files in your specified output directory:
- `consolidated_documentation.md`: Markdown documentation file
- `consolidated_documentation.pdf`: PDF documentation file (if --pdf flag is used)

## PDF Generation

The PDF conversion works across different operating systems:
- **Windows**: Uses Microsoft Edge or system browser
- **macOS**: Uses built-in textutil and cupsfilter
- **Linux**: Tries various tools like wkhtmltopdf, weasyprint, chromium, or chrome

No third-party Python libraries are required for PDF generation.

## How It Works

1. Uses AutoDoc's `CodeParser` to extract code units from your Python files
2. Uses AutoDoc's `AIDocGenerator` to generate documentation for each code unit
3. Uses a custom `ConsolidatedDocumentationRenderer` to render all documentation into a single file
4. Optionally converts the Markdown to PDF using system tools

## Examples

```bash
# Generate Markdown documentation grouped by module
autodoc generate --source ./my_project --output ./docs --group-by module

# Generate both Markdown and PDF documentation
autodoc generate --source ./my_project --output ./docs --pdf

#generate non-technical documentation along with pdf
autodoc generate --source ./my_project --output ./docs --pdf --non-tech

# Convert an existing Markdown file to PDF
autodoc md-to-pdf ./docs/consolidated_documentation.md --output ./docs/documentation.pdf

# Generate tests using pytest
autodoc generate-tests --source "your/source/dir" --output ./tests --framework pytest

# Generate tests using unittest
autodoc generate-tests --source "your/source/dir" --output ./tests --framework unittest

```


### Using the Python API

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
