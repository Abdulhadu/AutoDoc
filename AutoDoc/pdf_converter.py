"""PDF conversion module using only built-in Python libraries."""

import os
import subprocess
import sys
import tempfile
import platform
from typing import Optional


def convert_markdown_to_pdf(markdown_file: str, output_pdf: str) -> bool:
    """
    Convert a Markdown file to PDF using platform-specific methods.
    
    This uses built-in tools or commands available on most systems without requiring
    third-party Python libraries:
    - On Windows: Uses print to PDF functionality if available
    - On macOS: Uses textutil and cupsfilter which are built-in
    - On Linux: Uses a series of fallbacks (markdown → HTML → PDF)
    
    Args:
        markdown_file: Path to the markdown file
        output_pdf: Path where the PDF file should be saved
        
    Returns:
        True if conversion was successful, False otherwise
    """
    if not os.path.exists(markdown_file):
        print(f"Error: Markdown file not found: {markdown_file}")
        return False

    system = platform.system().lower()
    
    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_html = os.path.join(temp_dir, "temp_doc.html")
        
        # First convert markdown to HTML (simple conversion)
        with open(markdown_file, 'r', encoding='utf-8') as md_file:
            markdown_content = md_file.read()
        
        html_content = _convert_markdown_to_html(markdown_content)
        
        with open(temp_html, 'w', encoding='utf-8') as html_file:
            html_file.write(html_content)
        
        # Then convert HTML to PDF using system-specific methods
        if system == "darwin":  # macOS
            return _convert_with_macos(temp_html, output_pdf)
        elif system == "linux":
            return _convert_with_linux(temp_html, output_pdf)
        elif system == "windows":
            return _convert_with_windows(temp_html, output_pdf)
        else:
            print(f"Unsupported operating system: {system}")
            return False


def _convert_markdown_to_html(markdown_text: str) -> str:
    """
    Simple conversion of markdown to HTML using string replacement.
    
    Args:
        markdown_text: Markdown content
        
    Returns:
        HTML content
    """
    # Add HTML document structure
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Documentation</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        pre {{
            background-color: #f5f5f5;
            padding: 12px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        code {{
            font-family: Consolas, monospace;
            font-size: 0.9em;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #eee;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
"""
    
    # Headers
    lines = markdown_text.split('\n')
    in_code_block = False
    in_list = False
    html_lines = []
    
    for line in lines:
        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                in_code_block = True
                language = line[3:].strip()
                html_lines.append(f'<pre><code class="language-{language}">')
            continue
        
        if in_code_block:
            # Escape HTML entities in code blocks
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_lines.append(line)
            continue
            
        # Headers
        if line.startswith('# '):
            html_lines.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('## '):
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('### '):
            html_lines.append(f'<h3>{line[4:]}</h3>')
        # Lists
        elif line.startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line[2:]}</li>')
        # Horizontal rule
        elif line.startswith('---'):
            html_lines.append('<hr>')
        # Paragraph break
        elif line.strip() == '':
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append('<p></p>')
        # Regular paragraph
        else:
            # Basic formatting
            line = line.replace('**', '<strong>', 1)
            line = line.replace('**', '</strong>', 1)
            line = line.replace('*', '<em>', 1)
            line = line.replace('*', '</em>', 1)
            
            # Inline code
            while '`' in line:
                line = line.replace('`', '<code>', 1)
                line = line.replace('`', '</code>', 1)
                
            html_lines.append(f'<p>{line}</p>')
    
    if in_list:
        html_lines.append('</ul>')
    
    html += '\n'.join(html_lines)
    html += "\n</body>\n</html>"
    
    return html


def _convert_with_macos(html_file: str, output_pdf: str) -> bool:
    """Convert HTML to PDF on macOS using built-in tools."""
    try:
        # Using textutil to convert HTML to RTF, then cupsfilter to convert RTF to PDF
        with tempfile.NamedTemporaryFile(suffix='.rtf', delete=False) as temp_rtf:
            rtf_path = temp_rtf.name
            
        subprocess.run(['textutil', '-convert', 'rtf', '-output', rtf_path, html_file], check=True)
        subprocess.run(['cupsfilter', rtf_path], stdout=open(output_pdf, 'wb'), check=True)
        
        os.remove(rtf_path)
        return True
    except subprocess.SubprocessError as e:
        print(f"Error converting to PDF on macOS: {e}")
        return False


def _convert_with_linux(html_file: str, output_pdf: str) -> bool:
    """Convert HTML to PDF on Linux using commonly available tools."""
    tools = [
        ['wkhtmltopdf', html_file, output_pdf],
        ['weasyprint', html_file, output_pdf],
        ['chromium-browser', '--headless', '--disable-gpu', f'--print-to-pdf={output_pdf}', 
         f'file://{os.path.abspath(html_file)}'],
        ['google-chrome', '--headless', '--disable-gpu', f'--print-to-pdf={output_pdf}', 
         f'file://{os.path.abspath(html_file)}'],
    ]
    
    for tool in tools:
        try:
            subprocess.run(['which', tool[0]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(tool, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    print("Error: Could not convert to PDF. No supported tools found on Linux.")
    print("Please install one of: wkhtmltopdf, weasyprint, chromium-browser, or google-chrome")
    return False


def _convert_with_windows(html_file: str, output_pdf: str) -> bool:
    """Convert HTML to PDF on Windows using Microsoft Print to PDF."""
    try:
        # Try using Edge in headless mode (available in newer Windows versions)
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        
        for edge_path in edge_paths:
            if os.path.exists(edge_path):
                subprocess.run([
                    edge_path,
                    '--headless',
                    '--disable-gpu',
                    f'--print-to-pdf={output_pdf}',
                    f'file:///{os.path.abspath(html_file)}'
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
        
        # If Edge is not available, print instructions
        print("Could not automatically convert to PDF on Windows.")
        print(f"Please open the HTML file manually and use Print to PDF:")
        print(f"HTML file location: {os.path.abspath(html_file)}")
        
        # Simple HTML to PDF conversion using default browser
        os.startfile(html_file)
        input("Press Enter after you've saved the PDF... ")
        
        if os.path.exists(output_pdf):
            return True
        else:
            print(f"Could not find the PDF file at {output_pdf}")
            return False
            
    except Exception as e:
        print(f"Error converting to PDF on Windows: {e}")
        return False


if __name__ == "__main__":
    # Simple test/example usage
    if len(sys.argv) != 3:
        print("Usage: python pdf_converter.py input.md output.pdf")
        sys.exit(1)
        
    success = convert_markdown_to_pdf(sys.argv[1], sys.argv[2])
    if success:
        print(f"Conversion successful: {sys.argv[2]}")
    else:
        print("Conversion failed")
        sys.exit(1)