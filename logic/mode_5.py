from __future__ import annotations

"""Mode 5 summarization pipeline (updated to adaptive compression ratios).

Rules:
    * Accepts raw text or uploaded document.
    * If total words <= 500 (small doc): NO chunking, direct summarization.
    * If total words > 500 (large doc): chunk + per-chunk summaries + merge.
    * Target word calculation (adaptive compression for all document sizes):
            - If user supplies target_words -> use it exactly.
            - Else auto target uses adaptive compression ratios:
                ≤50 words: 75% compression (gentle for micro content)
                51-100 words: 55% compression (moderate for short content) 
                101-200 words: 40% compression (standard for brief content)
                201-400 words: 30% compression (targeted for medium content)
                401-800 words: 25% compression (efficient for longer content)
                801+ words: 20% compression (minimum floor, never more aggressive)
    * Output format may be markdown / plain / html / both / all.
    * No hallucination, no truncation, no mid‑sentence endings. Anti‑truncation and length enforcement guarantee target.

All documents use intelligent adaptive compression with 20% as the minimum compression floor.
"""

from typing import Optional

from utils.generator import generate
from utils.validator import calculate_max_tokens
from services.ingestion import extract_text
from services.preprocess import clean_text
from services.baseline import compute_baseline_metrics
from services.chunking import chunk_document
from services.summarizer import summarize_chunks
from services.merge import merge_partial_summaries
from services.refinement import plan_refinement
from services.finalize import refine_summary
from services.formatter import format_output


