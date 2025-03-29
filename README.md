# Automation Function API

A Python-based API service that dynamically retrieves and executes automation functions using Large Language Models (LLM) and Retrieval-Augmented Generation (RAG).

## Features

- **Function Registry**: Collection of automation functions for applications, system monitoring, and command execution
- **LLM + RAG for Function Retrieval**: Vector database storage of function metadata with semantic search
- **Dynamic Code Generation**: Automatic generation of executable Python code based on user prompts
- **Context Management**: Session-based memory to maintain chat history for improved function retrieval
- **REST API**: FastAPI-based service with comprehensive endpoints

## Project Structure

```
automation_api/
├── app/
│   ├── api/
│   │   ├── models.py      # Pydantic models for API requests/responses
│   │   └── routes.py      # FastAPI route definitions
│   ├── core/
│   │   ├── code_generator.py     # Code generation functionality
│   │   ├── context_manager.py    # Session management
│   │   └── service_processor.py  # Core service logic
│   ├── db/
│   │   └── vector_db.py   # Vector database implementation
│   ├── functions/
│   │   └── automation_functions.py  # Registry of automation functions
│   └── main.py            # FastAPI application
└── requirements.txt       # Project dependencies
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd automation_api
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the API

Start the API service:

```bash
cd automation_api
python -m app.main
```

The API will be available at `http://localhost:8000`.

## API Endpoints

- **POST /api/execute**: Execute an automation function based on user prompt
  ```json
  { "prompt": "Open calculator" }
  ```

- **POST /api/session/create**: Create a new session
  ```json
  {}
  ```

- **POST /api/session/history**: Get session history
  ```json
  { "session_id": "your-session-id" }
  ```

- **POST /api/registry/initialize**: Initialize function registry with modules
  ```json
  { "module_paths": ["app.functions.custom_functions"] }
  ```

- **GET /api/registry/status**: Get function registry status

- **POST /api/cleanup**: Clean up old sessions

## Example Usage

### Execute Function

Request:
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Open calculator"}'
```

Response:
```json
{
  "success": true,
  "function": "app.functions.automation_functions.open_calculator",
  "function_name": "open_calculator",
  "relevance_score": 0.92,
  "parameters": {},
  "code": "from app.functions.automation_functions import open_calculator\n\ndef main():\n    try:\n        result = open_calculator()\n        print(f\"Function executed successfully: {result}\")\n        return result\n    except Exception as e:\n        print(f\"Error executing function: {e}\")\n        return {\"error\": str(e)}\n\nif __name__ == \"__main__\":\n    main()",
  "execution_result": {
    "success": true,
    "result": "Calculator opened",
    "function": "app.functions.automation_functions.open_calculator"
  },
  "prompt": "Open calculator",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Extending the System

### Adding Custom Functions

1. Create a new module in the `app/functions/` directory:

```python
# app/functions/custom_functions.py
def my_custom_function(parameter1, parameter2="default"):
    """Description of what this function does."""
    # Implementation
    return f"Result with {parameter1} and {parameter2}"
```

2. Register the module:

```bash
curl -X POST http://localhost:8000/api/registry/initialize \
  -H "Content-Type: application/json" \
  -d '{"module_paths": ["app.functions.custom_functions"]}'
```

## License

[MIT License](LICENSE) # Automation-API
