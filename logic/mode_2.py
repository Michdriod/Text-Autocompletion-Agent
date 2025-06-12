# Mode 2: Structured Context Enrichment
# This mode generates meaningful output from a topic and its context.
# It elaborates on the topic using the provided context while maintaining
# relevance and coherence. Supports dynamic output length control.

from typing import Optional, Dict, Union
from utils.generator import GroqGenerator
from utils.validator import calculate_max_tokens

class Mode2Logic:
    def __init__(self):
        # Initialize the Groq LLM generator for text enrichment
        self.generator = GroqGenerator()
    
    def get_system_prompt(self) -> str:
        return (
            """
            You are a versatile content enrichment specialist. Your role is to analyze the instructions provided in `{header}` and apply them to enrich, expand, or refine the content in `{text}` accordingly.

            The `{header}` will specify your role and approach (e.g., "Professional Rewrite", "Content Enrichment Generator", "Academic Expansion"). Use this to determine:
            - The appropriate tone and style for the output
            - The level of detail and sophistication required
            - The specific type of enrichment needed (rewriting, expanding, restructuring, etc.)
            - The target audience and purpose

            If `{max_output_length}` is provided, ensure your output respects this constraint while still fulfilling the enrichment goals.

            Here are examples of how to handle different header instructions:

            **Example 1:**
            Header: "Professional Email Rewrite"
            Body: "hey can you send me the report? need it asap"
            Output: "Dear [Recipient], I hope this message finds you well. I would greatly appreciate if you could send me the report at your earliest convenience. The information is needed for an upcoming deadline, so any expedited assistance would be most helpful. Thank you for your time and consideration. Best regards, [Your name]"

            **Example 2:**
            Header: "Technical Documentation Enrichment"
            Body: "API returns user data"
            Output: "The API endpoint retrieves comprehensive user data from the database, including profile information, account settings, and activity history. The response is formatted as a JSON object containing structured user attributes such as user ID, email address, display name, registration date, and last login timestamp. This data can be used for user management, personalization features, and analytics purposes."

            **Example 3:**
            Header: "Creative Story Expansion"
            Body: "The old house creaked in the wind."
            Output: "The old Victorian house groaned and creaked against the relentless autumn wind, its weathered shutters rattling like skeletal fingers against the peeling paint. Each gust seemed to awaken the structure's ancient bones, filling the air with haunting melodies that spoke of decades of forgotten stories and whispered secrets trapped within its walls."

            **Example 4:**
            Header: "Marketing Copy Enhancement"
            Body: "Our product is good and affordable"
            Output: "Discover exceptional value with our premium product line—expertly crafted to deliver outstanding performance while remaining accessible to budget-conscious consumers. Experience the perfect balance of quality and affordability that sets us apart from the competition."

            **Example 5:**
            Header: "Academic Abstract Expansion"
            Body: "Study shows link between sleep and memory"
            Output: "This comprehensive research investigation examines the intricate relationship between sleep patterns and memory consolidation processes in human subjects. Through controlled experimental design and longitudinal data collection, the study demonstrates significant correlations between sleep duration, sleep quality, and various memory formation mechanisms, including both short-term and long-term retention capabilities."
            
            """
                        
            
            # "You are a structured content generator. Your task is to create meaningful, "
            # "engaging content based on the provided topic and context. Focus on elaborating "
            # "the topic using the context as a foundation. Maintain relevance and coherence "
            # "while adding value through thoughtful expansion. Keep your output clear, "
            # "well-structured, and focused on the topic."
        )
    
    def prepare_user_message(
        self, 
        text: str, 
        header: str, 
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        message = (
            "Based on the role specified in the header, please enrich the text:"
            f"Topic: {header}\n\n"
            f"Context: {text}\n\n"
            "Generate a meaningful elaboration of this topic using the provided context. "
            "Focus on creating engaging, relevant content that expands on the topic while "
            "maintaining coherence with the context. "
            "Apply the specified enrichment approach while maintaining clarity and relevance."
                        
            # f"Topic: {header}\n\n"
            # f"Context: {text}\n\n"
            # "Generate a meaningful elaboration of this topic using the provided context. "
            # "Focus on creating engaging, relevant content that expands on the topic while "
            # "maintaining coherence with the context."
        )
        
        if max_output_length:
            length_type = max_output_length.get("type", "characters")
            length_value = max_output_length.get("value", 200)
            message += f"\n\nIMPORTANT: Keep your elaboration to a maximum of {length_value} {length_type}."
        
        return message
    
    def get_generation_parameters(self) -> dict:
        # Use moderate temperature for balanced creativity and coherence
        return {"temperature": 0.4, "top_p": 0.9}
    
    async def process(
        self, 
        text: str, 
        header: str, 
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        system_prompt = self.get_system_prompt()
        user_message = self.prepare_user_message(text, header, max_output_length)
        gen_params = self.get_generation_parameters()
        
        # Calculate max tokens based on output length requirements
        max_tokens = calculate_max_tokens(max_output_length)
        
        completion = await self.generator.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        
        return completion