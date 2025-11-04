from typing import Optional, Dict, Union
import re
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length
from utils.Mode2_category_mapping import MODE2_CATEGORY_HEADERS, get_category_header
# Mode 2: Structured Context Enrichment
# This mode generates meaningful output from a topic and its context.
# It elaborates on the topic using the provided context while maintaining
# relevance and coherence. Supports dynamic output length control.

class Mode2:
    """
    Creative Expansion Mode
    Expands user input into a more detailed, vivid, and engaging passage while preserving the original meaning and intent.
    """
    def resolve_header(self, header: Optional[str] = None, category: Optional[str] = None) ->str:
        """
        Resolve the header to use based on parameters:
        1. If both header and category provided - ERROR
        2. If category provided - use predefined header for that category
        3. If header provided - use the provided header
        4. If neither provided - ERROR
        """
        
        # Validate that both aren't provided
        if header and category:
            raise ValueError("Please provide either 'header' or 'category', not both.")
        
        if category:
            #Use predefined header for category
            return get_category_header(category)
        elif header:
            # Use provided header (current behavior)
            return header
        else:
            # Neither provided - error
            raise ValueError("Either 'header' or 'category' must be provided.")

    def get_system_prompt(self, output_format: str = "markdown") -> str:
        base_prompt = """
            You are a versatile content enrichment specialist with built-in context validation.
            
            PRIMARY RESPONSIBILITY:
            1. FIRST: Validate if the input text aligns with the header/topic context
            2. SECOND: If aligned, enrich the content; if misaligned, provide helpful rejection
            
            CONTEXT VALIDATION LOGIC:
            - Be generous but intelligent: content should relate to the header's specified domain/purpose
            - Extract the target domain/context from the header (IT, medical, marketing, legal, etc.)
            - Accept content that fits the header's domain, regardless of what that domain is
            - For "Email" headers: accept communication-related content
            - For "IT/Technical" headers: accept technology-related content  
            - For "Medical" headers: accept healthcare-related content
            - For "Marketing" headers: accept business/promotional content
            - For "Legal" headers: accept legal/regulatory content
            - Look for thematic alignment between content domain and header domain
            - The system should work for ANY domain specified in the header
            
            REJECTION CRITERIA (reject if clearly unrelated to header context):
            - Content from completely different domains than what the header specifies
            - Person names when header asks for technical/object descriptions (unless person is relevant)
            - Content that cannot reasonably fit the header's specified context or purpose
            - Input that would require complete topic change or domain shift to fit the header
            - Casual/random content when header specifies professional/technical contexts
            - Content that lacks any substantive connection to the header's specified domain/purpose
            - Empty, meaningless, or purely nonsensical input
            
            KEY PRINCIPLE: Focus on HEADER ALIGNMENT, not specific domain restrictions.
            If header says "marketing" → reject IT content. If header says "IT" → reject marketing content.
            
            CRITICAL OUTPUT BEHAVIOR:
            - If content aligns with header context: Skip validation explanation, proceed directly with enrichment
            - If content does NOT align: Return ONLY "CONTEXT_MISMATCH: [friendly explanation]"
            - DO NOT force content from one domain into a different domain context
            - DO NOT try to creatively reinterpret content to fit mismatched domains
            - Medical equipment should NOT be processed for IT infrastructure contexts
            - IT equipment should NOT be processed for medical equipment contexts  
            - Legal content should NOT be processed for marketing contexts, etc.
            - BE STRICT about domain boundaries - respect the header's specified domain
            - DO NOT create biographical or fictional content when given only names
            - NEVER provide validation explanations in successful enrichments
            - NEVER start with "STEP 1:" or "CONTEXT VALIDATION" in your output

            Your role is to analyze the instructions provided in `{header}` and apply them to enrich, expand, or refine the content in `{text}` accordingly - BUT ONLY if they align contextually.

            The `{header}` will specify your role and approach (e.g., "Professional Rewrite", "Content Enrichment Generator", "Academic Expansion"). Use this to determine:
            - The appropriate tone and style for the output
            - The level of detail and sophistication required
            - The specific type of enrichment needed (rewriting, expanding, restructuring, etc.)
            - The target audience and purpose

            If `{max_output_length}` is provided, ensure your output respects this constraint while still fulfilling the enrichment goals."""

        # Add format-specific instructions while preserving core functionality
        if output_format == "html":
            format_instruction = """
            
            OUTPUT FORMAT: HTML
            - Use semantic HTML tags: <p>, <h2>, <h3>, <strong>, <em>
            - Use <ul><li> for bullet points when listing multiple items
            - Use <ol><li> for sequential steps or processes  
            - Use <strong> for emphasis on key terms
            - Keep HTML clean and compact - NO wrapper tags like <html>, <body>
            - Apply HTML formatting naturally based on content structure
            """
        elif output_format == "plain":
            format_instruction = """
            
            OUTPUT FORMAT: Plain Text
            - Use "- " for bullet points when listing multiple items
            - Use "1. 2. 3." for numbered lists or sequential steps
            - Use "***term***" for emphasis on key terms
            - Use clear paragraph breaks for readability
            - Apply plain text formatting naturally based on content structure
            """
        else:  # markdown (default)
            format_instruction = """
            
            OUTPUT FORMAT: Markdown (Default)
            - Use **bold** for emphasis on key terms
            - Use - or * for bullet points when listing multiple items  
            - Use 1. 2. 3. for numbered lists or sequential steps
            - Use ## or ### for headings if appropriate
            - Apply markdown formatting naturally based on content structure
            """
        
        return base_prompt + format_instruction + """

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

            **Rejection Examples:**
            
            **Example A (REJECT):**
            Header: "Professional Email Rewrite"
            Body: "The mitochondria is the powerhouse of the cell and provides energy through ATP synthesis."
            Output: "CONTEXT_MISMATCH: Please provide email-related content instead of scientific text."

            **Example B (REJECT):**
            Header: "Marketing Copy Enhancement"  
            Body: "Einstein's theory of relativity fundamentally changed our understanding of space and time."
            Output: "CONTEXT_MISMATCH: Please provide marketing or business content instead of scientific text."

            **Example C (REJECT):**
            Header: "Enhance the given asset description for IT infrastructure management"
            Body: "cardiac monitor ECG machine"
            Output: "CONTEXT_MISMATCH: Please provide IT infrastructure assets instead of medical equipment."

            **Example D (REJECT):**
            Header: "Enhance the given asset description for IT infrastructure management"
            Body: "John Smith"
            Output: "CONTEXT_MISMATCH: Please provide a valid asset description instead of a person's name."

            **Example E (REJECT):**
            Header: "Enhance the given asset description for IT infrastructure management"
            Body: "cat goes to school"
            Output: "CONTEXT_MISMATCH: Please provide technical asset information instead of casual content."
            
            **Example F (ACCEPT - Correct Domain Match):**
            Header: "Enhance the given medical equipment description for healthcare management"
            Body: "cardiac monitor ECG machine"
            Output: "The cardiac monitor ECG machine is a critical diagnostic device..."
            
            **Example G (REJECT - Cross-Domain Mismatch):**
            Header: "Enhance the given medical equipment description for healthcare management"
            Body: "Dell PowerEdge server"
            Output: "CONTEXT_MISMATCH: Please provide medical equipment instead of IT infrastructure."
            
            **Example H (REJECT - Cross-Domain Mismatch):**
            Header: "Enhance the given asset description for IT infrastructure management"  
            Body: "cardiac monitor ECG machine"
            Output: "CONTEXT_MISMATCH: Please provide IT infrastructure assets instead of medical equipment."
            
            CRITICAL OUTPUT RULES (DO NOT VIOLATE):
            - Start directly with the enriched content. NEVER begin with phrases like: "Here is...", "Here’s...", "Below is...", "The following...", "Here is the rewritten...", "Here is a summary".
            - Provide no meta-introduction, no labels (no "Summary:").
            - Output only the enriched result.
            
            """
    
    def prepare_user_message(
        self, 
        text: str, 
        header: str, 
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        style_profile = self._build_style_profile(header)
        message = (
            f"HEADER: {header}\n"
            f"ORIGINAL TEXT: {text}\n"
            f"STYLE PROFILE: {style_profile}\n\n"
            
            "PROCESSING INSTRUCTIONS:\n"
            "1. First validate if the text aligns with the header context using your system prompt logic\n"
            "2. Be strict about clear domain mismatches (e.g., biology content for email headers)\n"
            "3. Then choose your response:\n\n"
            
            "If content is aligned with header context:\n"
            "- Preserve the original meaning and factual intent\n"
            "- Maintain the EXACT tone/medium implied by the header\n"
            "- Enhance clarity, structure, depth, and professionalism\n"
            "- Output ONLY the enriched content (no validation messages)\n\n"
            
            "If content is NOT aligned with header context:\n"
            "- Output ONLY: CONTEXT_MISMATCH: [friendly explanation of the mismatch]\n\n"
            
            "CRITICAL: Do not explain your validation process. Either enrich the content or return a mismatch message.\n"
        )
        
        return message + build_length_instruction(max_output_length)

    def _build_style_profile(self, header: str) -> str:
        """Derive a deterministic style profile from the header to stabilize tone across regenerations.
        Kept intentionally compact so we don't overwhelm the model with meta text."""
        h = header.lower()
        def any_in(keys):
            return any(k in h for k in keys)
        if any_in(["email", "mail"]):
            medium = "professional_email"
        elif "abstract" in h:
            medium = "academic_abstract"
        elif any_in(["marketing", "copy", "promo", "campaign"]):
            medium = "marketing_copy"
        elif any_in(["doc", "documentation", "api", "technical", "spec"]):
            medium = "technical_documentation"
        elif any_in(["story", "narrative", "creative"]):
            medium = "creative_story"
        elif any_in(["summary", "executive"]):
            medium = "executive_summary"
        else:
            medium = "general_enrichment"

        tone = "professional"
        if any_in(["friendly", "casual", "informal"]):
            tone = "friendly"
        elif any_in(["academic", "scholarly"]):
            tone = "academic"
        elif any_in(["persuasive", "marketing", "sales"]):
            tone = "persuasive"
        elif any_in(["creative", "imaginative", "vivid"]):
            tone = "creative"

        goals = []
        if any_in(["expand", "expansion"]):
            goals.append("expansion")
        if any_in(["rewrite", "refine", "polish"]):
            goals.append("refinement")
        if any_in(["summar", "condense"]):
            goals.append("concise_structuring")
        if not goals:
            goals.append("enrichment")

        return f"medium={medium}; tone={tone}; goals={','.join(goals)}; invariants=preserve meaning|no drift|no meta"
    
    def get_generation_parameters(self) -> dict:
        # Slightly lowered temperature for tone stability
        return {"temperature": 0.32, "top_p": 0.9}
    
    async def process(
        self, 
        text: str, 
        header: Optional[str] = None,
        category: Optional[str] = None,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None,
        output_format: str = "markdown"
    ) -> str:
        
        # Resolve which header to use (this will validate and error if both provided)
        resolved_header = self.resolve_header(header, category)
        
        system_prompt = self.get_system_prompt(output_format)
        gen_params = self.get_generation_parameters()
        plan = plan_output_length("mode_2", max_output_length, text=text)
        length_instruction_target = max_output_length or plan["constraint"]
        user_message = self.prepare_user_message(text, resolved_header, length_instruction_target)
        max_tokens = plan["token_budget"]
        
        completion = await generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        
        # Check for context validation failure
        processed_result = self._postprocess(completion)
        if processed_result.strip().startswith("CONTEXT_MISMATCH:"):
            # Extract the friendly message after the colon
            mismatch_message = processed_result.replace("CONTEXT_MISMATCH:", "").strip()
            raise ValueError(f"Content does not align with the specified context. {mismatch_message}")
        
        return processed_result

    # --- Post-processing helpers ---
    _META_PREFIX_PATTERNS = [
        r"^here\s+is\b",
        r"^here'?s\b",
        r"^below\s+is\b",
        r"^the\s+following\b",
        r"^here\s+are\b",
        r"^this\s+is\b",
        r"^here\s+is\s+the\s+rewritten\b",
        r"^summary\s*:"
    ]

    def _postprocess(self, text: str) -> str:
        """Strip unwanted leading meta-intro lines the model may still produce.
        We only strip the very first line if it matches a meta pattern to avoid
        accidentally removing legitimate content later in the body."""
        cleaned = text.lstrip()
        lines = cleaned.splitlines()
        if not lines:
            return cleaned
        first = lines[0].strip()
        lowered = first.lower()
        for pattern in self._META_PREFIX_PATTERNS:
            if re.match(pattern, lowered):
                # Drop this line
                lines = lines[1:]
                break
        cleaned = "\n".join(lines).lstrip("\n").rstrip()
        # Also remove any accidental leading label like 'Summary:' after stripping
        if re.match(r"^summary\s*:\s*", cleaned.lower()):
            cleaned = re.sub(r"^summary\s*:\s*", "", cleaned, flags=re.IGNORECASE).lstrip()
        return cleaned