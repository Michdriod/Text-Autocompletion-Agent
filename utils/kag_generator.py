from dotenv import load_dotenv
import os
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Mode 6 specific model
kag_model = GroqModel(
    'llama-3.1-8b-instant',  # Reliable model for Mode 6
    provider=GroqProvider(api_key=api_key)
)
kag_agent = Agent(kag_model)

async def generate_kag(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 6000,
    top_p: float = 0.9
) -> str:
    """Generate content specifically for Mode 6 (KAG system)."""
    
    result = await kag_agent.run(
        user_message,
        message_history=[("system", system_prompt)],
        model_settings=ModelSettings(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p
        )
    )
    
    return str(result.output)