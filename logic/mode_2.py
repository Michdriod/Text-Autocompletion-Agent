# Mode 2: Structured Context Enrichment
# This mode generates meaningful output from a topic and its context.
# It elaborates on the topic using the provided context while maintaining
# relevance and coherence. Supports dynamic output length control.

from typing import Optional, Dict, Union
from utils.generator import get_generator
from utils.validator import calculate_max_tokens

class Mode2Logic:
    def __init__(self):
        # Use singleton generator for better performance
        self.generator = get_generator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a structured content generator. Your task is to create meaningful, "
            "engaging content based on the provided topic and context. Focus on elaborating "
            "the topic using the context as a foundation. Maintain relevance and coherence "
            "while adding value through thoughtful expansion. Keep your output clear, "
            "well-structured, and focused on the topic."
        )
    
    def prepare_user_message(
        self, 
        text: str, 
        header: str, 
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        message = (
            f"Topic: {header}\n\n"
            f"Context: {text}\n\n"
            "Generate a meaningful elaboration of this topic using the provided context. "
            "Focus on creating engaging, relevant content that expands on the topic while "
            "maintaining coherence with the context."
        )
        
        if max_output_length:
            length_type = max_output_length.get("type", "characters")
            length_value = max_output_length.get("value", 200)
            message += f"\n\nIMPORTANT: Keep your elaboration to a maximum of {length_value} {length_type}."
        
        return message
    
    def get_generation_parameters(self) -> dict:
        # Use moderate temperature for balanced creativity and coherence
        return {"temperature": 0.4, "top_p": 0.9}
    
    async def process(
        self, 
        text: str, 
        header: str, 
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(text, header, max_output_length)
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