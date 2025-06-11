# Mode 1: Context-Aware Regenerative Completion
# This mode enhances long-form user input using AI while preserving context.
# It maintains the style, tone, and semantics of the input text while generating
# enriched versions with dynamic output length control.

from typing import Optional, Dict, Union
from utils.generator import get_generator
from utils.validator import calculate_max_tokens

class Mode1Logic:
    def __init__(self):
        # Use singleton generator for better performance
        self.generator = get_generator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a context-aware writing assistant. Your task is to enhance and enrich "
            "the user's input while strictly preserving its original context, style, and intent. "
            "Do not invent new context or change the meaning. Focus on improving clarity, "
            "structure, and flow while maintaining the original message. "
            "Keep your enriched version concise and focused."
        )
    
    def prepare_user_message(self, text: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> str:
        message = (
            f"Enhance and enrich this text while preserving its context and meaning:\n\n{text}\n\n"
            "Provide an improved version that maintains the original intent but with better "
            "structure, clarity, and flow."
        )
        
        if max_output_length:
            length_type = max_output_length.get("type", "characters")
            length_value = max_output_length.get("value", 200)
            message += f"\n\nIMPORTANT: Keep your enriched version to a maximum of {length_value} {length_type}."
        
        return message
    
    def get_generation_parameters(self) -> dict:
        # Use lower temperature for more focused, context-preserving enrichment
        return {"temperature": 0.3, "top_p": 0.95}
    
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