#!/usr/bin/env python3

from main_processing import call_openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_evil_genai_integration():
    """Test the evil GenAI integration"""
    print("🤖 Testing evil GenAI Integration...")
    
    # Check if API key is set
    api_key = os.getenv('API_KEY')
    model = os.getenv('GENAI_MODEL', 'azure.gpt-4o-mini')
    
    if not api_key:
        print("❌ API_KEY not found in .env file")
        print("Please add: API_KEY=your_evil_genai_api_key_here")
        return
    
    print(f"✅ API_KEY found: {api_key[:10]}...")
    print(f"✅ Model configured: {model}")
    
    # Test message
    test_messages = [
        {
            "role": "system", 
            "content": "You are SRYODA, a Star Wars themed SRE droid. Respond briefly with droid personality."
        },
        {
            "role": "user", 
            "content": "Hello SRYODA, are you operational?"
        }
    ]
    
    print("🚀 Sending test message to evil GenAI...")
    response = call_openai(test_messages)
    
    if response.startswith("❌"):
        print(f"💥 Error: {response}")
    else:
        print("✅ Success! evil GenAI responded:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        print("🎯 Integration working perfectly!")

if __name__ == "__main__":
    test_evil_genai_integration() 