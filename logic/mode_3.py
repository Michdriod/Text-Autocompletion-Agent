# Mode 3: Flexible Input Refinement
# This mode focuses on improving and polishing text that may be messy,
# incomplete, or grammatically incorrect. It maintains the original meaning
# while enhancing clarity and structure.


from utils.generator import GroqGenerator

class Mode3Logic:
    def __init__(self):
        self.generator = GroqGenerator()
    
    def get_system_prompt(self) -> str:
        return (
            "You are a smart language refiner. The user may input messy, incomplete, or "
            "grammatically incorrect text. Your job is to infer the user's intent and rewrite "
            "the input in a polished, clear, and structured form. Do not change the meaning. "
            "Focus on grammar, clarity, and coherence."
        )
    
    def prepare_user_message(self, text: str) -> str:
        return f"Refine and polish this text: {text}"
    
    def get_generation_parameters(self) -> dict:
        return {"temperature": 0.2, "top_p": 0.95}
    
    async def process(self, text: str, max_tokens: int) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(text)
        gen_params = self.get_generation_parameters()
        
        completion = await self.generator.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        
        return completion