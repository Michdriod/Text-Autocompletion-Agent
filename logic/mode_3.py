# Mode 3: Input Refinement
# This mode cleans and refines short, unclear, or messy input.
# It improves clarity and structure while preserving the original meaning.
# No minimum word requirement, suitable for polishing notes or broken thoughts.

from typing import Optional, Dict, Union
from utils.generator import GroqGenerator
from utils.validator import calculate_max_tokens

class Mode3Logic:
    def __init__(self):
        self.generator = GroqGenerator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a text refinement specialist. Your task is to clean and polish "
            "unclear, messy, or broken input while preserving its core meaning. "
            "Focus on improving grammar, structure, and clarity. Handle incomplete "
            "thoughts, typos, and poor formatting. Your goal is to make the text "
            "clear and readable while keeping the original intent intact."
        )
    
    def prepare_user_message(self, text: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> str:
        message = (
            f"Clean and polish this text while preserving its meaning:\n\n{text}\n\n"
            "Improve its structure, grammar, and clarity. Handle any incomplete thoughts "
            "or formatting issues. Make it more readable while keeping the original intent."
        )
        
        if max_output_length:
            length_type = max_output_length.get("type", "characters")
            length_value = max_output_length.get("value", 200)
            message += f"\n\nIMPORTANT: Keep your polished version to a maximum of {length_value} {length_type}."
        
        return message
    
    def get_generation_parameters(self) -> dict:
        # Use very low temperature for consistent, focused refinement
        return {"temperature": 0.1, "top_p": 0.98}
    
    async def process(
        self, 
        text: str, 
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(text, max_output_length)
        gen_params = self.get_generation_parameters()
        
        # Calculate max tokens based on output length requirements
        max_tokens = calculate_max_tokens(max_output_length)
        
        completion = await self.generator.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        
        return completion