# Mode 4: Description Agent
# Generates natural language descriptions from a header and structured JSON body.

from typing import Dict, Any, Optional, Union
from utils.generator import get_generator
from utils.validator import calculate_max_tokens
import json

class Mode4Logic:
    def __init__(self):
        # Use singleton generator for better performance
        self.generator = get_generator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a description agent. Given a high-level context (header) and a structured JSON body, "
            "generate one or more clear, natural language descriptions that accurately summarize or describe the contents. "
            "Descriptions should be human-readable, contextually relevant, and faithful to the data."
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
            "Generate one or more natural language descriptions that summarize or describe the above payload. "
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