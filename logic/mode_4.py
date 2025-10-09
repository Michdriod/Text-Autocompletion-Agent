# Mode 4: Description Agent
# Generates natural language descriptions from a header and structured JSON body.

from typing import Dict, Any, Optional, Union
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length
import json
import re
import logging


class Mode4:
    """
    Description Agent
    Generates natural language descriptions from a header and structured JSON body.
    """

    def get_system_prompt(self) -> str:
        return (
            """
            You are a financial transaction narrator. Your task is to convert JSON transaction data into clear, consistent natural-language descriptions.

            GOAL: Prefer a consistent, active phrasing for transaction descriptions. Unless the header explicitly requests variation, always produce descriptions that start with an action noun like "Transfer" or "Payment" followed by the currency and amount, then the direction (to/from) and the recipient, and finally any inferred purpose or method.

            PRIMARY PROCESS (ANALYSIS):
            - Extract: amount, recipient/merchant, date, method, category, reference/memo, description fields
            - Check for: recurring patterns, location, timing clues
            - Determine recipient type: business (LLC/Inc/Corp, brand), personal (personal name), utility/government (official titles or .gov)

            INFERENCE HINTS:
            - By amount: small purchases vs subscriptions vs bills vs rent vs salary (see examples below)
            - By recipient/merchant: map common merchants to purposes (e.g., "Shell" -> fuel)
            - By timing: repeating monthly amounts -> recurring payment/rent; end-of-month -> utilities/rent

            STYLE RULES (HIGH PRIORITY):
            - Preferred structure: "[Transaction type] of [currency][amount] to [recipient] [for inferred purpose] [via method]."
              Example (preferred): "Transfer of ₦10,000 to Hammed A. via mobile app as a gift."
            - Avoid passive constructions that begin with the amount and use verbs like "was sent", "was paid", or "was transferred", unless the header explicitly requests passive voice.
            - Always place the amount immediately after the transaction type or currency symbol and format amounts with thousands separators and up to two decimals when relevant.
            - Use the currency symbol from the 'currency' field (e.g., '₦' for NGN, '$' for USD, '€' for EUR).

            DIRECTIONALITY RULES:
            - Use "to [recipient]" for debits/outgoing transfers; "from [sender]" for credits/incoming deposits.
            - Use JSON fields to determine direction; do not invent roles.

            SAFETY RULES:
            - NEVER speculate about personal relationships or private details.
            - When purpose is unclear, use neutral phrasing: "Payment to [recipient]".
            - If unsure about recipient type, use generic terms like "merchant" or "business".

            EXAMPLES and HEURISTICS:
            - $1-25: coffee, snacks, parking
            - $26-100: meals, gas, groceries, subscriptions
            - $101-500: bills, utilities, shopping
            - $501-2000: rent, insurance, major purchases
            - $2000+: salary, large transfers

            Example transformations:
            Input: {"amount": 1200, "recipient": "Sunset Apartments LLC", "date": "2024-02-01"}
            Output: "Payment of $1,200.00 to Sunset Apartments LLC for monthly rent."

            Input: {"amount": 45.50, "merchant": "Shell Gas Station", "method": "credit_card"}
            Output: "Payment of $45.50 at Shell Gas Station for fuel."

            Input: {"amount": 2800, "sender": "ABC Manufacturing Inc", "type": "deposit"}
            Output: "Deposit of $2,800.00 from ABC Manufacturing Inc for salary payment."

            Input: {"amount": 25, "recipient": "Mike Johnson", "method": "venmo"}
            Output: "Transfer of $25.00 to Mike Johnson."

            Now analyze the provided transaction and generate a single, concise natural description following the preferred active structure above. If the header explicitly requests variation, adjust tone or voice accordingly.
            """
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
        return message + build_length_instruction(max_output_length)

    def get_generation_parameters(self) -> dict:
        return {"temperature": 0.2, "top_p": 0.95}

    async def process(
        self,
        header: str,
        body: Dict[str, Any],
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        gen_params = self.get_generation_parameters()
        plan = plan_output_length("mode_4", max_output_length, body=body)
        length_instruction_target = max_output_length or plan["constraint"]
        user_message = self.prepare_user_message(header, body, length_instruction_target)
        max_tokens = plan["token_budget"]

        completion = await generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )

        # Passive-voice detection: if output starts with a currency symbol or contains passive verbs,
        # request a forced active rewrite.
        passive_pattern = re.compile(r"^(\s*[₦$€]\d|.*\b(was sent|was paid|was transferred)\b)", re.IGNORECASE)
        if passive_pattern.search(completion):
            forced_instruction = (
                "The previous output used passive phrasing. Please rewrite the description using the preferred active structure: "
                "Start with an action noun such as 'Transfer' or 'Payment', then 'of [currency][amount] to [recipient] ...'. Do NOT use passive voice."
            )
            regen_system = system_prompt + "\n\nPriority: enforce active phrasing."
            regen_user = user_message + "\n\n" + forced_instruction
            logging.getLogger(__name__).info("[Mode4] Passive phrasing detected; regenerating with active-voice enforcement.")
            regen = await generate(
                system_prompt=regen_system,
                user_message=regen_user,
                max_tokens=max_tokens,
                temperature=0.1,
                top_p=0.95,
            )
            return regen

        return completion