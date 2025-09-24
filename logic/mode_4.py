# Mode 4: Description Agent
# Generates natural language descriptions from a header and structured JSON body.

from typing import Dict, Any, Optional, Union
from utils.generator import GroqGenerator
from utils.validator import calculate_max_tokens
import json

class Mode4Logic:
    def __init__(self):
        self.generator = GroqGenerator()
    
    def get_system_prompt(self) -> str:
        return (
            """
            You are a financial transaction narrator. Your task is to convert JSON transaction data into natural, meaningful descriptions using logical reasoning.
            
            IMPORTANT: Generate varied descriptions each time. If asked to regenerate, provide a different but equally accurate version.
            
            YOUR PROCESS:
            ANALYZE the transaction data:

            Extract: amount, recipient/merchant, date, method, category
            Look for: reference, purpose, memo, description fields
            Check for: recurring patterns, location, timing clues


            DETERMINE recipient type:

            Business: LLC/Inc/Corp suffixes, brand names, service keywords
            Personal: First name + last name only, no business indicators
            Utility/Government: Official names, department titles, .gov domains


            INFER likely purpose using these patterns:
            By Amount:

            $1-25: Coffee, snacks, parking, small items
            $26-100: Meals, gas, groceries, app subscriptions
            $101-500: Bills, utilities, shopping, car payments
            $501-2000: Rent, insurance, major purchases
            $2000+: Salary, large transfers, investments

            By Recipient Name:

            "Starbucks/Coffee shop" → coffee/food purchase
            "Gas Station/Shell/BP" → fuel purchase
            "Dr./Medical Center" → healthcare payment
            "Electric/Water/Gas Company" → utility bill
            "Netflix/Spotify" → subscription service
            Personal names → individual transfer

            By Timing:

            Same amount monthly → recurring bill or rent
            Bi-weekly deposits → salary payments
            End of month → utility/rent payments


            GENERATE description following this exact format:
            "[Transaction type] of $[amount] [to/from] [recipient] [for inferred purpose]"

            EXAMPLES TO FOLLOW:
            Input: {"amount": 1200, "recipient": "Sunset Apartments LLC", "date": "2024-02-01"}
            Analysis: $1200 + LLC business + Feb 1st = rent payment
            Output: "Payment of $1,200.00 to Sunset Apartments LLC for monthly rent."
            Input: {"amount": 45.50, "merchant": "Shell Gas Station", "method": "credit_card"}
            Analysis: Mid-range amount + gas station = fuel purchase
            Output: "Payment of $45.50 at Shell Gas Station for fuel."
            Input: {"amount": 2800, "sender": "ABC Manufacturing Inc", "type": "deposit"}
            Analysis: Large deposit + Inc business = salary
            Output: "Deposit of $2,800.00 from ABC Manufacturing Inc for salary payment."
            Input: {"amount": 25, "recipient": "Mike Johnson", "method": "venmo"}
            Analysis: Small amount + personal name + P2P = personal transfer
            Output: "Transfer of $25.00 to Mike Johnson."
            SAFETY RULES:

            NEVER speculate about personal relationships or private details
            When purpose is unclear, use neutral language: "Payment to [recipient]"
            DON'T make assumptions about financial situations
            If unsure about recipient type, use generic terms like "merchant" or "business"

            LANGUAGE VARIATIONS:
            Use different words each time:

            Transaction types: Payment, Transfer, Purchase, Deposit, Transaction
            Connectors: to, from, at, with
            Purpose words: for, regarding, related to, as a

            Now analyze the provided transaction and generate a natural description following this process.
            """
                   
            
            # """
            # You are a structured data interpreter and narrative generator. Your role is to analyze JSON payloads and convert them into natural language descriptions based on the context and tone specified in `{header}`.

            # The `{header}` will define your narrative approach (e.g., "Transaction Description Generator", "Product Summary Creator", "Event Report Writer"). Use this to determine:
            # - The appropriate tone and formality level
            # - The target audience and use case
            # - The level of detail and technical specificity
            # - The narrative structure and flow

            # When processing the structured JSON body, extract relevant information from the JSON structure and weave it into coherent, natural-sounding descriptions that serve the specified purpose.

            # Here are examples of how to handle different payload types:

            # **Example 1:**
            # Header: "Transaction Description Generator"
            # Payload: `{"amount": 45.99, "merchant": "Coffee Bean Cafe", "category": "Food & Dining", "date": "2024-01-15", "method": "credit_card"}`
            # Output: "Transfer of $45.99 to Coffee Bean Cafe for coffee and snacks."

            # **Example 2:**
            # Header: "Transaction Description Generator"
            # Payload: `{"amount": 1250.00, "recipient": "John Smith", "date": "2024-01-20", "method": "bank_transfer", "reference": "Rent payment February 2024"}`
            # Output: "Transfer of $1,250.00 to John Smith for February rent."

            # **Example 3:**
            # Header: "Transaction Description Generator"
            # Payload: `{"amount": 2500.00, "sender": "Acme Corp", "date": "2024-01-18", "method": "direct_deposit"}`
            # Output: "Transfer of $2,500.00 from Acme Corp for salary payment."

            # **Example 4:**
            # Header: "Product Summary Creator"
            # Payload: `{"name": "Wireless Bluetooth Headphones", "price": 129.99, "rating": 4.3, "reviews": 1247, "features": ["noise_cancellation", "30hr_battery", "quick_charge"]}`
            # Output: "The Wireless Bluetooth Headphones are priced at $129.99 and have earned a solid 4.3-star rating from 1,247 customer reviews. Key features include advanced noise cancellation technology, an impressive 30-hour battery life, and convenient quick charge capability."

            # **Example 5:**
            # Header: "Event Report Writer"
            # Payload: `{"event_type": "webinar", "title": "Digital Marketing Trends", "attendees": 342, "duration": 90, "engagement_rate": 0.78, "host": "Marketing Pro Institute"}`
            # Output: "The Marketing Pro Institute hosted a 90-minute webinar titled 'Digital Marketing Trends' which attracted 342 attendees. The session achieved a strong engagement rate of 78%, indicating high participant interest and interaction throughout the presentation."     
            # """
            
            # "You are a description agent. Given a high-level context (header) and a structured JSON body, "
            # "generate one or more clear, natural language descriptions that accurately summarize or describe the contents. "
            # "Descriptions should be human-readable, contextually relevant, and faithful to the data."
        )
    
    def prepare_user_message(
        self,
        header: str,
        body: Dict[str, Any],
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        formatted_body = json.dumps(body, indent=2)
        message = (          
            f"Header: {header}\n\n"
            f"Body (JSON):\n{formatted_body}\n\n"
            "Based on the specified context, please convert the following JSON data into a natural language description:"
            "Generate one or more natural language descriptions that summarize or describe the above payload. "
            "Generate a clear, natural-sounding description that appropriately interprets and presents the structured data."
            "Descriptions should be clear, concise, and appropriate to the header context."
        )
        if max_output_length:
            length_type = max_output_length.get("type", "characters")
            length_value = max_output_length.get("value", 200)
            message += f"\n\nIMPORTANT: Keep your description(s) to a maximum of {length_value} {length_type}."
        return message
    
    def get_generation_parameters(self) -> dict:
        return {"temperature": 0.2, "top_p": 0.95}
    
    async def process(
        self,
        header: str,
        body: Dict[str, Any],
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(header, body, max_output_length)
        gen_params = self.get_generation_parameters()
        max_tokens = calculate_max_tokens(max_output_length)
        completion = await self.generator.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        return completion