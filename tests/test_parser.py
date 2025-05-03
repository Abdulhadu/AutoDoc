"""Tests for the code parser module."""

import os
import tempfile
import unittest

from autodoc.parser import CodeParser, CodeUnit


class TestCodeParser(unittest.TestCase):
    """Test cases for the CodeParser class."""

    def setUp(self):
        """Set up temporary directory and files for testing."""
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a simple Python file for testing
        self.test_file_path = os.path.join(self.temp_dir.name, "test_module.py")
        with open(self.test_file_path, "w") as f:
            f.write("""
\"\"\"Test module docstring.\"\"\"

def test_function(param1, param2=None):
    \"\"\"Test function docstring.
    
    Args:
        param1: First parameter
        param2: Second parameter (optional)
        
    Returns:
        Some value
    \"\"\"
    return param1 + str(param2)

class TestClass:
    \"\"\"Test class docstring.\"\"\"
    
    def __init__(self, value):
        \"\"\"Initialize the class.\"\"\"
        self.value = value
        
    def test_method(self, param):
        \"\"\"Test method docstring.\"\"\"
        return self.value + param
""")

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def test_parse_file(self):
        """Test parsing a Python file."""
        parser = CodeParser(self.temp_dir.name)
        code_units = parser.parse()
        
        # There should be 4 units: module, function, class, and method
        self.assertEqual(len(code_units), 4)
        
        # Check that all expected code units are found
        unit_types = [unit.type for unit in code_units]
        unit_names = [unit.name for unit in code_units]
        
        self.assertIn("module", unit_types)
        self.assertIn("function", unit_types)
        self.assertIn("class", unit_types)
        self.assertIn("method", unit_types)
        
        self.assertIn("test_module", unit_names)
        self.assertIn("test_function", unit_names)
        self.assertIn("TestClass", unit_names)
        self.assertIn("test_method", unit_names)
        
        # Check docstrings
        for unit in code_units:
            if unit.name == "test_function":
                self.assertIn("Test function docstring", unit.docstring)
            elif unit.name == "TestClass":
                self.assertIn("Test class docstring", unit.docstring)
            elif unit.name == "test_method":
                self.assertIn("Test method docstring", unit.docstring)
            elif unit.name == "test_module":
                self.assertIn("Test module docstring", unit.docstring)
        
        # Check parent-child relationship
        for unit in code_units:
            if unit.name == "test_method":
                self.assertEqual(unit.parent, "TestClass")

    def test_exclude_dirs(self):
        """Test excluding directories from parsing."""
        # Create subdirectory with a Python file
        exclude_dir = os.path.join(self.temp_dir.name, "exclude_dir")
        os.makedirs(exclude_dir)
        with open(os.path.join(exclude_dir, "excluded.py"), "w") as f:
            f.write("def excluded_function(): pass")
        
        # Parse with exclusion
        parser = CodeParser(self.temp_dir.name, exclude_dirs=["exclude_dir"])
        code_units = parser.parse()
        
        # The excluded file should not be parsed
        unit_names = [unit.name for unit in code_units]
        self.assertNotIn("excluded_function", unit_names)


if __name__ == "__main__":
    unittest.main()
