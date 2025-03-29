import requests
import json
import time
import sys

def print_json(data):
    """Print JSON data in a formatted way."""
    print(json.dumps(data, indent=2))

def test_api(base_url="http://localhost:8000"):
    """Test the Automation Function API."""
    print("\n=== Testing Automation Function API ===\n")
    
    # 1. Check API root
    print("1. Checking API root...")
    response = requests.get(f"{base_url}/")
    if response.status_code == 200:
        print("✅ API is running")
        print_json(response.json())
    else:
        print(f"❌ API is not running: {response.status_code}")
        sys.exit(1)
    
    # 2. Create a session
    print("\n2. Creating a session...")
    response = requests.post(f"{base_url}/api/session/create")
    if response.status_code == 200:
        session_id = response.json()["session_id"]
        print(f"✅ Session created with ID: {session_id}")
    else:
        print(f"❌ Failed to create session: {response.status_code}")
        session_id = None
    
    # 3. Check registry status
    print("\n3. Checking registry status...")
    response = requests.get(f"{base_url}/api/registry/status")
    if response.status_code == 200:
        print("✅ Registry status:")
        print_json(response.json())
    else:
        print(f"❌ Failed to get registry status: {response.status_code}")
    
    # 4. Execute functions
    test_prompts = [
        "What's the current CPU usage?",
        "Open calculator",
        "Show me memory usage",
        "List the contents of the current directory"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n4.{i}. Testing execution with prompt: '{prompt}'")
        response = requests.post(
            f"{base_url}/api/execute",
            json={"prompt": prompt, "session_id": session_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Function executed: {result.get('function_name')}")
            print(f"Relevance score: {result.get('relevance_score')}")
            print(f"Parameters: {result.get('parameters')}")
            
            # Print generated code
            print("\nGenerated code:")
            print("```python")
            print(result.get('code'))
            print("```")
            
            # Print execution result
            print("\nExecution result:")
            print_json(result.get('execution_result'))
            
            # Wait a bit to see the effect (if it's opening applications)
            if "open" in prompt.lower():
                time.sleep(2)
        else:
            print(f"❌ Failed to execute function: {response.status_code}")
            print(response.text)
    
    # 5. Get session history
    if session_id:
        print("\n5. Getting session history...")
        response = requests.post(
            f"{base_url}/api/session/history",
            json={"session_id": session_id}
        )
        
        if response.status_code == 200:
            print("✅ Session history:")
            history = response.json()
            print(f"Number of interactions: {len(history.get('history', []))}")
            # Print just the prompts for brevity
            prompts = [item.get('prompt') for item in history.get('history', [])]
            print(f"Prompts: {prompts}")
        else:
            print(f"❌ Failed to get session history: {response.status_code}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    # Get optional base URL from command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_api(base_url) 