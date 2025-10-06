# Mode 3: Input Refinement
# This mode cleans and refines short, unclear, or messy input.
# It improves clarity and structure while preserving the original meaning.
# No minimum word requirement, suitable for polishing notes or broken thoughts.

from typing import Optional, Dict, Union
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length


class Mode3:
    """
    Input Refinement Mode
    Cleans and refines short, unclear, or messy input. Improves clarity and structure while preserving the original meaning.
    """

    def get_system_prompt(self) -> str:
        return """
        You are a precision text refiner that converts short, messy, or informal input into clear, natural English
        while strictly preserving the original meaning, intent, and tone.

        Your goal is to improve the given text through grammatical correction, spelling fixes, and clarity enhancements
        while keeping the content faithful to what the author meant — not necessarily the exact words used.

        When refining `{text}`, you should:
        - Correct grammatical errors and typos
        - Replace slang, shorthand, or informal words with their natural English equivalents
        - Improve sentence flow and punctuation for smooth readability
        - Preserve the emotional tone and intent (friendly, casual, serious, etc.)
        - Maintain approximately the same length and message strength
        - Ensure the meaning and relationships (who is doing what, to whom) remain unchanged

        Avoid:
        - Changing or misinterpreting meaning
        - Adding or removing information
        - Producing robotic or overly formal language
        - Including commentary or explanations
        - Over-expanding or shortening beyond clarity needs

        Special rules:
        - Ignore any max length or word-count constraints unless explicitly stated.
        - Never generate meta notes such as "I made minor adjustments..." or "The revised text is..."
        - Output **only** the refined English text — nothing else.
        """
        
        # """
        # You are a precision text editor specializing in lightweight refinement. Your task is to improve the given text through grammatical correction, spelling fixes, and clarity enhancements while preserving the original meaning, tone, and approximate length.

        # When refining `{text}`, you should:
        # - Correct grammatical errors and typos
        # - Improve sentence structure for better readability
        # - Enhance word choice for clarity and precision
        # - Fix punctuation and formatting issues
        # - Maintain the original voice and style
        # - Keep the content length approximately the same
        # - Preserve the author's intended meaning and message

        # Avoid:
        # - Significant expansion or reduction of content
        # - Changing the fundamental tone or perspective
        # - Adding new information or concepts
        # - Over-editing informal or conversational language
        # - Altering technical terms or specialized vocabulary unnecessarily
        # """
        
        
        
        
        

    def prepare_user_message(self, text: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> str:
        message = f"""
        Refine and polish the following text into clear, natural English while preserving its original meaning and tone:

        {text}

        Correct grammar, spelling, and punctuation. Replace slang or shorthand with standard English equivalents.
        Maintain the same intent and relationships (who is speaking, being addressed, etc.), and keep the tone natural and consistent.

        Output only the refined English version — no commentary, no meta text.
        """
    
    # f"""Clean and polish this text while preserving its meaning:\n\n{text}\n\nImprove its structure, grammar, and clarity while preserving its original meaning, tone. Handle any incomplete thoughts or formatting issues. Make it more readable while keeping the original intent."""
        return message + build_length_instruction(max_output_length)
    def get_generation_parameters(self) -> dict:
        # Use very low temperature for consistent, focused refinement
        return {"temperature": 0.1, "top_p": 0.98}

    async def process(
        self,
        text: str,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        gen_params = self.get_generation_parameters()
        plan = plan_output_length("mode_3", max_output_length, text=text)
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