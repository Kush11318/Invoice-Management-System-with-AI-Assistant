import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Use a model that supports JSON mode if possible, or instruct it clearly
model = genai.GenerativeModel('gemini-2.0-flash')

SYSTEM_PROMPT = """
You are a smart billing assistant for an Invoice Management System. 
Your goal is to extract structured data from natural language to help create invoices, add customers, or add products.

You will be provided with:
1. User Input (Natural Language)
2. Current Database Context (List of existing products and customers)

Output JSON format:
{
    "intent": "create_invoice" | "add_customer" | "add_product" | "unknown",
    "data": { ... },
    "missing_info": "Question to ask user if info is missing",
    "response_text": "Natural language response to speak back to the user"
}

For 'create_invoice':
- "data" should contain:
    - "customer_name": string (matched from context or new)
    - "is_new_customer": boolean
    - "items": list of objects { "product_name": string, "quantity": int, "is_new_product": boolean, "price": float (if mentioned), "discount": float (default 0) }
    - "tax": float (default 0)
    - "due_date": string (YYYY-MM-DD) or null

For 'add_customer':
- "data": { "name": string, "email": string, "phone": string, "address": string }

For 'add_product':
- "data": { "name": string (REQUIRED - must extract from user input), "price": float (default 0 if not mentioned), "stock": int (default 0 if not mentioned), "description": string (optional) }
- IMPORTANT: Always extract the product name from the user's input. If the user says "add product Milk", the name should be "Milk". If they say "add product called Laptop", the name should be "Laptop".

Rules:
- Fuzzy match product names from the provided context. If a product sounds similar to an existing one, use the existing name.
- If a product is definitely new (not in context), mark is_new_product=true.
- If customer is not in context, mark is_new_customer=true.
- Be helpful and concise in 'response_text'.
- If the user's intent is unclear, set intent to 'unknown' and ask for clarification in 'response_text'.
- ALWAYS return valid JSON.
"""

def parse_command(user_text, context, history=[]):
    """
    Parses user text using Gemini to extract structured data.
    context: { 'products': [...], 'customers': [...] }
    history: list of { 'sender': 'user'|'ai', 'text': '...' }
    """
    try:
        # Prepare context summary for the prompt
        product_names = [p['name'] for p in context.get('products', [])]
        customer_names = [c['name'] for c in context.get('customers', [])]
        
        context_str = f"Existing Products: {', '.join(product_names)}\nExisting Customers: {', '.join(customer_names)}"
        
        history_str = ""
        if history:
            history_str = "Conversation History:\n"
            for msg in history:
                role = "User" if msg.get('sender') == 'user' else "Assistant"
                history_str += f"{role}: {msg.get('text', '')}\n"
        
        prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context_str}\n\n{history_str}\nUser Input:\n{user_text}\n\nResponse (JSON):"
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        content = response.text
        # Clean up potential markdown code blocks if Gemini adds them despite JSON mode
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        return json.loads(content)
        
    except Exception as e:
        import traceback
        with open('error.log', 'w') as f:
            f.write(traceback.format_exc())
        print(f"AI Service Error: {e}")
        return {
            "intent": "unknown",
            "data": {},
            "missing_info": None,
            "response_text": "Sorry, I encountered an error processing your request."
        }
