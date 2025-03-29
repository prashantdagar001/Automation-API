import requests
import json
import sys

def print_json(data):
    """Print JSON data in a formatted way."""
    print(json.dumps(data, indent=2))

def test_prompt(prompt, base_url="http://localhost:8000"):
    """Test a specific prompt against the API."""
    print(f"\n=== Testing Prompt: '{prompt}' ===\n")
    
    # Create a session
    response = requests.post(f"{base_url}/api/session/create")
    if response.status_code == 200:
        session_id = response.json()["session_id"]
        print(f"Session created with ID: {session_id}")
    else:
        print(f"Failed to create session: {response.status_code}")
        return
    
    # Execute the prompt
    response = requests.post(
        f"{base_url}/api/execute",
        json={"prompt": prompt, "session_id": session_id}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Function matched: {result.get('function_name')}")
        print(f"Relevance score: {result.get('relevance_score')}")
        
        # Print generated code
        print("\nGenerated code:")
        print("```python")
        print(result.get('code'))
        print("```")
        
        # Print execution result
        print("\nExecution result:")
        print_json(result.get('execution_result'))
    else:
        print(f"\n❌ Failed to execute function: {response.status_code}")
        print(response.text)
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    # Get prompt from command line or use default
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Show me memory usage"
    test_prompt(prompt) 