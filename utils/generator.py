
from dotenv import load_dotenv
import os
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
import logging
import time
from typing import Optional


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")
model = GroqModel(
    'llama-3.1-8b-instant',  
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


# Lightweight logger for generation statistics
logger = logging.getLogger(__name__)
if not logger.handlers:
	# configure basic handler if the app hasn't already
	handler = logging.StreamHandler()
	fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
	handler.setFormatter(logging.Formatter(fmt))
	logger.addHandler(handler)
	logger.setLevel(logging.INFO)


def _tail_text(text: str, max_chars: int = 3000) -> str:
	"""Return the last max_chars of text (helpful to keep continuation context small)."""
	if not text:
		return ""
	return text[-max_chars:]


async def generate_with_continuation(
	system_prompt: str,
	user_message: str,
	max_tokens: int = 2048,
	temperature: float = 0.0,
	top_p: float = 0.9,
	end_marker: str = "<END_OF_DOCUMENT>",
	max_iterations: int = 4,
	continuation_system_instructions: Optional[str] = None,
) -> str:
	"""
	Generate output and, if trimmed, attempt to continue the generation until an end marker is seen
	or max_iterations is reached.

	Usage pattern:
	- Include the `end_marker` in your prompt's instructions so the model can signal completion.
	- This function will call `generate()` to produce an initial chunk and then call it again
	  with a small "continue" prompt that includes a tail of the previous output to resume.

	Notes:
	- Continuation appends the previous tail to reduce token usage.
	- Temperature defaults to 0.0 for more deterministic continuing behavior.
	"""
	start_time = time.time()
	attempt = 0
	accumulated = ""

	# Initial generation
	attempt += 1
	generated = await generate(system_prompt, user_message, max_tokens=max_tokens, temperature=temperature, top_p=top_p)
	accumulated += generated

	# If the model was instructed to append an explicit end_marker, honor that. Otherwise we'll
	# use a heuristic (see below) to decide whether to continue.
	while attempt < max_iterations and end_marker not in accumulated:
		attempt += 1

		# Heuristic: if the output ends with an incomplete line or doesn't contain a natural ending,
		# ask the model to continue. We keep only the tail to avoid blowing past the context window.
		tail = _tail_text(accumulated, max_chars=3000)

		cont_system = continuation_system_instructions or (
			"You are continuing a document generation. Finish the document and when fully finished, append the exact marker: " + end_marker
		)

		cont_user = (
			"The previous partial output (possibly truncated) is below. Continue the document where it left off.\n"
			"Only continue; do not repeat the full document. If you reach the true end of the document, append the exact marker: "
			f"{end_marker}\n---\n" + tail
		)

		more = await generate(cont_system, cont_user, max_tokens=max_tokens, temperature=temperature, top_p=top_p)
		# Append a separator to make clear joins between chunks
		accumulated += "\n" + more

		# Quick safety: if continuation produced nothing new, break to avoid infinite loop
		if not more.strip():
			break

	duration = time.time() - start_time
	# Simple words/pages stat
	word_count = len(accumulated.split())
	approx_pages = max(1, word_count // 450)
	logger.info(f"[generator] gen_attempts={attempt} words={word_count} approx_pages={approx_pages} duration_s={duration:.2f}")

	return accumulated

