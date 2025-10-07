
from dotenv import load_dotenv
import os
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")
model = GroqModel(
    'llama-3.3-70b-versatile',  
    provider=GroqProvider(api_key=api_key)
)
agent = Agent(model)

# llama-3.3-70b-versatile
# openai/gpt-oss-20b
# llama-3.1-8b-instant
# moonshotai/kimi-k2-instruct-0905


async def generate(
	system_prompt: str,
	user_message: str,
	max_tokens: int = 8192,
	temperature: float = 0.7,
	top_p: float = 0.9
    # reasoning_effort="medium"
) -> str:
	prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_message}"
	result = await agent.run(
		prompt,
		model_settings=ModelSettings(
			max_tokens=max_tokens,
			temperature=temperature,
			top_p=top_p
            # reasoning_effort=reasoning_effort
		),
	)
	return result.output

