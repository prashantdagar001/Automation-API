from typing import Dict, Any, Optional, List
from app.db.vector_db import VectorDatabase
from app.core.code_generator import CodeGenerator
from app.core.context_manager import ContextManager
import logging
import re
import json
import importlib
import inspect

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceProcessor:
    def __init__(self, db_path: str = "./vector_db"):
        """Initialize the service processor."""
        self.vector_db = VectorDatabase(persist_directory=db_path)
        self.code_generator = CodeGenerator()
        self.context_manager = ContextManager()
        
        # Load automation functions directly for simple matching
        self.available_functions = {}
        
        # Function intent patterns - direct mapping between phrases and functions
        self.intent_patterns = {
            # Memory - put memory patterns BEFORE calculator since "calc" appears in "calculate memory"
            r"(show|display|get).*memory": "get_memory_usage",
            r"memory.*usage": "get_memory_usage",
            r"(usage|space|available).*(memory|ram)": "get_memory_usage",
            r"(memory|ram).*(usage|info|stat)": "get_memory_usage",
            
            # Directory listing - put before calculator
            r"(list|show).*directory": "list_directory_contents",
            r"(list|show).*folder": "list_directory_contents",
            r"(list|show).*file": "list_directory_contents",
            r"directory.*content": "list_directory_contents",
            r"(show|list|display).*content": "list_directory_contents",
            
            # Calculator - moved after memory and directory
            r"(open|launch|start|run).*(calc|calculator)": "open_calculator",
            
            # Chrome
            r"(open|launch|start).*chrome": "open_chrome",
            r"browse|browser|web": "open_chrome",
            
            # Notepad
            r"(open|launch|start).*note": "open_notepad",
            r"text editor|notepad": "open_notepad",
            
            # CPU usage
            r"(cpu|processor).*usage": "get_cpu_usage",
            r"(usage|load|utilization).*(cpu|processor)": "get_cpu_usage",
            r"(show|display|get|what).*(cpu|processor)": "get_cpu_usage",
            
            # Disk
            r"(disk|storage|drive).*usage": "get_disk_usage",
            r"(usage|available|space).*(disk|storage|drive)": "get_disk_usage",
            r"(show|display|get).*(disk|storage|drive)": "get_disk_usage",
            
            # Process list
            r"(process|running|task).*list": "list_running_processes",
            r"list.*(process|running|task)": "list_running_processes",
            r"(show|display|get).*(process|running|task)": "list_running_processes",
            
            # Command execution
            r"run command|execute command|shell command": "run_command",
            
            # Create directory
            r"create.*dir|create.*folder|create.*directory": "create_directory"
        }
        
        try:
            # Import module
            from app.functions import automation_functions
            
            # Extract functions
            for name, obj in inspect.getmembers(automation_functions):
                if inspect.isfunction(obj):
                    self.available_functions[name] = {
                        'function': obj,
                        'module': obj.__module__,
                        'name': obj.__name__,
                        'docstring': obj.__doc__ or "",
                        'keywords': self._extract_keywords(name, obj.__doc__ or "")
                    }
            
            logger.info(f"Loaded {len(self.available_functions)} functions for direct matching")
        except Exception as e:
            logger.error(f"Error loading functions for direct matching: {str(e)}", exc_info=True)
    
    def _extract_keywords(self, name: str, docstring: str) -> List[str]:
        """Extract keywords from function name and docstring."""
        keywords = []
        
        # Add function name parts
        name_parts = re.split(r'[_\s]+', name.lower())
        keywords.extend(name_parts)
        
        # Add docstring parts (first sentence only)
        first_sentence = docstring.split('.')[0] if docstring else ""
        doc_words = re.findall(r'\b\w+\b', first_sentence.lower())
        keywords.extend(doc_words)
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'with', 'for', 'to', 'in', 'on', 'of'}
        keywords = [word for word in keywords if word not in common_words and len(word) > 2]
        
        return list(set(keywords))  # Remove duplicates
    
    def _direct_intent_match(self, prompt: str) -> Optional[str]:
        """Match prompt to function using intent patterns."""
        prompt_lower = prompt.lower()
        
        logger.info(f"Attempting to match prompt: '{prompt_lower}'")
        
        for pattern, function_name in self.intent_patterns.items():
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                logger.info(f"Intent match: '{prompt}' -> {function_name} (pattern: {pattern})")
                return function_name
        
        logger.info(f"No intent match found for: '{prompt}'")
        return None
    
    def _simple_keyword_match(self, prompt: str) -> Optional[Dict]:
        """Simple keyword-based function matching as fallback."""
        # Try direct intent matching first
        intent_match = self._direct_intent_match(prompt)
        if intent_match and intent_match in self.available_functions:
            func_info = self.available_functions[intent_match]
            logger.info(f"Direct intent match found: {intent_match}")
            
            # Create a matching format similar to vector_db.search_function
            parameters = []
            try:
                # Extract parameters
                signature = inspect.signature(func_info['function'])
                parameters = [
                    {
                        'name': name,
                        'default': str(param.default) if param.default is not inspect.Parameter.empty else None,
                        'required': param.default is inspect.Parameter.empty and param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.VAR_KEYWORD
                    }
                    for name, param in signature.parameters.items()
                ]
            except Exception as e:
                logger.error(f"Error extracting parameters for {intent_match}: {str(e)}")
            
            return {
                "id": f"{func_info['module']}.{func_info['name']}",
                "name": func_info['name'],
                "module": func_info['module'],
                "docstring": func_info['docstring'],
                "parameters": parameters,
                "relevance_score": 0.95
            }
        
        # Fall back to keyword matching
        prompt_words = set(re.findall(r'\b\w+\b', prompt.lower()))
        best_match = None
        best_score = 0
        
        for name, func_info in self.available_functions.items():
            # Calculate a simple match score based on keyword overlap
            keywords = set(func_info['keywords'])
            common_words = prompt_words.intersection(keywords)
            score = len(common_words) / max(1, len(keywords))
            
            logger.info(f"Keyword match for {name}: {score} (common words: {common_words})")
            
            if score > best_score:
                best_score = score
                
                # Create a matching format similar to vector_db.search_function
                parameters = []
                try:
                    # Extract parameters
                    signature = inspect.signature(func_info['function'])
                    parameters = [
                        {
                            'name': name,
                            'default': str(param.default) if param.default is not inspect.Parameter.empty else None,
                            'required': param.default is inspect.Parameter.empty and param.kind != inspect.Parameter.VAR_POSITIONAL and param.kind != inspect.Parameter.VAR_KEYWORD
                        }
                        for name, param in signature.parameters.items()
                    ]
                except Exception as e:
                    logger.error(f"Error extracting parameters for {name}: {str(e)}")
                
                best_match = {
                    "id": f"{func_info['module']}.{func_info['name']}",
                    "name": func_info['name'],
                    "module": func_info['module'],
                    "docstring": func_info['docstring'],
                    "parameters": parameters,
                    "relevance_score": score
                }
        
        # Only return matches with a minimum score
        if best_score >= 0.1:
            logger.info(f"Best keyword match: {best_match['name']} with score {best_score}")
            return best_match
        
        return None
    
    def _extract_parameters(self, prompt: str, function_metadata: Dict) -> Dict[str, Any]:
        """Extract potential parameters from the user prompt."""
        if not function_metadata or "parameters" not in function_metadata:
            return {}
        
        extracted_params = {}
        
        # For each parameter, try to find a value in the prompt
        for param in function_metadata["parameters"]:
            param_name = param["name"]
            
            # Create regex patterns for common parameter formats
            patterns = [
                rf"{param_name}\s*[=:]\s*[\"']?([^\"',\s]+)[\"']?",  # name="value" or name: value
                rf"{param_name}\s+(?:is|should be|as)\s+[\"']?([^\"',\s]+)[\"']?",  # name is value
                rf"with\s+(?:a|the)?\s*{param_name}\s+(?:of|as)\s+[\"']?([^\"',\s]+)[\"']?",  # with a name of value
                rf"[\"']([^\"',\s]+)[\"']\s+(?:for|as)\s+(?:the)?\s*{param_name}"  # "value" for the name
            ]
            
            # Try each pattern
            for pattern in patterns:
                matches = re.search(pattern, prompt, re.IGNORECASE)
                if matches:
                    extracted_params[param_name] = matches.group(1)
                    break
        
        return extracted_params
    
    def process_request(self, prompt: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a user request, find the appropriate function, and generate code."""
        try:
            # Create session if not provided
            if not session_id:
                session_id = self.context_manager.create_session()
            
            # Enhance prompt with history context
            enhanced_prompt = self.context_manager.enhance_prompt_with_history(session_id, prompt)
            
            # First try direct intent matching
            best_match = self._simple_keyword_match(enhanced_prompt)
            
            # Only try vector search if direct matching fails
            if not best_match:
                search_results = self.vector_db.search_function(enhanced_prompt)
                if search_results:
                    best_match = search_results[0]
                    logger.info(f"Vector search match: {best_match['name']} (score: {best_match['relevance_score']:.2f})")
            
            if not best_match:
                error_response = {
                    "success": False,
                    "error": "No matching function found for your request.",
                    "prompt": prompt,
                    "session_id": session_id
                }
                self.context_manager.add_interaction(session_id, prompt, None, error_response)
                return error_response
            
            logger.info(f"Best function match: {best_match['name']}")
            
            # Extract parameters from prompt
            extracted_params = self._extract_parameters(prompt, best_match)
            
            # Validate parameters
            try:
                valid_params = self.code_generator.validate_parameters(best_match, extracted_params)
            except ValueError as e:
                error_response = {
                    "success": False,
                    "error": str(e),
                    "function": best_match['id'],
                    "prompt": prompt,
                    "session_id": session_id
                }
                self.context_manager.add_interaction(session_id, prompt, best_match['id'], error_response)
                return error_response
            
            # Generate executable code
            generated_code = self.code_generator.generate_code(best_match, valid_params)
            
            # Execute the function if appropriate
            execution_result = self.code_generator.execute_function(best_match, valid_params)
            
            # Create response
            response = {
                "success": True,
                "function": best_match['id'],
                "function_name": best_match['name'],
                "relevance_score": best_match['relevance_score'],
                "parameters": valid_params,
                "code": generated_code,
                "execution_result": execution_result,
                "prompt": prompt,
                "session_id": session_id
            }
            
            # Record the interaction
            self.context_manager.add_interaction(
                session_id, 
                prompt, 
                best_match['id'], 
                execution_result
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            error_response = {
                "success": False,
                "error": f"Error processing request: {str(e)}",
                "prompt": prompt,
                "session_id": session_id
            }
            self.context_manager.add_interaction(session_id, prompt, None, error_response)
            return error_response
    
    def initialize_function_registry(self, module_paths: List[str]) -> Dict[str, Any]:
        """Initialize the function registry with functions from specified modules."""
        results = {}
        for module_path in module_paths:
            try:
                registered = self.vector_db.register_functions_from_module(module_path)
                results[module_path] = {
                    "success": True,
                    "count": len(registered),
                    "functions": registered
                }
            except Exception as e:
                logger.error(f"Error registering functions from {module_path}: {str(e)}", exc_info=True)
                results[module_path] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results 