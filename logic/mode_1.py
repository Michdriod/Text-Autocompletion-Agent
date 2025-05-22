# Mode 1: Context-Aware Completion
# This mode provides intelligent text continuation based on the given context.
# It maintains the style, tone, and semantics of the input text while generating
# natural continuations.

from utils.generator import GroqGenerator

class Mode1Logic:    
    def __init__(self):
        # Initialize the Groq LLM generator for text completion
        self.generator = GroqGenerator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a context-aware writing assistant. Given a coherent input from the user, "
            "your task is to intelligently continue or complete the text based strictly on the "
            "user's intent. Do not invent new context. Stay within the style, tone, and semantics "
            "of the given content. Always generate a natural, logical continuation."
        )
    
    def prepare_user_message(self, text: str) -> str:
        return f"Continue this text naturally: {text}"
    
    def get_generation_parameters(self, regenerate: bool = False) -> dict:
        params = {"temperature": 0.3, "top_p": 0.95}
        
        # Increase variation for regeneration requests
        if regenerate:
            params["temperature"] = min(params["temperature"] + 0.3, 0.9)
            params["top_p"] = max(params["top_p"] - 0.1, 0.7)
        
        return params
    
    async def process(self, text: str, max_tokens: int, regenerate: bool = False) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(text)
        gen_params = self.get_generation_parameters(regenerate)
        
        completion = await self.generator.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        
        return completion