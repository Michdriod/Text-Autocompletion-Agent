# Mode 1: Context-Aware Regenerative Completion
# This mode enhances long-form user input using AI while preserving context.
# It maintains the style, tone, and semantics of the input text while generating
# enriched versions with dynamic output length control.

from typing import Optional, Dict, Union
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length


class Mode1:
    """
    Context-Aware Regenerative Completion
    Enhances long-form user input using AI while preserving context.
    Maintains the style, tone, and semantics of the input text while generating
    enriched versions with dynamic output length control.
    """

    def get_system_prompt(self) -> str:
        return (
            """
            You are an expert content completion assistant. Your task is to read partial or incomplete statements and complete them naturally based on semantic understanding and context clues.

            When given a context fragment in `{text}`, you should:
            - Analyze the existing content for tone, style, and intent
            - Complete the thought or statement logically and coherently
            - Maintain consistency with the established voice and perspective
            - Ensure the completion flows naturally from the provided context
            - Avoid adding unnecessary complexity or changing the original direction

            Your completion should feel like a natural continuation that the original author might have written themselves.
            """
        )

    def prepare_user_message(self, text: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> str:
        message = (
            "Continue the following text naturally. Preserve tone, voice, tense, and intent. "
            "If it ends mid-thought, resolve it smoothly without forcing an artificial conclusion.\n\n"
            f"Input:\n{text}\n\n"
            "Produce a seamless continuation (not a rewrite of the original portion)."
        )
        return message + build_length_instruction(max_output_length)

    def get_generation_parameters(self) -> dict:
        # Use lower temperature for more focused, context-preserving enrichment
        return {"temperature": 0.3, "top_p": 0.9}

    async def process(
        self,
        text: str,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        gen_params = self.get_generation_parameters()
        # Unified length planning (user provided constraint honored; otherwise inferred)
        plan = plan_output_length("mode_1", max_output_length, text=text)
        length_instruction_target = max_output_length or plan["constraint"]
        user_message = self.prepare_user_message(text, length_instruction_target)
        max_tokens = plan["token_budget"]

        completion = await generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        return completion