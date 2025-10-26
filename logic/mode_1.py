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
            You are an intelligent text autocomplete system. Your role is to continue the user's writing exactly where they left off.

            CORE PRINCIPLE:
            Your output will be directly appended to their text. Think of yourself as their brain continuing the thought mid-sentence.

            INTELLIGENT CONTINUATION:
            
            1. READ AND UNDERSTAND:
               - Analyze the full context, topic, and writing style
               - Identify what the user is trying to express
               - Determine the natural direction of their thought
               
            2. ASSESS THE ENDING:
               - Look at how the text ends
               - If it ends mid-word (like "recurs"), complete that word naturally first
               - If it ends with a complete word, continue with the next logical word/phrase
               - If it ends with a space, start immediately with the next word
               
            3. GENERATE SEAMLESS CONTINUATION:
               - Complete any partial words using contextual clues
               - Continue the sentence/paragraph naturally
               - Maintain the same tone, style, and vocabulary level
               - Stay on topic and don't introduce unrelated ideas
               - Avoid redundancy - don't repeat concepts already expressed
            
            QUALITY STANDARDS:
            • Contextually relevant and coherent
            • Grammatically correct when combined with input
            • Maintains consistent voice and style
            • Adds meaningful content without redundancy
            • Feels like the same person continued writing
            
            OUTPUT FORMAT:
            • Pure continuation text only
            • No explanations, labels, or meta-commentary
            • Start immediately with the next letters/words needed
            • NEVER begin with ellipsis (...), periods, or quotation marks
            • First character must be a letter or space, never punctuation
            """
        )

    def prepare_user_message(self, text: str, max_output_length: Optional[Dict[str, Union[str, int]]] = None) -> str:
        # Extract last few words for context
        words = text.strip().split() if text.strip() else []
        last_few_words = " ".join(words[-5:]) if words else ""
        
        message = (
            "Continue this text exactly where it stops. Your response will be directly appended.\n\n"
            "CRITICAL OUTPUT FORMAT:\n"
            "• Do NOT start with ellipsis (...) or periods\n"
            "• Do NOT add quotation marks or formatting\n"
            "• Start immediately with the continuation text\n"
            "• Your first character should be a letter or space (never punctuation)\n\n"
            "CONTINUATION TASK:\n"
            "1. If the text ends mid-word (like 'recurs'), complete it contextually\n"
            "2. Then continue the sentence/thought naturally\n"
            "3. Avoid repeating ideas already expressed\n"
            "4. Stay focused on the same topic and maintain coherence\n"
            "5. Match the writing style, tone, and vocabulary level\n\n"
            "CONTEXT ANALYSIS:\n"
            "• Understand the full meaning and direction of the text\n"
            "• Identify where this thought is naturally heading\n"
            "• Determine if the ending needs word completion first\n\n"
            "TEXT TO CONTINUE:\n"
            f"{text}\n\n"
            "Your continuation (start immediately, no ellipsis or periods):"
        )
        
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