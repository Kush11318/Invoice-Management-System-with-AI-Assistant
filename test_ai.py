from ai_service import parse_command
import os
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("OPENAI_API_KEY")
print(f"Key loaded: {bool(key)}")
if key:
    print(f"Key length: {len(key)}")
    print(f"Key start: {key[:5]}")

# Mock context
context = {
    'products': [{'p_name': 'Milk', 'p_price': 50}, {'p_name': 'Bread', 'p_price': 40}],
    'customers': [{'c_name': 'Riya'}]
}

# Test case 1: Create Invoice
text = "Bill for Riya: 2 milk and 1 bread"
print(f"Testing: {text}")
result = parse_command(text, context)
print(result)

# Test case 2: Add Product
text = "Add product Maggi price 20"
print(f"\nTesting: {text}")
result = parse_command(text, context)
print(result)
