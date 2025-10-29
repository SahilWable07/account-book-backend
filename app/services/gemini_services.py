import os
import requests
import json
import logging
from dotenv import load_dotenv
 
load_dotenv()
 
API_KEY = os.getenv("GEMINI_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
 
if not API_KEY:
    raise RuntimeError("❌ Gemini API key not found in .env file.")
 
logger = logging.getLogger(__name__)
 
def parse_transaction_query(text: str) -> dict:
    """
    Analyzes the user's query using Gemini AI to extract transaction details,
    intelligently inferring GST and identifying inventory and loan types.
    """
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
   
    system_prompt = f"""
    You are an intelligent financial transaction parser for India. Your task is to analyze the user's text and extract details into a structured JSON object.
 
    The JSON output MUST contain:
    - "type": "income", "expense", "loan_payable", or "loan_receivable".
    - "total_amount": The full numeric value of the transaction.
    - "description": A clear description of the item or service.
    - "category": A relevant category (e.g., "Vehicle", "Electronics", "Salary", "Loan").
    - "inventory" (optional): An object with "item", "quantity", "unit_price", and "total_value" if the query is about purchasing goods.
    - "gst_details" (optional): An object with "base_amount", "gst_amount", and "gst_percentage".
    - "gst_assumption_reason" (optional): A brief explanation if you inferred the GST rate.
 
    --- LOAN RULES (VERY IMPORTANT) ---
    1.  **loan_receivable**: If the user says they "lent money", "gave a loan", "dile", or similar phrases to another person/entity, it means money is going OUT. The type MUST be "loan_receivable".
    2.  **loan_payable**: If the user says they "borrowed money", "took a loan", "ghetle", or received money from any person/entity that is NOT their salary, it means money is coming IN as a liability. The type MUST be "loan_payable".
    3.  For any loan-related transaction, the category should be "Loan".
 
    --- GST RULES (VERY IMPORTANT) ---
    (He rules jase ahet tase ahet...)
 
    --- INVENTORY RULES ---
    (He rules jase ahet tase ahet...)
 
    --- EXAMPLES ---
    - User Input: "i purchase the swift car 1000000 rupees"
    - Your Output: {{"type": "expense", "total_amount": 1000000, "description": "Purchase swift car", "category": "Vehicle"}}
 
    - User Input: "mi aaj 10 chairs ghetlya tyanchi kimmat 1000 rupaye jhali saglya chair chi"
    - Your Output: {{"type": "expense", "total_amount": 1000, "description": "Purchase of 10 chairs", "category": "Furniture", "inventory": {{"item": "chair", "quantity": 10, "unit_price": 100, "total_value": 1000}}}}
 
    - User Input: "got my 50000 salary"
    - Your Output: {{"type": "income", "total_amount": 50000, "description": "Salary", "category": "Salary"}}
 
    - User Input: "i sold 20 quintal of soyabean at the rate 5000 rupees per quintal"
    - Your Output: {{"type": "income", "total_amount": 20000, "description": "Sale of 10 quintal wheat", "category": "Sales"}}
 
    - User Input: "lent 5000 rs to Rohan"
    - Your Output: {{"type": "loan_receivable", "total_amount": 5000, "description": "Lent money to Rohan", "category": "Loan"}}
 
    - User Input: "mitrani mla 500 dile"
    - Your Output: {{"type": "loan_payable", "total_amount": 500, "description": "Received money from friend", "category": "Loan"}}
 
    - User Input: "took a loan of 20000 from my friend"
    - Your Output: {{"type": "loan_payable", "total_amount": 20000, "description": "Took a loan from friend", "category": "Loan"}}
 
    IMPORTANT: Your response MUST be ONLY the raw, single-line, compact JSON object without any markdown.
 
    User Input: "{text}"
    """
 
    payload = {"contents": [{"parts": [{"text": system_prompt}]}]}
    raw_ai_text = ""
    try:
        resp = requests.post(API_URL, headers=headers, params=params, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
 
        raw_ai_text = data["candidates"][0]["content"]["parts"][0].get("text", "").strip()
        json_str = raw_ai_text.strip().replace('```json', '').replace('```', '')
       
        if not json_str:
            logger.error("Empty response from Gemini AI.")
            return {"error": "AI returned an empty response."}
 
        return json.loads(json_str)
 
    except requests.exceptions.RequestException as e:
        logger.error(f"API request to Gemini failed: {e}")
        return {"error": f"API request failed: {str(e)}"}
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse AI response: {e}. Raw text was: '{raw_ai_text}'")
        return {"error": "Failed to parse AI response"}
    except Exception as e:
        logger.error(f"An unexpected error occurred in Gemini service: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}
 
 
 