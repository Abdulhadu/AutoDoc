"""Code parsing module for AutoDoc."""

import os
import ast
import inspect
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CodeUnit:
    """Represents a unit of code (function, class, or module)."""
    
    type: str  # "function", "class", "method", or "module"
    name: str
    source: str
    docstring: Optional[str]
    file_path: str
    module_path: str
    line_start: int
    line_end: int
    parent: Optional[str] = None  # Parent class for methods


class CodeParser:
    """Parser for extracting code units from Python source files."""

    def __init__(self, source_dir: str, exclude_dirs: List[str] = None):
        """
        Initialize the code parser.

        Args:
            source_dir: Root directory of the source code
            exclude_dirs: List of directories to exclude from parsing
        """
        self.source_dir = os.path.abspath(source_dir)
        self.exclude_dirs = exclude_dirs or []
        
    def parse(self) -> List[CodeUnit]:
        """
        Parse the source code directory and extract code units.

        Returns:
            List of CodeUnit objects
        """
        code_units = []
        
        for root, dirs, files in os.walk(self.source_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs and not d.startswith(".")]
            
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, self.source_dir)
                    
                    # Generate module path
                    module_path = os.path.splitext(relative_path)[0].replace(os.path.sep, ".")
                    
                    # Parse the file
                    file_units = self._parse_file(file_path, module_path)
                    code_units.extend(file_units)
        
        return code_units
    
    def _parse_file(self, file_path: str, module_path: str) -> List[CodeUnit]:
        """
        Parse a single Python file and extract code units.

        Args:
            file_path: Path to the Python file
            module_path: Importable module path

        Returns:
            List of CodeUnit objects
        """
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
            
        try:
            tree = ast.parse(source)
            units = []
            
            # Extract module docstring
            module_docstring = ast.get_docstring(tree)
            module_unit = CodeUnit(
                type="module",
                name=module_path,
                source=source,
                docstring=module_docstring,
                file_path=file_path,
                module_path=module_path,
                line_start=1,
                line_end=len(source.splitlines()),
            )
            units.append(module_unit)
            
            # Extract classes and functions
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    units.append(self._extract_function(node, source, file_path, module_path))
                elif isinstance(node, ast.ClassDef):
                    class_unit = self._extract_class(node, source, file_path, module_path)
                    units.append(class_unit)
                    
                    # Extract methods
                    for class_node in ast.iter_child_nodes(node):
                        if isinstance(class_node, ast.FunctionDef):
                            method_unit = self._extract_function(
                                class_node, 
                                source, 
                                file_path, 
                                module_path,
                                parent=node.name
                            )
                            method_unit.type = "method"
                            units.append(method_unit)
            
            return units
        except SyntaxError:
            # Skip files with syntax errors
            return []
    
    def _extract_function(
        self, 
        node: ast.FunctionDef, 
        source: str, 
        file_path: str, 
        module_path: str,
        parent: str = None
    ) -> CodeUnit:
        """Extract information about a function."""
        source_lines = source.splitlines()
        line_start = node.lineno
        line_end = node.end_lineno if hasattr(node, "end_lineno") else line_start
        
        # Get the source code for this function
        function_source = "\n".join(source_lines[line_start-1:line_end])
        
        return CodeUnit(
            type="function",
            name=node.name,
            source=function_source,
            docstring=ast.get_docstring(node),
            file_path=file_path,
            module_path=module_path,
            line_start=line_start,
            line_end=line_end,
            parent=parent
        )
    
    def _extract_class(
        self, 
        node: ast.ClassDef, 
        source: str, 
        file_path: str, 
        module_path: str
    ) -> CodeUnit:
        """Extract information about a class."""
        source_lines = source.splitlines()
        line_start = node.lineno
        line_end = node.end_lineno if hasattr(node, "end_lineno") else line_start
        
        # Get the source code for this class
        class_source = "\n".join(source_lines[line_start-1:line_end])
        
        return CodeUnit(
            type="class",
            name=node.name,
            source=class_source,
            docstring=ast.get_docstring(node),
            file_path=file_path,
            module_path=module_path,
            line_start=line_start,
            line_end=line_end
        )
