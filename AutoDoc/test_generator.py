"""Test case generation module for AutoDoc."""

import os
import ast
import inspect
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from autodoc.parser import CodeParser, CodeUnit
from autodoc.utils import detect_framework, get_test_file_path
from autodoc.ai import AIDocGenerator
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough


@dataclass
class TestCodeUnit:
    """Represents a unit of code that needs test cases."""
    
    type: str  # "function", "class", "method", "route", or "module"
    name: str
    source: str
    docstring: Optional[str]
    file_path: str
    module_path: str
    line_start: int
    line_end: int
    parent: Optional[str] = None  # Parent class for methods
    framework: Optional[str] = None  # Detected framework (flask, fastapi, django, etc.)
    is_route: bool = False  # Whether this is a route/endpoint
    http_method: Optional[str] = None  # HTTP method for routes
    route_path: Optional[str] = None  # URL path for routes


# Template for generating test cases
TEST_TEMPLATE = """
You are an expert Python test developer. Given the following Python code, generate comprehensive test cases using {framework}.
The test cases should cover:
1. Edge cases
2. Error cases
3. Input validation

If the code defines API endpoints (e.g., using flask):
- Use the test client provided by the framework (e.g., Flask's `test_client()`) to simulate requests
- Test different HTTP methods (GET, POST, etc.)
- Test request validation and handling of unsupported methods
- Test response status codes and content types
- Test response JSON structures and values
- Test error handling (e.g., exceptions, missing routes)
- Include authentication tests if applicable
- Ensure the app is configured with `TESTING = True` during testing

If the code defines functions or classes:
- Test all public methods and expected behavior
- Validate handling of invalid or missing inputs
- Include tests for raised exceptions or errors
- Cover edge cases (e.g., empty data, extreme values)
- Assert correct return types and values

Ensure that the generated test cases are valid, executable, and structured using best practices for {framework}. Use fixtures for reusable setup if needed.

CODE:
```python
{source}
```

Generate test cases for the function/class named: {name}

RESPONSE:
"""


