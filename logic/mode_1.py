# Mode 1: Intelligent Text Autocomplete
# This mode continues user input based on context, tone, and style.
# It analyzes the semantic intent and writing characteristics of the input,
# then generates a natural continuation that matches the original author's voice.
# Perfect for completing partial thoughts, sentences, or paragraphs.

from typing import Optional, Dict, Union
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length


class Mode1:
    """
    Intelligent Text Autocomplete
    
    Continues user input by analyzing context, tone, style, and semantic intent.
    Generates natural continuations that feel like they were written by the same person.
    
    Key Features:
    - Context-aware continuation (not rewriting)
    - Tone and style preservation
    - Semantic coherence
    - Topic consistency
    - Voice matching (formal, casual, technical, creative, etc.)
    """

    def get_system_prompt(self) -> str:
        return (
            """
            You are an intelligent text autocomplete system. Your ONLY output is the continuation text itself — nothing else.

            CRITICAL OUTPUT RULE:
            - Your response will be directly appended to the user's text
            - Do NOT include any meta-commentary, explanations, or formatting
            - Do NOT write "Here is the continuation:" or "Based on the text..." or similar phrases
            - Do NOT include checkmarks, labels, or instructions in your output
            - Start immediately with the next word that should follow the user's text

            Your Task:
            1. ANALYZE THE INPUT:
               - Understand the semantic intent and meaning
               - Identify the writing style, tone, and emotional character
               - Detect the topic, domain, and context
               - Recognize grammatical patterns and vocabulary level
               - PAY CLOSE ATTENTION to the exact last words of the input

            2. GENERATE SEAMLESS CONTINUATION:
               - Check the last word(s) of the input before starting
               - If input ends with "the", "to", "a", "an", etc., your first word should complete that phrase grammatically
               - If input ends mid-sentence, continue that exact sentence without repeating words
               - If input ends with complete sentence, start a new related sentence naturally
               - Match the original author's voice, tone, and style perfectly
               - Stay on-topic and maintain the same subject matter
               - Use similar vocabulary sophistication and sentence structure

            3. CRITICAL RULES:
               - DO NOT repeat the user's input
               - DO NOT repeat the last word(s) of the input
               - DO NOT add meta-commentary or labels
               - Your entire response = pure continuation text only
            """
        )

    def prepare_user_message(self, text: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> str:
        # Extract the last few words to emphasize seamless continuation
        last_words = text.strip().split()[-5:] if text.strip() else []
        last_phrase = " ".join(last_words)
        
        message = (
            "Continue the text below exactly where it stops. Output ONLY the continuation — no labels, no checkmarks, no meta-commentary.\n\n"
            "CRITICAL:\n"
            "- Text ends with: \"...{}\"\n"
            "- Your first word must grammatically follow this ending\n"
            "- DO NOT repeat \"{}\" or any ending words\n"
            "- Match the original tone, style, and topic\n"
            "- Your response will be directly appended to the user's text\n\n"
            "USER'S TEXT:\n"
            "{}\n\n"
            "OUTPUT ONLY THE CONTINUATION (start with the next word):"
        ).format(last_phrase, last_phrase, text)
        return message + build_length_instruction(max_output_length)

    def get_generation_parameters(self) -> dict:
        # Use lower temperature for more focused, context-aligned continuation
        # Higher top_p for natural vocabulary diversity while maintaining coherence
        return {"temperature": 0.4, "top_p": 0.95}

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