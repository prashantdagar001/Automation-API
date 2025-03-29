import inspect
import importlib
from typing import Dict, Any, List, Optional

class CodeGenerator:
    def __init__(self):
        """Initialize the code generator."""
        pass
    
    def _generate_import_statement(self, module_name: str, function_name: str) -> str:
        """Generate import statement for the function."""
        return f"from {module_name} import {function_name}"
    
    def _format_parameter_value(self, value: Any) -> str:
        """Format parameter value based on its type."""
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)
    
    def _generate_function_call(self, function_name: str, params: Dict[str, Any]) -> str:
        """Generate a function call with parameters."""
        param_strs = []
        for name, value in params.items():
            if value is not None:
                param_strs.append(f"{name}={self._format_parameter_value(value)}")
        
        params_str = ", ".join(param_strs)
        return f"{function_name}({params_str})"
    
    def _generate_error_handling(self, function_call: str) -> str:
        """Generate error handling code around a function call."""
        return f"""try:
    result = {function_call}
    print(f"Function executed successfully: {{result}}")
    return result
except Exception as e:
    print(f"Error executing function: {{e}}")
    return {{"error": str(e)}}"""
    
    def generate_code(self, function_metadata: Dict, params: Optional[Dict[str, Any]] = None) -> str:
        """Generate executable Python code for the function."""
        if not function_metadata:
            return "# No function metadata provided"
        
        module_name = function_metadata["module"]
        function_name = function_metadata["name"]
        
        # Generate import statement
        import_stmt = self._generate_import_statement(module_name, function_name)
        
        # Generate function call with parameters
        if params is None:
            params = {}
        function_call = self._generate_function_call(function_name, params)
        
        # Generate error handling
        error_handling = self._generate_error_handling(function_call)
        
        # Generate the complete script
        code = f"""{import_stmt}

def main():
    {error_handling}

if __name__ == "__main__":
    main()
"""
        return code
    
    def execute_function(self, function_metadata: Dict, params: Optional[Dict[str, Any]] = None) -> Any:
        """Dynamically execute the function using the metadata."""
        try:
            # Import the module and get the function
            module_name = function_metadata["module"]
            function_name = function_metadata["name"]
            
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)
            
            # Execute the function with parameters
            if params is None:
                params = {}
            
            result = function(**params)
            return {
                "success": True,
                "result": result,
                "function": f"{module_name}.{function_name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "function": f"{module_name}.{function_name}" if 'module_name' in locals() and 'function_name' in locals() else "unknown"
            }
    
    def validate_parameters(self, function_metadata: Dict, provided_params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and prepare parameters for the function."""
        if not function_metadata or "parameters" not in function_metadata:
            return provided_params
        
        valid_params = {}
        required_params = []
        
        # Check which parameters are required and which have defaults
        for param in function_metadata["parameters"]:
            param_name = param["name"]
            
            # Add provided parameter if available
            if param_name in provided_params:
                valid_params[param_name] = provided_params[param_name]
            # Otherwise, check if it's required
            elif param["required"]:
                required_params.append(param_name)
        
        # If there are missing required parameters, raise an error
        if required_params:
            raise ValueError(f"Missing required parameters: {', '.join(required_params)}")
        
        return valid_params 