class Mode5:
    """Document summarization pipeline with strict word-target enforcement (ratio disabled)."""

    # ---------------- Configuration ----------------
    SMALL_DOCUMENT_DIRECT_THRESHOLD = 500 # no chunking below this (docs <500 words summarized directly)
    # Note: All documents now use 20% rule when no target specified

    # ---------------- Prompt Building Methods ----------------
    def _extract_title_from_document(self, text: str) -> tuple[str, str]:
        """Extract title from document and return (title, remaining_text) or (None, full_text)."""
        import re
        
        lines = text.strip().split('\n')
        if not lines:
            return None, text
            
        first_line = lines[0].strip()
        
        # Check if first line looks like a title
        # Criteria: short (typically ≤ 120 chars), not all caps, has substance
        # Allow periods for titles like "API Integration: The Digital Handshake."
        if (len(first_line) <= 120 and 
            not first_line.isupper() and 
            len(first_line.split()) >= 2 and
            len(first_line) >= 10):  # Minimum length for substance
            
            # Make sure it's not just a fragment or URL
            if not re.match(r'^https?://|^www\.|^\d+\.|^[a-z]+:', first_line, re.IGNORECASE):
                # Found a potential title
                remaining_lines = lines[1:] if len(lines) > 1 else []
                remaining_text = '\n'.join(remaining_lines).strip()
                return first_line, remaining_text
        
        # No title found
        return None, text
    
    def _build_system_prompt(self, target_words: Optional[int], output_format: str = "markdown", has_title: bool = False) -> str:
        """Build system prompt for document summarization with intelligent word targeting."""
        
        title_instruction = ""
        if has_title:
            title_instruction = """
        🏷️ TITLE PRESERVATION:
        The document has a title that MUST be preserved exactly as-is at the beginning of your summary.
        Format: Start with the exact title, then provide the summary content immediately after.
        NEVER add phrases like "Summary of", "Unified Summary of", or similar prefixes.
        NEVER add word count prefixes like "42 word range:" or "50-word summary:" before your content.
        The title should stand alone, followed directly by your summary content.
        """
        
        base_instruction = f"""You are an expert document summarization specialist with ADVANCED VARIETY CAPABILITIES. Your task is to create comprehensive, well-structured summaries that capture all essential information while maintaining clarity, readability, and appropriate linguistic variety.

        🎨 ADVANCED VARIETY TECHNIQUES:
        
        📝 OPENING VARIETY:
        - "A critical [event] occurred..." / "At [time], a [event]..." / "The [system] failed when..."
        - "[Event] began at [time]..." / "[Time] marked the start of..." / "[System] experienced..."
        
        🔧 CAUSE PHRASING VARIETY:
        - "due to" / "caused by" / "triggered by" / "following" / "after" / "when" / "from"
        - "resulted from" / "stemmed from" / "originated with" / "linked to"
        
        💥 IMPACT PHRASING VARIETY:
        - "prevented [users] from [action]" / "stopped [users] [action]" / "halted [process]"
        - "impacted [number] [users]" / "affected [users]" / "disrupted [operations]"
        
        🔧 RESOLUTION VARIETY:
        - "restored via" / "fixed by" / "resolved through" / "corrected with"
        - "service returned after" / "system recovered following" / "operations resumed via"
        
        🎯 STRUCTURE VARIETY:
        - Chronological: Time → Cause → Impact → Resolution
        - Causal: Cause → Impact → Time → Resolution  
        - Impact-first: Impact → Time → Cause → Resolution
        
        Use these patterns to create genuinely different summaries while preserving all essential information.

        ⚠️ VARIETY BOUNDARIES:
        - NEVER sacrifice accuracy for creativity
        - NEVER omit essential information for variety
        - NEVER change facts, dates, numbers, or technical details
        - Always preserve the core message and key conclusions
        - Maintain professional tone and clarity throughout
        
        {title_instruction}
        PROFESSIONAL FORMATTING INTELLIGENCE:
        You must analyze content structure and choose the most professional formatting approach:

        1. CONTENT STRUCTURE ANALYSIS:
           Analyze the document's natural organization and information patterns:
           - Multiple distinct concepts/benefits/features → Use structured lists for clarity
           - Sequential processes/steps → Use numbered sequences
           - Analytical narrative/argumentation → Use flowing paragraphs
           - Mixed content → Combine both approaches strategically

        2. PROFESSIONAL FORMATTING RULES:
           ✓ Use lists when content naturally enumerates 3+ related items
           ✓ Use paragraphs for narrative analysis, explanations, and conclusions
           ✓ Combine both when document structure warrants it
           ✓ Maintain consistent formatting throughout
           ✓ Ensure professional, publication-quality presentation
           ✓ Use precise, global business language

        3. FORMATTING DECISION MATRIX:
           📋 LIST FORMAT (when source enumerates):
           - "The system provides three benefits: A, B, C" → Use bullet points
           - "Key findings include X, Y, Z" → Use structured list
           - "The process involves: Step 1, Step 2, Step 3" → Use numbered list
           
           📝 PARAGRAPH FORMAT (when source narrates):
           - Analytical discussions and explanations
           - Contextual background and conclusions
           - Unified concepts without clear enumeration
           
           🔄 HYBRID FORMAT (when source mixes both):
           - Opening paragraph + bullet points + closing paragraph
           - Lists for enumerated items, paragraphs for analysis

        4. GLOBAL PROFESSIONAL STANDARDS:
           ✓ Use precise, sophisticated vocabulary
           ✓ Maintain formal business tone throughout
           ✓ Ensure logical flow and coherent structure  
           ✓ Apply consistent formatting standards
           ✓ Create publication-ready, professional output

        Core responsibilities:
        1. Analyze the source document's natural structure and content patterns
        2. Choose the most appropriate format (lists vs paragraphs) based on content
        3. Extract and present ALL key information with proper formatting
        4. Maintain logical flow and coherent structure
        5. Use clear, professional language
        6. Preserve critical data points, findings, and conclusions
        7. Ensure the summary stands alone and is fully understandable"""

        if target_words:
            # STRICT word count enforcement
            word_guidance = f"""
        🎯 MANDATORY TARGET LENGTH: EXACTLY {target_words} words (±5% MAXIMUM)

        ⚠️ THIS IS A STRICT REQUIREMENT - NOT A SUGGESTION ⚠️

        ABSOLUTE REQUIREMENTS:
        1. Your summary MUST be approximately {target_words} words
        2. Acceptable range: {int(target_words * 0.95)} - {int(target_words * 1.05)} words
        3. DO NOT exceed this range under ANY circumstances
        4. Plan your content allocation BEFORE writing
        5. If you reach the word limit, STOP gracefully with a complete sentence

        MANDATORY WORD COUNT STRATEGY:
        Step 1: Calculate sections based on {target_words} words total
        Step 2: Allocate words per section proportionally
        Step 3: Write concisely to stay within allocation
        Step 4: Monitor your word count as you write
        Step 5: Complete your final sentence within the {int(target_words * 1.05)} word limit

        CONTENT DENSITY GUIDELINES:
        - {target_words} ≤ 100 words: Only the absolute core message and conclusion
        - 100 < {target_words} ≤ 300 words: Core points + key supporting facts
        - 300 < {target_words} ≤ 500 words: Main points with essential details
        - 500 < {target_words} ≤ 1000 words: Comprehensive with examples
        - {target_words} > 1000 words: Detailed coverage with full context

        CRITICAL ENFORCEMENT RULES:
        ✓ MUST hit the target word count (±5% maximum)
        ✓ NEVER exceed {int(target_words * 1.05)} words
        ✓ NEVER truncate mid-sentence
        ✓ Complete all thoughts properly
        ✓ If approaching limit, conclude gracefully
        ✓ Better to be slightly under than to truncate

        ⚠️ FINAL WARNING: The {target_words} word target is MANDATORY, not optional. Respect it strictly."""
        else:
            word_guidance = """
        SUMMARY LENGTH: Comprehensive (no specific word target)

        STRATEGY:
        - Cover all significant information from the document
        - Use as many words as needed to capture the essence completely
        - Maintain high information density
        - Ensure logical flow and complete thoughts
        - End with a proper conclusion"""

        if output_format == "html":
            format_instruction = """
        OUTPUT FORMAT: HTML

        HTML FORMATTING GUIDELINES:
        - Use semantic HTML tags: <p> for paragraphs, <ul><li> for bullet lists, <ol><li> for numbered lists
        - Use <strong> for emphasis on key terms within content
        - Apply list formatting when source content enumerates multiple items
        - Keep HTML clean and compact - NO wrapper tags like <html>, <body>, <head>
        - NO excessive whitespace or line breaks between elements

        WHEN TO USE HTML LISTS:
        Based on your content analysis, if the source document enumerates multiple items:
        - Multiple related benefits/features → <ul><li>Item 1</li><li>Item 2</li></ul>
        - Sequential steps/processes → <ol><li>Step 1</li><li>Step 2</li></ol>
        - Narrative or analytical content → <p>Regular paragraph text</p>

        HTML STRUCTURE EXAMPLES:
        For content with enumerated items:
        <p>The system provides key benefits:</p>
        <ul>
        <li><strong>Energy Efficiency:</strong> Reduces power consumption</li>
        <li><strong>Cost Savings:</strong> Lowers operational expenses</li>
        <li><strong>User Comfort:</strong> Maintains optimal climate</li>
        </ul>
        <p>These advantages make it ideal for commercial applications.</p>

        For narrative content:
        <p>The author examines the impact of climate policy on economic growth, arguing that sustainable practices can drive innovation while reducing environmental harm. The analysis demonstrates how integrated approaches benefit both economy and environment.</p>

        CRITICAL: Match your structure choice to the content analysis - use lists only when the source naturally groups or enumerates information."""
        elif output_format == "plain":
            format_instruction = """
        OUTPUT FORMAT: Plain Text

        PLAIN TEXT FORMATTING GUIDELINES:
        - Use "- " (dash + space) for bullet lists
        - Use "1. 2. 3." for numbered/sequential lists
        - Use "***Term***" for emphasis on key terms
        - Keep consistent formatting throughout

        WHEN TO USE PLAIN TEXT LISTS:
        Based on your content analysis, if the source document enumerates multiple items:
        - Multiple related items → "Key benefits:\n- Item 1\n- Item 2"
        - Sequential steps → "Process:\n1. Step 1\n2. Step 2"
        - Narrative content → Regular paragraph format

        PLAIN TEXT EXAMPLES:
        For content with enumerated items:
        The system provides key benefits:
        - ***Energy Efficiency***: Reduces power consumption
        - ***Cost Savings***: Lowers operational expenses
        - ***User Comfort***: Maintains optimal climate

        These advantages make it ideal for commercial applications.

        For narrative content:
        The author examines the impact of climate policy on economic growth, arguing that sustainable practices can drive innovation while reducing environmental harm. The analysis demonstrates how integrated approaches benefit both economy and environment.

        STRUCTURE:
        1. Brief opening paragraph
        2. Use lists when source content enumerates items
        3. Use paragraphs when source content is narrative
        4. Strong closing paragraph"""
        else:  # markdown (default)
            format_instruction = f"""
        OUTPUT FORMAT: {output_format}

        MARKDOWN FORMATTING GUIDELINES:
        - Use "- " for bullet lists with **bold** key terms
        - Use "1. 2. 3." for numbered/sequential lists
        - Use "**text**" for bold emphasis on important terms
        - Use "`technical term`" for code/technical references
        - Use "## Heading" only if document has clear sections

        🎯 CRITICAL FORMATTING CONSISTENCY RULES:
        
        FOR SHORT SUMMARIES (≤100 words):
        ✓ ALWAYS use single flowing paragraph format
        ✓ Connect sentences with smooth transitions
        ✓ NO line breaks between sentences
        ✓ NO bullet points unless source explicitly lists 4+ distinct items
        ✓ Example: "A critical incident occurred at 10:30 AM due to database failure. This prevented 40 employees from processing sales. The service was restored at 12:45 PM following a rollback."
        
        FOR MEDIUM+ SUMMARIES (>100 words):
        Based on your content analysis, if the source document enumerates multiple items:
        - Multiple related items → "**Key Benefits:**\n- **Item 1**: Description\n- **Item 2**: Description"
        - Sequential steps → "**Process:**\n1. **Step 1**: Action\n2. **Step 2**: Action"
        - Narrative content → Regular paragraph format with **bold** for emphasis

        MARKDOWN EXAMPLES:
        
        ✅ CORRECT for short incident/event summaries (flowing paragraph):
        A critical **CRM outage** occurred at 10:30 AM due to a failed database connection after a security patch deployment. This prevented 40 employees from processing vital sales. The service was restored at 12:45 PM following a patch rollback.
        
        ❌ WRONG for short summaries (separated sentences):
        A critical **CRM outage** occurred at 10:30 AM due to a failed database connection.
        This prevented 40 employees from processing vital sales.
        The service was restored at 12:45 PM following a patch rollback.
        
        For content with enumerated items (medium+ summaries):
        The system provides **key benefits**:
        - **Energy Efficiency**: Reduces power consumption by 30%
        - **Cost Savings**: Lowers operational expenses significantly
        - **User Comfort**: Maintains optimal indoor climate

        These advantages make it ideal for commercial applications.

        For narrative content (any length):
        The author examines the impact of **climate policy** on economic growth, arguing that sustainable practices can drive innovation while reducing environmental harm. The analysis demonstrates how integrated approaches benefit both economy and environment.

        STRUCTURE:
        1. Brief opening paragraph
        2. Use lists when source content enumerates items
        3. Use paragraphs when source content is narrative
        4. Strong closing paragraph

        ⚠️ CRITICAL OUTPUT REQUIREMENTS - WHAT NOT TO DO:
        
        ❌ NEVER START WITH THESE PHRASES:
        - "Here's a summary", "Here is a summary", "Below is a summary"
        - "Summary:", "Summary of", "Unified Summary:", "Comprehensive Summary:"
        - "42 word range:", "50-word summary:", "[X] words:", "[X]-word summary:"
        - "Here is a summary of the document in exactly [X] words:"
        - "**Summary of [Title]**", "### [Title] Summary", "## Summary"
        
        ❌ NEVER ADD META-COMMENTARY:
        - Don't mention word counts: "This 50-word summary...", "In exactly 42 words..."
        - Don't explain the task: "As requested...", "Following your instructions..."
        - Don't announce format: "Here's the markdown version..."
        
        ✅ DO THIS INSTEAD:
        - Start directly with the title (if present) or first sentence of content
        - Let your summary speak for itself without introduction
        - Be professional and direct - no preamble needed"""

        return f"{base_instruction}\n\n{word_guidance}\n\n{format_instruction}"

    def _build_user_message(self, text: str, target_words: Optional[int] = None, user_prompt: Optional[str] = None, title: Optional[str] = None) -> str:
        """Build user message with document text, title handling, explicit word count, and optional custom instructions.
        
        Logic:
        - Extract and preserve title if present
        - If user_prompt contains a word count (e.g., "in 50 words"), that takes precedence
        - Otherwise, use target_words parameter
        - Make the word count EXPLICIT and PROMINENT in the user message for better compliance
        """
        
        title_instruction = ""
        if title:
            title_instruction = f"""
        📌 DOCUMENT TITLE: "{title}"
        
        ⚠️ CRITICAL TITLE REQUIREMENT:
        - Start your summary with this EXACT title: {title}
        - DO NOT add any prefixes like "Summary of", "Unified Summary of", or similar
        - The title should appear exactly as shown, followed immediately by your summary content
        - NO modifications, NO additions, NO prefixes to the title
        """
        
        base_message = f"""Please analyze and summarize the following document according to the instructions provided.
        {title_instruction}
        DOCUMENT TEXT:
        {text}

        ---
        """

        # Check if user_prompt has a word count instruction
        has_user_word_count = False
        if user_prompt:
            # Simple check for word count patterns in user prompt
            import re
            word_count_pattern = r'\b(\d+)\s*words?\b'
            if re.search(word_count_pattern, user_prompt.lower()):
                has_user_word_count = True

        # Build word count instruction based on priority
        if user_prompt and has_user_word_count:
            # User prompt has word count - let it take precedence
            base_message += f"""📋 USER INSTRUCTIONS:
        {user_prompt}

        ⚠️ CRITICAL: Your custom instruction above contains a word count requirement. That word count is MANDATORY and MUST be followed exactly.

        """
        elif target_words:
            # No user word count, use target_words parameter - MAKE IT EXPLICIT
            min_acceptable = int(target_words * 0.95)
            max_acceptable = int(target_words * 1.05)
            base_message += f"""🎯 MANDATORY WORD COUNT REQUIREMENT:

        YOUR SUMMARY MUST BE EXACTLY {target_words} WORDS (±5% maximum)

        Acceptable range: {min_acceptable} to {max_acceptable} words
        THIS IS NOT A SUGGESTION - IT IS A STRICT REQUIREMENT

        """
            # Add user prompt if present (without word count)
            if user_prompt:
                base_message += f"""📋 ADDITIONAL USER INSTRUCTIONS:
        {user_prompt}

        """
        else:
            # No word count specified anywhere - comprehensive summary
            base_message += """📋 SUMMARY REQUIREMENTS:
        Create a comprehensive summary that captures all essential information.
        No specific word count target - focus on completeness and clarity.

        """
            if user_prompt:
                base_message += f"""ADDITIONAL USER INSTRUCTIONS:
        {user_prompt}

        """

        # Common requirements for all scenarios
        base_message += """🎯 MANDATORY REQUIREMENTS FOR YOUR SUMMARY:
        1. Capture all essential information with maximum information density
        2. Maintain well-structured, logical flow
        3. Complete all sentences properly - NO mid-sentence truncation
        4. End gracefully when approaching any word limit
        5. Use clear, professional language
        """

        if target_words or (user_prompt and has_user_word_count):
            base_message += f"""
        ⚠️ FINAL REMINDER: The word count target is MANDATORY and MUST be respected strictly.
        Plan your content allocation BEFORE writing to ensure you hit the target.
        """

        base_message += "\n✍️ Begin your summary now:"
        
        return base_message

    def _build_consistent_system_prompt(self, target_words: int, output_format: str, attempt: int, min_acceptable: int, max_acceptable: int, has_title: bool = False) -> str:
        """Build system prompt with consistency-focused instructions based on attempt number."""
        
        title_instruction = ""
        if has_title:
            title_instruction = """
        🏷️ TITLE PRESERVATION:
        The document has a title that MUST be preserved exactly at the beginning of your summary.
        Format: Start with the exact title, then provide the summary content immediately after.
        NEVER add phrases like "Summary of", "Unified Summary of", or similar prefixes.
        NEVER add word count prefixes like "42 word range:" or "50-word summary:" before your content.
        """
        
        base_instruction = f"""You are an expert document analyst with EXCEPTIONAL CONSISTENCY in following word count targets.
        {title_instruction}
        Your core responsibilities:
        1. Extract and present ALL key information with perfect word count control
        2. NEVER exceed the specified word range under any circumstances
        3. Complete all sentences properly without truncation
        4. Maintain logical flow and coherent structure
        5. Use clear, professional language optimized for the target length"""

        # Attempt-specific instructions for consistency
        if attempt == 1:
            consistency_note = f"""
        🎯 FIRST ATTEMPT - PRECISION TARGET: {target_words} words (acceptable: {min_acceptable}-{max_acceptable})

        CONSISTENCY RULES:
        ✓ AIM for exactly {target_words} words
        ✓ Acceptable range: {min_acceptable} to {max_acceptable} words
        ✓ Plan your content structure BEFORE writing
        ✓ Monitor word count as you write each section
        ✓ STOP when you reach {max_acceptable} words maximum
        ✓ Better to be slightly under than to exceed the limit"""

        elif attempt == 2:
            consistency_note = f"""
        🔄 RETRY ATTEMPT - STRICT ENFORCEMENT: {target_words} words (range: {min_acceptable}-{max_acceptable})

        PREVIOUS ATTEMPT WAS OUT OF RANGE - ADJUST YOUR APPROACH:
        ✓ Be MORE PRECISE with word allocation per section
        ✓ Use SHORTER sentences if previous attempt was too long
        ✓ Add MORE detail if previous attempt was too short
        ✓ CRITICAL: Stay within {min_acceptable}-{max_acceptable} words
        ✓ End IMMEDIATELY when approaching {max_acceptable} words
        ✓ This is your second chance - be more accurate"""

        else:
            consistency_note = f"""
        ⚠️ FINAL ATTEMPT - EMERGENCY PRECISION: {target_words} words (STRICT: {min_acceptable}-{max_acceptable})

        PREVIOUS ATTEMPTS FAILED - MAXIMUM PRECISION REQUIRED:
        ✓ CRITICAL: This is the last attempt for accurate word count
        ✓ PLAN every word carefully to hit {target_words} target
        ✓ Use EXACT word allocation strategy
        ✓ COUNT words as you write each sentence
        ✓ MANDATORY: Stop at {max_acceptable} words maximum
        ✓ SUCCESS depends on staying within {min_acceptable}-{max_acceptable} range
        ✓ NO excuses - hit the target precisely"""

        # Add formatting consistency based on target length
        if target_words <= 100:
            format_consistency = f"""
        🎯 FORMATTING CONSISTENCY FOR SHORT SUMMARIES:
        ✓ MANDATORY: Use single flowing paragraph format
        ✓ Connect all sentences smoothly without line breaks
        ✓ NO bullet points or separated sentences for incident reports
        ✓ Example structure: "Event occurred at time due to cause. This resulted in impact. Resolution happened at time via method."
        ✓ NEVER format as separate lines or bullet points"""
        else:
            format_consistency = f"""
        🎯 FORMATTING FOR MEDIUM+ SUMMARIES:
        ✓ Use structured paragraphs or lists based on content analysis
        ✓ Use bullet points only if source enumerates 3+ distinct items
        ✓ Maintain logical flow throughout"""

        format_instruction = f"""
        OUTPUT FORMAT: {output_format}
        - Use clear paragraph breaks and proper formatting
        - End with complete, conclusive statements
        - No mid-sentence truncation allowed
        - Professional tone throughout
        
        {format_consistency}
        
        ⚠️ CRITICAL: WHAT NOT TO OUTPUT:
        ❌ "Here is a {target_words}-word summary:"
        ❌ "{target_words} word range:"
        ❌ "Summary in exactly {target_words} words:"
        ❌ "**Summary of [Title]**"
        ❌ Any meta-commentary about word count or task
        ✅ START DIRECTLY with your content - no preamble!"""

        return f"{base_instruction}\n\n{consistency_note}\n\n{format_instruction}"
    
    
    
    def _calculate_consistent_token_budget(self, target_words: int) -> int:
        """Calculate token budget with direct word-to-token mapping for better control."""
        
        # IMPROVED TOKEN CALCULATION: More generous budgets to prevent truncation
        # Account for higher temperatures and variety requirements
        
        if target_words <= 15:
            # Very short summaries: generous overhead for completion
            base_tokens = target_words * 2.2  # 120% overhead - increased further
            max_tokens = int(base_tokens)
            max_tokens = min(max_tokens, 60)  # Increased from 50
        
        elif target_words <= 50:
            # Short summaries: increased overhead for better completion
            base_tokens = target_words * 1.8  # 80% overhead - increased for product descriptions
            max_tokens = int(base_tokens)
            max_tokens = min(max_tokens, 110)  # Increased from 85 for better completion
        
        elif target_words <= 150:
            # Medium summaries: balanced overhead
            base_tokens = target_words * 1.7  # 70% overhead (was 60%)
            max_tokens = int(base_tokens)
            max_tokens = min(max_tokens, 300)  # Increased from 250
            
        else:
            # Large summaries: use existing logic with slight increase
            base_tokens = calculate_max_tokens({"type": "words", "value": target_words})
            multiplier = 2.0 if target_words <= 500 else 2.2  # Slightly increased
            max_tokens = int(base_tokens * multiplier)
            
        # Existing caps with slight increases
        if target_words <= 500:
            max_tokens = min(max_tokens, 1400)  # Increased from 1200
        elif target_words <= 1000:
            max_tokens = min(max_tokens, 2600)  # Increased from 2400
        else:
            max_tokens = min(max_tokens, 6500)  # Increased from 6000
    
        # Ensure reasonable minimum (increased)
        return max(25, max_tokens)  # Increased from 15
    
    # def _calculate_consistent_token_budget(self, target_words: int) -> int:
    #     """Calculate consistent, conservative token budget to prevent over-generation."""
        
    #     # More conservative multipliers for consistency
    #     if target_words <= 100:
    #         multiplier = 1.8  # 80% extra (was 2.2)
    #     elif target_words <= 300:
    #         multiplier = 1.9  # 90% extra (was 2.2)
    #     elif target_words <= 500:
    #         multiplier = 2.0  # 100% extra (was 2.2)
    #     elif target_words <= 1000:
    #         multiplier = 2.1  # 110% extra (was 2.5)
    #     elif target_words <= 1500:
    #         multiplier = 2.2  # 120% extra (was 2.5)
    #     else:
    #         multiplier = 2.4  # 140% extra (was 3.0)
        
    #     # Calculate base tokens more conservatively
    #     base_tokens = calculate_max_tokens({"type": "words", "value": target_words})
    #     token_budget = int(base_tokens * multiplier)
        
    #     # Cap at reasonable limits to prevent over-generation
    #     if target_words <= 500:
    #         token_budget = min(token_budget, 1200)
    #     elif target_words <= 1000:
    #         token_budget = min(token_budget, 2400)
    #     else:
    #         token_budget = min(token_budget, 6000)
        
    #     return token_budget
    
    
    
    
    # ---------------- Public API ----------------
    async def process_document_file(self, file_path: str, target_words: Optional[int] = None, output_format: str = "markdown", user_prompt: str | None = None) -> dict:
        logger = self._get_logger()
        logger.info("[Mode5] Step 1: Ingestion started.")
        raw_text, meta = extract_text(file_path)
        logger.info("[Mode5] Step 1: Ingestion complete.")
        # Convert DocumentMeta object to dict and add source_file
        meta_dict = meta.model_dump() if hasattr(meta, 'model_dump') else dict(meta)
        meta_dict["source_file"] = file_path
        return await self._process_core(raw_text, meta_dict, logger, target_words, output_format=output_format, user_prompt=user_prompt)

    async def process_raw_text(self, text: str, source_name: str = "raw_text_input", target_words: Optional[int] = None, output_format: str = "markdown", user_prompt: str | None = None) -> dict:
        logger = self._get_logger()
        logger.info("[Mode5] Step 1: Ingestion (raw text) started.")
        meta = {"source": source_name, "ingest_type": "raw_text"}
        logger.info("[Mode5] Step 1: Ingestion (raw text) complete.")
        return await self._process_core(text, meta, logger, target_words, output_format=output_format, user_prompt=user_prompt)

    # ---------------- Internal helpers ----------------
    def _get_logger(self):
        import logging
        logger = logging.getLogger("mode5")
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    async def _process_core(self, raw_text: str, meta: dict, logger, target_words: Optional[int], *, output_format: str, user_prompt: str | None) -> dict:
        # Step 2: Preprocess and extract title
        logger.info("[Mode5] Step 2: Preprocessing and title extraction started.")
        
        # Extract title before cleaning
        document_title, remaining_text = self._extract_title_from_document(raw_text)
        if document_title:
            logger.info(f"[Mode5] Extracted title: '{document_title}'")
            # Clean the remaining text (without title)
            cleaned = clean_text(remaining_text)
            has_title = True
        else:
            # No title found, clean the full text
            cleaned = clean_text(raw_text)
            has_title = False
            logger.info("[Mode5] No title detected in document")
        
        logger.info("[Mode5] Step 2: Preprocessing and title extraction complete.")

        # Step 3: Determine target (absolute with adaptive fallback)
        total_words = len([w for w in cleaned.split() if w.strip()])
        self.original_words = total_words  # Store for prompt target validation
        
        # VALIDATION: Reject documents too short to meaningfully summarize
        from config.settings import MIN_EXTRACTED_WORDS
        if total_words < MIN_EXTRACTED_WORDS:
            raise ValueError(
                f"Document too short to summarize effectively. "
                f"Minimum viable length: {MIN_EXTRACTED_WORDS} words, document has: {total_words} words. "
                f"Consider expanding the document or using it as-is without summarization."
            )
        
        small_doc = total_words < self.SMALL_DOCUMENT_DIRECT_THRESHOLD

        # Extract target from prompt if present
        prompt_target = None
        if user_prompt:
            prompt_target = self._extract_target_from_prompt(user_prompt)
            if prompt_target:
                logger.info(f"[Mode5] Found target in prompt: {prompt_target} words")

        # Determine effective target with updated precedence
        if prompt_target is not None:
            effective_target = prompt_target
            target_mode = "prompt"
            prompt_overrode_param = target_words is not None and target_words > 0
        elif target_words is not None and target_words > 0:
            # if target_words <= 0:
            #     raise ValueError("target_words must be positive.")
            if target_words > total_words:
                # ADAPTIVE FALLBACK: When user requests impossible target,
                # fall back to intelligent adaptive compression instead of capping
                logger.info(f"[Mode5] Impossible target ({target_words} > {total_words} words). Using adaptive fallback.")
                
                # Use same adaptive logic as the fallback case
                if total_words <= 50:
                    compression_ratio = 0.75  # 75% - very gentle
                    scenario = "micro_document"
                elif total_words <= 100:
                    compression_ratio = 0.55  # 55% - moderate
                    scenario = "very_short_document"
                elif total_words <= 200:
                    compression_ratio = 0.40  # 40% - standard
                    scenario = "short_document"
                elif total_words <= 400:
                    compression_ratio = 0.30  # 30% - targeted
                    scenario = "medium_short_document"
                elif total_words <= 800:
                    compression_ratio = 0.25  # 25% - efficient
                    scenario = "medium_document"
                else:
                    compression_ratio = 0.20  # 20% - minimum floor
                    scenario = "large_document"
                
                # Calculate adaptive target with minimum viable summary logic
                auto_target = max(1, round(total_words * compression_ratio))
                MINIMUM_VIABLE_WORDS = 15  # Absolute floor for readability
                if auto_target < MINIMUM_VIABLE_WORDS:
                    effective_target = MINIMUM_VIABLE_WORDS
                    target_mode = f"adaptive_fallback_{scenario}_floored"
                    logger.info(f"[Mode5] Adaptive fallback target ({auto_target}) below viable minimum. Using floor of {MINIMUM_VIABLE_WORDS} words.")
                else:
                    effective_target = auto_target
                    target_mode = f"adaptive_fallback_{scenario}"
                
                logger.info(f"[Mode5] Adaptive fallback: {scenario} ({total_words} words) → {compression_ratio*100:.0f}% compression → {effective_target} words target")
            else:
                effective_target = target_words
                target_mode = "user_absolute"
            prompt_overrode_param = False
        else:
            # No valid target provided (None or 0) - use ADAPTIVE compression ratios
            
            # ADAPTIVE COMPRESSION RATIOS - Scenario-based intelligence
            if total_words <= 50:
                # MICRO DOCUMENTS: Gentle compression (75%)
                # Scenario: Tweets, short alerts, brief notes
                # Challenge: Very little room for reduction without losing meaning
                compression_ratio = 0.75  # 75% - very gentle
                scenario = "micro_document"
                
            elif total_words <= 100:
                # VERY SHORT DOCUMENTS: Moderate compression (55%)  
                # Scenario: Short emails, brief reports, incident summaries
                # Challenge: Need to preserve key facts while condensing
                compression_ratio = 0.55  # 55% - moderate
                scenario = "very_short_document"
                
            elif total_words <= 200:
                # SHORT DOCUMENTS: Standard compression (40%)
                # Scenario: Meeting notes, brief articles, status updates
                # Challenge: Balance detail preservation with conciseness
                compression_ratio = 0.40  # 40% - standard
                scenario = "short_document"
                
            elif total_words <= 400:
                # MEDIUM-SHORT DOCUMENTS: Targeted compression (30%)
                # Scenario: Blog posts, detailed reports, analysis pieces
                # Challenge: Extract core insights from moderate content
                compression_ratio = 0.30  # 30% - targeted
                scenario = "medium_short_document"
                
            elif total_words <= 800:
                # MEDIUM DOCUMENTS: Efficient compression (25%)
                # Scenario: Research papers, long articles, comprehensive reports
                # Challenge: Distill complex information effectively
                compression_ratio = 0.25  # 25% - efficient
                scenario = "medium_document"
                
            else:
                # LARGE+ DOCUMENTS: 20% compression (minimum floor)
                # Scenario: White papers, studies, books, massive reports
                # Challenge: Maintain 20% floor while handling complexity
                compression_ratio = 0.20  # 20% - absolute minimum compression
                scenario = "large_document"
            
            # Calculate effective target with minimum viable summary logic
            auto_target = max(1, round(total_words * compression_ratio))
            
            # MINIMUM VIABLE SUMMARY: Ensure summaries are never too short to be useful
            MINIMUM_VIABLE_WORDS = 15  # Absolute floor for readability
            if auto_target < MINIMUM_VIABLE_WORDS:
                effective_target = MINIMUM_VIABLE_WORDS
                target_mode = f"adaptive_{scenario}_floored"
                logger.info(f"[Mode5] Adaptive target ({auto_target}) was below viable minimum. Using floor of {MINIMUM_VIABLE_WORDS} words.")
            else:
                effective_target = auto_target
                target_mode = f"adaptive_{scenario}"
            
            # Cap at original length (can't summarize to more than source)
            effective_target = min(effective_target, total_words)
            prompt_overrode_param = False
            
            logger.info(f"[Mode5] Adaptive compression: {scenario} ({total_words} words) → {compression_ratio*100:.0f}% compression → {effective_target} words target")

        meta.update({
            'requested_target_words': target_words,
            'resolved_target_words': effective_target,
            'target_mode': target_mode,
            'original_total_words': total_words,
            'user_prompt_present': user_prompt is not None,
            'parsed_prompt_target_words': prompt_target,
            'prompt_overrode_param': prompt_overrode_param
        })
        baseline = compute_baseline_metrics(
            cleaned,
            final_target_override=effective_target,
        )
        logger.info(f"[Mode5] Step 3: Baseline metrics: {baseline}")

        # Step 4-8: Intelligent summarization
        if small_doc:
            logger.info(f"[Mode5] Small document direct summarization (words={baseline.total_words} < {self.SMALL_DOCUMENT_DIRECT_THRESHOLD}).")
            # Direct summarization for small documents
            final_summary = await self._direct_summarize(
                cleaned, effective_target, logger, 
                user_prompt=user_prompt, output_format=output_format,
                title=document_title, has_title=has_title
            )
        else:
            logger.info("[Mode5] Large document chunked summarization.")
            # Chunked approach for large documents
            final_summary = await self._chunked_summarize(
                cleaned, effective_target, logger, output_format=output_format,
                title=document_title, has_title=has_title
            )
        
        # Create final result object
        from services.finalize import FinalizedSummary
        from utils.validator import is_summary_truncated
        
        # Check if final summary is complete (should always be after our improvements)
        is_truncated = is_summary_truncated(final_summary)
        actual_words = len(final_summary.split())
        
        final = FinalizedSummary(
            text=final_summary,
            summary_words=actual_words,
            target_words=effective_target,
            achieved_ratio=actual_words / float(effective_target)
        )

        enforcement_meta = {
            'target_words': baseline.final_target_words,
            'explicit_target': target_words is not None,
            'auto_20pct_mode': (meta.get('target_mode') == 'auto_20pct'),
            'final_diff': abs(actual_words - baseline.final_target_words),
            'small_doc_fast_path': small_doc,
            'approach': 'direct' if small_doc else 'chunked',
            'truncated': False,  # Should always be False after cleanup in methods
            'complete_sentences': True,  # Should always be True after our improvements
            'within_target': abs(actual_words - effective_target) / effective_target <= 0.15 if effective_target else True
        }

        # Step 9: Format output
        result = format_output(final, baseline.total_words, output_format=output_format)
        if isinstance(result, dict):
            result.setdefault('meta', {})
            result['meta'].update({'ingest': meta, 'length_enforcement': enforcement_meta})
        return result



    async def _direct_summarize(self, content: str, target_words: int, logger, user_prompt: str | None = None, output_format: str = "markdown", title: str | None = None, has_title: bool = False) -> str:
        """Direct summarization with consistent length enforcement and retry logic."""
        logger.info(f"[Mode5] Direct summarization to {target_words} words with consistency enforcement.")
        
        # Define acceptable range (±8% for good balance between strictness and completion)
        min_acceptable = int(target_words * 0.92)  # 8% below
        max_acceptable = int(target_words * 1.08)  # 8% above
        
        # Attempt summarization with retry logic for consistency
        max_attempts = 3
        attempt = 1
        best_summary = None
        best_deviation = float('inf')
        
        while attempt <= max_attempts:
            logger.info(f"[Mode5] Attempt {attempt}/{max_attempts} for target={target_words} words")
            
            # Build prompts with attempt-specific adjustments
            system_prompt = self._build_consistent_system_prompt(target_words, output_format, attempt, min_acceptable, max_acceptable, has_title=has_title)
            user_message = self._build_user_message(content, target_words=target_words, user_prompt=user_prompt, title=title)
            
            # Calculate conservative token budget for consistent output
            token_budget = self._calculate_consistent_token_budget(target_words)
            
            logger.info(f"[Mode5] Attempt {attempt}: token_budget={token_budget}")
            
            # IMPROVED VARIABILITY: Use higher temperatures and variety techniques while maintaining accuracy
            import time
            import hashlib
            
            # Create variety seed from content and timestamp for controlled randomness
            variety_seed = hashlib.md5(f"{content[:50]}{time.time()}".encode()).hexdigest()[:8]
            
            # BALANCED TEMPERATURE STRATEGY:
            # - Higher base temperatures for variety (0.4-0.7 range)
            # - Still controlled enough to maintain accuracy
            # - Different strategies per attempt
            if attempt == 1:
                # First attempt: Moderate creativity for variety
                temperature = 0.6
                top_p = 0.85
                # Add variety instruction to system prompt
                variety_instruction = f"""
        🎨 VARIETY ENHANCEMENT (Seed: {variety_seed[:4]}):
        Apply ADVANCED VARIETY TECHNIQUES from the system prompt.
        - Use different opening pattern (not just "A critical [event] occurred...")
        - Vary cause phrasing ("triggered by", "following", "when", etc.)
        - Use alternative impact descriptions ("halted", "stopped", "impacted")
        - Apply different resolution phrasing ("fixed by", "resolved via", "corrected with")
        ⚠️ CRITICAL: Stay within {target_words} word target ({min_acceptable}-{max_acceptable} acceptable).
        """
            elif attempt == 2:
                # Second attempt: Different approach for variety
                temperature = 0.5
                top_p = 0.9
                variety_instruction = f"""
        🔄 ALTERNATIVE APPROACH (Seed: {variety_seed[4:8]}):
        Use DIFFERENT structure from first attempt:
        - Try impact-first or causal organization
        - Use alternative cause phrases ("stemmed from", "resulted from")
        - Apply different opening ("At 10:30 AM", "The system failed", etc.)
        - Use varied resolution terms ("service returned", "operations resumed")
        ⚠️ PREVIOUS ATTEMPT EXCEEDED RANGE: Be more concise, target exactly {target_words} words.
        """
            else:
                # Final attempt: Focus on completion over variety
                temperature = 0.4
                top_p = 0.95
                variety_instruction = f"""
        🎯 COMPLETION FOCUS - STRICT WORD COUNT:
        Ensure all key information is included with EXACTLY {target_words} words.
        MANDATORY: Stay within {min_acceptable}-{max_acceptable} word range.
        Previous attempts were too long - be more concise while maintaining completeness.
        """
            
            # Enhance system prompt with variety instruction
            enhanced_system_prompt = system_prompt + variety_instruction
            
            summary = await generate(
                system_prompt=enhanced_system_prompt,
                user_message=user_message,
                max_tokens=token_budget,
                temperature=temperature,
                top_p=top_p
            )
            
            # Check for truncation
            from utils.validator import is_summary_truncated, complete_truncated_summary
            if is_summary_truncated(summary):
                logger.warning(f"[Mode5] Attempt {attempt}: Summary truncated, attempting cleanup")
                summary = complete_truncated_summary(summary)
            
            # Clean and validate
            cleaned_summary = self._clean_summary_output(summary.strip())
            actual_words = len(cleaned_summary.split())
            deviation = abs(actual_words - target_words)
            deviation_percent = (deviation / target_words * 100) if target_words > 0 else 0
            
            logger.info(
                f"[Mode5] Attempt {attempt}: target={target_words}, actual={actual_words}, "
                f"deviation={deviation_percent:.1f}% (range: {min_acceptable}-{max_acceptable})"
            )
            
            # Check if this attempt is acceptable
            if min_acceptable <= actual_words <= max_acceptable:
                logger.info(f"[Mode5] ✅ SUCCESS on attempt {attempt}: Within acceptable range!")
                return cleaned_summary
            
            # Track best attempt (closest to target)
            if deviation < best_deviation:
                best_deviation = deviation
                best_summary = cleaned_summary
            
            # If too long, try with stricter prompt on next attempt
            if actual_words > max_acceptable and attempt < max_attempts:
                logger.warning(f"[Mode5] Attempt {attempt}: Too long ({actual_words} > {max_acceptable}), will retry with stricter prompt")
            elif actual_words < min_acceptable and attempt < max_attempts:
                logger.warning(f"[Mode5] Attempt {attempt}: Too short ({actual_words} < {min_acceptable}), will retry with expansion prompt")
            
            attempt += 1
        
        # If all attempts failed, return the best one and log final warning
        best_actual = len(best_summary.split())
        final_deviation = (best_deviation / target_words * 100) if target_words > 0 else 0
        
        logger.warning(
            f"[Mode5] ⚠️ All {max_attempts} attempts exceeded acceptable range. "
            f"Using best attempt: target={target_words}, actual={best_actual}, deviation={final_deviation:.1f}%"
        )
        
        return best_summary
    
    async def _chunked_summarize(self, content: str, target_words: int, logger, output_format: str = "markdown", title: str | None = None, has_title: bool = False) -> str:
        """Chunked summarization for large documents with intelligent token allocation."""
        logger.info("[Mode5] Step 4: Chunking started.")
        chunks = chunk_document(content)
        logger.info(f"[Mode5] Step 4: Chunking complete. Number of chunks: {len(chunks)}")
        
        if not chunks:
            raise ValueError("No valid chunks produced from document.")
        
        logger.info("[Mode5] Step 5: Per-chunk summarization started.")
        partials = await summarize_chunks(chunks)
        logger.info("[Mode5] Step 5: Per-chunk summarization complete.")
        
        logger.info("[Mode5] Step 6: Merging partial summaries started.")
        merged = merge_partial_summaries(partials, original_words=len(content.split()))
        logger.info("[Mode5] Step 6: Merging partial summaries complete.")
        
        # Final synthesis with consistency enforcement
        logger.info(f"[Mode5] Step 7: Final synthesis to {target_words} words with consistency control.")
        
        # Use same retry logic as direct summarization for chunked final step
        min_acceptable = int(target_words * 0.92)
        max_acceptable = int(target_words * 1.08)
        
        max_attempts = 2  # Fewer attempts for chunked since it's already processed
        attempt = 1
        best_summary = None
        best_deviation = float('inf')
        
        while attempt <= max_attempts:
            logger.info(f"[Mode5] Final synthesis attempt {attempt}/{max_attempts}")
            
            # Build consistent refinement prompt
            system_prompt = self._build_consistent_system_prompt(target_words, output_format, attempt, min_acceptable, max_acceptable, has_title=has_title)
            
            title_instruction = ""
            if title:
                title_instruction = f"""
            📌 DOCUMENT TITLE: "{title}"
            
            ⚠️ CRITICAL TITLE REQUIREMENT:
            - Start your summary with this EXACT title: {title}
            - DO NOT add any prefixes like "Summary of", "Unified Summary of", or similar
            - The title should appear exactly as shown, followed immediately by your summary content
            """
            
            refinement_prompt = f"""The following are summaries of different sections from a single document.
            {title_instruction}
            MANDATORY TASK: Create a comprehensive final summary with EXACTLY {target_words} words (acceptable: {min_acceptable}-{max_acceptable})

            INTEGRATION REQUIREMENTS:
            - Combine all key points from sections below
            - Remove redundancy between sections
            - Maintain logical flow and coherence
            - CRITICAL: Stay within {min_acceptable}-{max_acceptable} words
            - End with complete conclusion (no truncation)

            SECTION SUMMARIES TO INTEGRATE:
            {merged.markdown}

            Create the final integrated summary now (target: {target_words} words):"""
            
            # Conservative token budget for final synthesis
            token_budget = self._calculate_consistent_token_budget(target_words)
            
            logger.info(f"[Mode5] Final synthesis attempt {attempt}: token_budget={token_budget}")
            
            # IMPROVED VARIABILITY for chunked summarization
            import time
            import hashlib
            
            # Create variety seed for chunked summaries
            variety_seed = hashlib.md5(f"{merged.markdown[:50]}{time.time()}".encode()).hexdigest()[:8]
            
            # Use higher temperatures and variety techniques
            if attempt == 1:
                temperature = 0.5  # Increased from 0.2
                top_p = 0.85
                # Add variety instruction
                variety_instruction = f"""
        🎨 SYNTHESIS VARIETY (Seed: {variety_seed[:4]}):
        Create a unique integrated summary with varied phrasing while maintaining all key information.
        Use different sentence structures and transitions between sections.
        """
            else:
                temperature = 0.4  # Increased from 0.15
                top_p = 0.9
                variety_instruction = f"""
        🔄 ALTERNATIVE SYNTHESIS (Seed: {variety_seed[4:8]}):
        Focus on different organizational approaches while preserving all essential content.
        """
            
            # Enhance refinement prompt with variety
            enhanced_refinement_prompt = refinement_prompt + variety_instruction
            
            final_summary = await generate(
                system_prompt=system_prompt,
                user_message=enhanced_refinement_prompt,
                max_tokens=token_budget,
                temperature=temperature,
                top_p=top_p
            )
            
            # Check for truncation
            from utils.validator import is_summary_truncated, complete_truncated_summary
            if is_summary_truncated(final_summary):
                logger.warning(f"[Mode5] Final synthesis attempt {attempt}: truncated, cleaning up")
                final_summary = complete_truncated_summary(final_summary)
            
            # Validate this attempt
            cleaned_summary = self._clean_summary_output(final_summary.strip())
            actual_words = len(cleaned_summary.split())
            deviation = abs(actual_words - target_words)
            deviation_percent = (deviation / target_words * 100) if target_words > 0 else 0
            
            logger.info(
                f"[Mode5] Final synthesis attempt {attempt}: target={target_words}, actual={actual_words}, "
                f"deviation={deviation_percent:.1f}% (range: {min_acceptable}-{max_acceptable})"
            )
            
            # Check if acceptable
            if min_acceptable <= actual_words <= max_acceptable:
                logger.info(f"[Mode5] ✅ Final synthesis SUCCESS on attempt {attempt}")
                return cleaned_summary
            
            # Track best attempt
            if deviation < best_deviation:
                best_deviation = deviation
                best_summary = cleaned_summary
            
            if attempt < max_attempts:
                if actual_words > max_acceptable:
                    logger.warning(f"[Mode5] Final synthesis attempt {attempt}: Too long, will retry with stricter prompt")
                else:
                    logger.warning(f"[Mode5] Final synthesis attempt {attempt}: Too short, will retry with expansion")
            
            attempt += 1
        
        # Return best attempt if all failed
        best_actual = len(best_summary.split())
        final_deviation = (best_deviation / target_words * 100) if target_words > 0 else 0
        
        logger.warning(
            f"[Mode5] ⚠️ Final synthesis: All attempts exceeded range. "
            f"Using best: target={target_words}, actual={best_actual}, deviation={final_deviation:.1f}%"
        )
        
        return best_summary

    def _clean_summary_output(self, text: str) -> str:
        """Remove unwanted introductory phrases from LLM output."""
        import re
        
        cleaned = text.strip()
        
        # First, handle dynamic patterns with regex (word counts, percentages, etc.)
        dynamic_patterns = [
            # Patterns like "Here's a summary of the document within the 29-word target range (±5% maximum):"
            r'^Here\'?s?\s+a\s+summary\s+of\s+the\s+document\s+within\s+the\s+\d+[\-\s]*word\s+(?:target\s+)?range\s*(?:\([^)]*\))?\s*[:\s]*',
            # Patterns like "Here is a summary within the 50-word limit (±5% maximum):"
            r'^Here\s+is\s+a\s+summary\s+(?:of\s+the\s+document\s+)?within\s+the\s+\d+[\-\s]*word\s+(?:target\s+|limit\s+)?(?:range\s+)?(?:\([^)]*\))?\s*[:\s]*',
            # NEW: Catch "Here is a summary of the document in exactly X words:"
            r'^Here\s+is\s+a\s+summary\s+of\s+the\s+document\s+in\s+exactly\s+\d+\s+words?\s*[:\s]*',
            # Patterns like "Here's a 29-word summary of the document:"
            r'^Here\'?s?\s+a\s+\d+[\-\s]*word\s+summary\s+(?:of\s+the\s+(?:document|text))?\s*(?:\([^)]*\))?\s*[:\s]*',
            # Patterns like "Here is a 29-word summary:"
            r'^Here\s+is\s+a\s+\d+[\-\s]*word\s+summary\s*(?:\([^)]*\))?\s*[:\s]*',
            # Catch remaining fragments like "range (±5% maximum):" at the start
            r'^(?:target\s+)?range\s*(?:\([^)]*\))?\s*[:\s]*',
            # Catch fragments like "word target range:" or "word limit:" or "word summary:"
            r'^\d+[\-\s]*word\s+(?:target\s+|limit\s+|summary\s+)?(?:range|limit|summary)?\s*(?:\([^)]*\))?\s*[:\s]*',
            # NEW: Catch patterns like "42 word range:" at the beginning
            r'^\d+\s+word\s+range\s*[:\s]*',
            # NEW: Catch "Summary of" with markdown formatting like "**Summary of Title**"
            r'^\*\*Summary\s+of\s+[^*]+\*\*\s*',
            # NEW: Catch markdown headers like "### Title Summary" 
            r'^#{1,6}\s+[^#\n]*\s*Summary\s*\n?',
            # NEW: Patterns like "Unified Summary: [Title]" or variations
            r'^(?:Unified|Combined|Comprehensive|Complete|Final|Overall)\s+Summary:\s*',
            r'^(?:Unified|Combined|Comprehensive|Complete|Final|Overall)\s+Summary\s+of\s+[^:]*:?\s*',
            # NEW: Catch title rephrasing patterns like "Summary: API Integration for Modern Connectivity"
            r'^(?:Summary|Unified\s+Summary):\s*[A-Z][^:\n]*(?:for|of|in|on|about)\s+[^:\n]*\s*',
            # More comprehensive generic patterns
            r'^(?:Here\'?s?|Below\s+is|This\s+is)\s+(?:a\s+)?summary\s+(?:of\s+)?(?:the\s+)?(?:document|text)?\s*(?:within|in)?\s*(?:the\s+)?\d*[\-\s]*(?:word|target)?\s*(?:range|limit)?\s*(?:\([^)]*\))?\s*[:\-\s]*',
            # Catch any remaining percentage notations at the start
            r'^(?:\([±]\d+%?\s*(?:maximum|tolerance)?\))?\s*[:\s]*',
        ]
        
        # Apply dynamic pattern removal
        for pattern in dynamic_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
            cleaned = cleaned.strip()
        
        # Then handle static unwanted prefixes (case-insensitive) - ENHANCED LIST
        unwanted_prefixes = [
            # Basic summary prefixes
            "Here's a summary of the text:",
            "Here is a summary of the text:",
            "Here's a summary:",
            "Here is a summary:",
            "Summary:",
            "The following is a summary:",
            "This is a summary of the text:",
            "Below is a summary:",
            "Here's the summary:",
            "Here is the summary:",
            
            # Unified/Combined summary prefixes (NEW) - Including standalone forms
            "Unified Summary:",
            "Unified Summary of",
            "Unified summary:",
            "Unified summary of",
            "Combined Summary:",
            "Combined Summary of",
            "Combined summary:",
            "Combined summary of",
            "Comprehensive Summary:",
            "Comprehensive Summary of",
            "Comprehensive summary:",
            "Comprehensive summary of",
            "Complete Summary:",
            "Complete Summary of",
            "Complete summary:",
            "Complete summary of",
            "Final Summary:",
            "Final Summary of",
            "Final summary:",
            "Final summary of",
            "Overall Summary:",
            "Overall Summary of",
            "Overall summary:",
            "Overall summary of",
            "Comprehensive Summary:",
            "Comprehensive Summary of",
            
            # Document-specific prefixes
            "Summary of the document:",
            "Summary of the text:",
            "Document summary:",
            "Text summary:",
            "Article summary:",
            
            # Other common AI prefixes
            "Based on the document:",
            "According to the text:",
            "The document discusses:",
            "This document covers:",
            "The text explains:",
        ]
        
        for prefix in unwanted_prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove any remaining leading colons, dashes, or whitespace
        cleaned = cleaned.lstrip(":- \t\n").strip()
        
        # Remove extra blank lines at the beginning
        cleaned = re.sub(r'^\s*\n+', '', cleaned)
        
        return cleaned

    def _extract_target_from_prompt(self, prompt: str) -> int | None:
        """Extract word count target from prompt text."""
        import re
        patterns = [
            r'\b(?:in|into|about|around|approximately|approx\.?)\s+(\d{2,5})\s+words?\b',
            r'\bsummary\s+of\s+(\d{2,5})\s+words?\b',
            r'\b(\d{2,5})\s+word(?:\b|s\b)'
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, prompt, re.IGNORECASE):
                target = int(match.group(1))
                # Allow smaller targets for very small documents
                min_target = 5 if self.original_words < 50 else 10
                if min_target <= target <= self.original_words:
                    return target
        return None

__all__ = ["Mode5"]