class TestCaseGenerator:
    """Generator for creating test cases for Python code using AI."""

    def __init__(
        self,
        source_dir: str,
        output_dir: str,
        framework: str = "pytest",
        exclude_dirs: List[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the test case generator.

        Args:
            source_dir: Path to the source code directory
            output_dir: Path where test files will be generated
            framework: Testing framework to use ('pytest' or 'unittest')
            exclude_dirs: Directories to exclude from parsing
            api_key: Google AI API key
        """
        self.source_dir = os.path.abspath(source_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.framework = framework.lower()
        self.exclude_dirs = exclude_dirs or []
        
        # Initialize AI generator
        self.ai_generator = AIDocGenerator(
            api_key=api_key or os.environ.get("GOOGLE_API_KEY"),
            model_name="models/gemini-1.5-flash",
            temperature=0.2,
            max_output_tokens=8192,
        )
        
        # Initialize test chain
        self.test_prompt = PromptTemplate(
            input_variables=["framework", "source", "name"],
            template=TEST_TEMPLATE
        )
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate(self) -> Dict[str, str]:
        """
        Generate test cases for all code units in the source directory.
        
        Returns:
            Dictionary mapping original files to generated test files
        """
        # Parse the source code
        parser = CodeParser(
            source_dir=self.source_dir,
            exclude_dirs=self.exclude_dirs,
        )
        code_units = parser.parse()
        
        # Convert CodeUnit to TestCodeUnit and detect frameworks
        test_units = []
        for unit in code_units:
            framework = detect_framework(unit.file_path)
            test_unit = TestCodeUnit(
                type=unit.type,
                name=unit.name,
                source=unit.source,
                docstring=unit.docstring,
                file_path=unit.file_path,
                module_path=unit.module_path,
                line_start=unit.line_start,
                line_end=unit.line_end,
                parent=unit.parent,
                framework=framework,
                is_route=self._is_route(unit),
                http_method=self._get_http_method(unit) if self._is_route(unit) else None,
                route_path=self._get_route_path(unit) if self._is_route(unit) else None,
            )
            test_units.append(test_unit)
        
        # Group test units by file

        print("code units are", code_units)
        file_units = self._group_by_file(test_units)
        print("File units are", file_units)
        # Generate test files
        generated_files = {}
        for file_path, units in file_units.items():
            test_file_path = self._generate_test_file(file_path, units)
            if test_file_path:
                generated_files[file_path] = test_file_path
        
        return generated_files
    
    def _is_route(self, unit: CodeUnit) -> bool:
        """Check if a code unit is a route/endpoint."""
        if not hasattr(unit, 'source'):
            return False
            
        source = unit.source.lower()
        route_patterns = [
            '@app.route', '@blueprint.route',
            '@app.get', '@app.post', '@app.put', '@app.delete',
            '@router.get', '@router.post', '@router.put', '@router.delete',
            'def get_', 'def post_', 'def put_', 'def delete_',
        ]
        return any(pattern in source for pattern in route_patterns)
    
    def _get_http_method(self, unit: CodeUnit) -> Optional[str]:
        """Extract HTTP method from a route."""
        if not hasattr(unit, 'source'):
            return None
            
        source = unit.source.lower()
        methods = ['get', 'post', 'put', 'delete', 'patch']
        for method in methods:
            if f'@{method}' in source or f'def {method}_' in source:
                return method.upper()
        return None
    
    def _get_route_path(self, unit: CodeUnit) -> Optional[str]:
        """Extract route path from a route."""
        if not hasattr(unit, 'source'):
            return None
            
        source = unit.source
        # Look for route decorator with path
        route_match = re.search(r'@.*?route\([\'"]([^\'"]+)[\'"]', source)
        if route_match:
            return route_match.group(1)
        return None
    
    def _group_by_file(self, test_units: List[TestCodeUnit]) -> Dict[str, List[TestCodeUnit]]:
        """Group test units by their file paths."""
        file_units = {}
        
        for unit in test_units:
            if unit.file_path not in file_units:
                file_units[unit.file_path] = []
            
            # Don't add modules to the list
            if unit.type != "module":
                file_units[unit.file_path].append(unit)
        
        return file_units
    
    def _generate_test_file(self, file_path: str, units: List[TestCodeUnit]) -> Optional[str]:
        """Generate a test file for the given source file using AI."""
        if not units:
            return None
            
        # Get the module path and determine the test directory structure
        rel_path = os.path.relpath(file_path, self.source_dir)
        test_rel_dir = os.path.dirname(rel_path)
        test_dir = os.path.join(self.output_dir, test_rel_dir)
        os.makedirs(test_dir, exist_ok=True)
        
        # Get file name and create test file name
        file_name = os.path.basename(file_path)
        base_name, _ = os.path.splitext(file_name)
        test_file_name = f"{base_name}_test.py"
        test_file_path = os.path.join(test_dir, test_file_name)
        
        # Generate test content using AI
        test_content = self._generate_test_content(file_path, units)
        
        # Write the test file
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        return test_file_path
    
    def _generate_test_content(self, file_path: str, units: List[TestCodeUnit]) -> str:
        """Generate test content using AI."""
        # Prepare imports
        imports = self._get_required_imports(units)
        
        # Generate test cases for each unit
        test_cases = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for unit in units:
                future = executor.submit(self._generate_unit_tests, unit)
                futures.append(future)
            
            for future in futures:
                test_cases.append(future.result())
        
        # Combine everything
        content = [
            '"""Generated test cases."""',
            "",
            *imports,
            "",
            *test_cases,
        ]
        
        return "\n".join(content)
    
    def _get_required_imports(self, units: List[TestCodeUnit]) -> List[str]:
        """Get required imports based on the code units."""
        imports = set()
        
        # Framework imports
        if self.framework == "pytest":
            imports.add("import pytest")
        else:  # unittest
            imports.add("import unittest")
        
        # Standard imports
        imports.update([
            "import os",
            "import sys",
            "from unittest.mock import patch, MagicMock",
        ])
        
        # Module import
        module_path = os.path.splitext(os.path.relpath(units[0].file_path, self.source_dir))[0].replace(os.path.sep, ".")
        imports.add(f"from {module_path} import *")
        
        # Framework-specific imports
        for unit in units:
            if unit.framework == "flask":
                imports.update([
                    "import flask",
                    "from flask import Flask",
                    "from flask.testing import FlaskClient",
                ])
            elif unit.framework == "fastapi":
                imports.update([
                    "from fastapi import FastAPI",
                    "from fastapi.testclient import TestClient",
                ])
            elif unit.framework == "django":
                imports.update([
                    "from django.test import TestCase, Client",
                    "from django.urls import reverse",
                ])
        
        return sorted(list(imports))
    
    def _generate_unit_tests(self, unit: TestCodeUnit) -> str:
        """Generate test cases for a single code unit using AI."""
        try:
            # Prepare the input
            chain_input = {
                "framework": self.framework,
                "source": unit.source,
                "name": unit.name,
            }
            
            # Generate test cases using AI
            result = self.test_prompt | self.ai_generator.llm
            response = result.invoke(chain_input)
            
            test_cases = response.content
            
            # Clean up the response
            test_cases = test_cases.strip()
            if test_cases.startswith("```python"):
                test_cases = test_cases[9:]
            if test_cases.endswith("```"):
                test_cases = test_cases[:-3]
            
            # Format the test cases
            formatted_test = f"# Test cases for {unit.name}\n{test_cases}"
            return formatted_test.strip()
            
        except Exception as e:
            return f"# Error generating tests for {unit.name}: {str(e)}"

def generate_tests(
    source_dir: str,
    output_dir: str,
    framework: str = "pytest",
    exclude_dirs: List[str] = None,
) -> Dict[str, str]:
    """
    Generate test cases for all Python files in the source directory.
    
    Args:
        source_dir: Path to the source code directory
        output_dir: Path where test files will be generated
        framework: Testing framework to use ('pytest' or 'unittest')
        exclude_dirs: Directories to exclude from parsing
        
    Returns:
        Dictionary mapping original files to generated test files
    """
    generator = TestCaseGenerator(
        source_dir=source_dir,
        output_dir=output_dir,
        framework=framework,
        exclude_dirs=exclude_dirs,
    )
    
    return generator.generate()

# Make sure this is at the end of the file
__all__ = ['TestCaseGenerator', 'generate_tests']