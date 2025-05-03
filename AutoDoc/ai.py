"""AI documentation generation module using Gemini via LangChain."""

import os
import asyncio
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai

from autodoc.parser import CodeUnit


# Templates for generating documentation
FUNCTION_TEMPLATE = """
You are an expert programmer documenting Python code. Given the following Python function, generate comprehensive documentation in markdown format that explains:
1. What the function does
2. Parameters and their types
3. Return value and type
4. Any exceptions that might be raised
5. Example usage of the function

If the function has existing docstrings, incorporate that information.

FUNCTION CODE:
```python
{source}
```

RESPONSE FORMAT:
# `{name}`

[General description of what the function does]

## Parameters
- `param1` (type): Description
- `param2` (type): Description
...

## Returns
(type): Description of return value

## Raises
- `ExceptionType`: Description of when this exception is raised
...

## Example
```python
# Example code showing how to use the function
```

RESPONSE:
"""

CLASS_TEMPLATE = """
You are an expert programmer documenting Python code. Given the following Python class, generate comprehensive documentation in markdown format that explains:
1. What the class represents and its purpose
2. Constructor parameters and their types
3. Key methods and their purposes
4. Attributes and their types
5. Example usage of the class

If the class has existing docstrings, incorporate that information.

CLASS CODE:
```python
{source}
```

RESPONSE FORMAT:
# `{name}`

[General description of what the class represents]

## Constructor
`__init__(param1, param2, ...)`
- `param1` (type): Description
- `param2` (type): Description
...

## Attributes
- `attribute1` (type): Description
- `attribute2` (type): Description
...

## Methods
### `method1(param1, param2, ...)`
- Description of what method1 does
- Parameters and return type

### `method2(param1, param2, ...)`
- Description of what method2 does
- Parameters and return type
...

## Example
```python
# Example code showing how to use the class
```

RESPONSE:
"""

MODULE_TEMPLATE = """
You are an expert programmer documenting Python code. Given the following Python module, generate comprehensive documentation in markdown format that explains:
1. The module's purpose and what it provides
2. Key functions and classes exposed by the module
3. How the module fits into the broader project
4. Example usage of key components

If the module has existing docstrings, incorporate that information.

MODULE NAME: {name}
MODULE DOCSTRING: {docstring}

RESPONSE FORMAT:
# Module `{name}`

[General description of the module's purpose]

## Overview
[Explanation of what the module provides and how it fits into the project]

## Components
- [List key functions, classes, and other components]

## Example Usage
```python
# Example code showing how to use key components
```

RESPONSE:
"""


class AIDocGenerator:
    """AI-powered documentation generator using Gemini models via LangChain."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "models/gemini-1.5-flash",
        temperature: float = 0.2,
        max_output_tokens: int = 8192,
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize the AI documentation generator.

        Args:
            api_key: Google Gemini API key
            model_name: Name of the Gemini model to use
            temperature: Temperature parameter for generation (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens in the response
            cache_dir: Directory to store cached responses (None to disable caching)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.cache_dir = cache_dir
        
        # Initialize model
        genai.configure(api_key=api_key)
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            convert_system_message_to_human=True,
        )
        
        # Initialize prompt templates
        self.function_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=FUNCTION_TEMPLATE,
                input_variables=["source", "name"],
            ),
        )
        
        self.class_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=CLASS_TEMPLATE,
                input_variables=["source", "name"],
            ),
        )
        
        self.module_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=MODULE_TEMPLATE,
                input_variables=["name", "docstring"],
            ),
        )
        
        # Create cache directory if provided
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_key(self, code_unit: CodeUnit) -> str:
        """Generate a cache key for a code unit."""
        if not self.cache_dir:
            return None
            
        # Create a hash of the code unit's content and type
        hash_input = f"{code_unit.type}:{code_unit.name}:{code_unit.source}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _get_cached_doc(self, cache_key: str) -> Optional[str]:
        """Get documentation from cache if available."""
        if not self.cache_dir or not cache_key:
            return None
            
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)["documentation"]
            except (json.JSONDecodeError, KeyError):
                return None
        return None
    
    def _save_to_cache(self, cache_key: str, documentation: str) -> None:
        """Save documentation to cache."""
        if not self.cache_dir or not cache_key:
            return
            
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        with open(cache_file, "w") as f:
            json.dump({"documentation": documentation}, f)
    
    def _generate_doc_for_unit(self, code_unit: CodeUnit) -> Dict[str, Any]:
        """Generate documentation for a single code unit."""
        # Check cache first
        cache_key = self._get_cache_key(code_unit)
        cached_doc = self._get_cached_doc(cache_key)
        
        if cached_doc:
            return {
                "unit": code_unit,
                "documentation": cached_doc,
                "from_cache": True,
            }
        
        # Generate documentation based on code unit type
        try:
            if code_unit.type == "function" or code_unit.type == "method":
                result = self.function_chain.invoke({
                    "source": code_unit.source,
                    "name": code_unit.name,
                })
                doc = result["text"]
            elif code_unit.type == "class":
                result = self.class_chain.invoke({
                    "source": code_unit.source,
                    "name": code_unit.name,
                })
                doc = result["text"]
            elif code_unit.type == "module":
                result = self.module_chain.invoke({
                    "name": code_unit.name,
                    "docstring": code_unit.docstring or "No docstring provided",
                })
                doc = result["text"]
            else:
                doc = f"# {code_unit.name}\n\nNo documentation available for this type of code unit."
                
            # Save to cache
            if cache_key:
                self._save_to_cache(cache_key, doc)
                
            return {
                "unit": code_unit,
                "documentation": doc,
                "from_cache": False,
            }
        except Exception as e:
            return {
                "unit": code_unit,
                "documentation": f"# {code_unit.name}\n\nError generating documentation: {str(e)}",
                "from_cache": False,
                "error": str(e),
            }
    
    def generate_docs(self, code_units: List[CodeUnit]) -> List[Dict[str, Any]]:
        """
        Generate documentation for multiple code units in parallel.

        Args:
            code_units: List of CodeUnit objects

        Returns:
            List of dictionaries containing the code unit and its documentation
        """
        # Use ThreadPoolExecutor to parallelize API calls
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(self._generate_doc_for_unit, code_units))
        
        return results
