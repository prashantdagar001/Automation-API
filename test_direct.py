"""
Direct test script for opening the calculator
"""
from app.functions.automation_functions import open_calculator

def main():
    print("Directly testing the open_calculator function...")
    try:
        result = open_calculator()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 