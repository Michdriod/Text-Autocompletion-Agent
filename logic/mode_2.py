# Mode 2: Structured Context Enrichment
# This mode enhances text based on a provided header/topic context.
# It maintains alignment with the topic while enriching the content
# without introducing irrelevant information.


from utils.generator import GroqGenerator

class Mode2Logic:
    def __init__(self):
        # Initialize the Groq LLM generator for text enrichment
        self.generator = GroqGenerator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a structured enrichment assistant. Using the context header provided, "
            "enrich and enhance the user's body text without adding irrelevant or new ideas. "
            "Maintain alignment with the topic. Output should be polished, clear, and relevant. "
            "Only respond using the given user context."
        )
    
    def prepare_user_message(self, text: str, header: str) -> str:
        return f"Header/Topic: {header}\n\nBody text to enrich: {text}\n\nEnriched version:"
    
    def get_generation_parameters(self, regenerate: bool = False) -> dict:
        params = {"temperature": 0.4, "top_p": 0.9}
        
        # Increase variation for regeneration requests
        if regenerate:
            params["temperature"] = min(params["temperature"] + 0.3, 0.9)
            params["top_p"] = max(params["top_p"] - 0.1, 0.7)
        
        return params
    
    async def process(self, text: str, header: str, max_tokens: int, regenerate: bool = False) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(text, header)
        gen_params = self.get_generation_parameters(regenerate)
        
        completion = await self.generator.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        
        return completion