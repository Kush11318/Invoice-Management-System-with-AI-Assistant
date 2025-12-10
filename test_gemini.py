import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

with open('test_result.txt', 'w') as f:
    sys.stdout = f
    print("Listing available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")

    from ai_service import parse_command, model
    import json

    print(f"\nUsing model: {model.model_name}")

    context = {
        'products': [{'name': 'Widget', 'price': 10.0, 'stock': 100}],
        'customers': [{'name': 'Customer A', 'email': 'a@example.com'}]
    }

    user_text = "Create an invoice for Customer A for 5 Widgets"

    print("\nTesting Gemini API...")
    try:
        result = parse_command(user_text, context)
        print("Result:")
        print(json.dumps(result, indent=2))
        
        if result.get('intent') == 'create_invoice':
            print("\nSUCCESS: Intent recognized correctly.")
        else:
            print("\nFAILURE: Intent not recognized.")
            
    except Exception as e:
        print(f"\nERROR: {e}")
