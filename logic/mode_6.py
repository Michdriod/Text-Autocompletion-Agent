from typing import Optional, Dict, Union
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length

class Mode6:
    """
    Document Development Agent
    Produces polished, professional, publication-ready documents from header and body.
    """

    def get_system_prompt(self) -> str:
        return (
            """You are a senior-level document development assistant. Produce polished, professional, publication-ready documents.

            CORE PRINCIPLES:
            - Structure clearly with standardized section headings (use single blank lines between sections).
            - Avoid excessive inline bolding – use clean headings instead (e.g., 'Executive Summary', not '**Executive Summary:**').
            - Rewrite and normalize any messy or over-formatted input; do NOT echo raw asterisk-heavy markup from the source.
            - Maintain a consistent, formal, confident tone (unless the header implies a creative narrative).
            - Keep lists parallel (each bullet starts with a strong noun or infinitive verb).
            - Use numbered lists for ordered steps / goals; bullets for unordered items.
            - Avoid redundancy; do not restate the title in every section.
            - If length constraints exist, prioritize: Title/Executive Summary > Core Sections > KPIs > Risks > Timeline > Appendix.

            DEFAULT BUSINESS-STYLE SECTION ORDER (adapt when appropriate):
            1. Title (concise)
            2. Executive Summary (short paragraph)
            3. Introduction / Context
            4. Objectives or Goals
            5. Strategy / Approach (subsections allowed)
            6. Implementation Plan / Phases
            7. KPIs & Measurement
            8. Risks & Mitigation
            9. Resource & Budget (if relevant)
            10. Timeline (tabular or phased bullets)
            11. Conclusion / Call to Action

            FOR TECHNICAL GUIDES: include Prerequisites, Step-by-Step, Best Practices, Troubleshooting.
            FOR CREATIVE STORIES: structure with Title, Opening Hook, Rising Development, Climax, Resolution, Optional Reflection.

            FORMATTING RULES:
            - Use plain text headings (no Markdown hashes unless explicitly requested) like: EXECUTIVE SUMMARY\n
            - Separate sections with a single blank line only.
            - Keep bullet points concise (≤ 20 words where possible).
            - Do not wrap entire paragraphs in bold or asterisks.
            - Convert any inline **bold** sequences in input into clean plain-text headings or emphasis only when necessary.

            QUALITY CHECK BEFORE RETURNING:
            1. Is every heading necessary? Remove filler.
            2. Are there any duplicated concepts? Merge them.
            3. Are tense, voice, and style consistent?
            4. Does Executive Summary stand alone?
            5. Are KPIs specific and measurable where applicable?

            If the header implies a specific genre or style, adapt structure accordingly while keeping professionalism and clarity.
            """
        )
    
    def prepare_user_message(
        self,
        header: str,
        body: str,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        """Build the user-facing instruction message for the model.

        header: High-level purpose / intent of the document.
        body:   Descriptive details the user provided (free text, NOT JSON).
        max_output_length: Optional constraint dict: {"type": "characters"|"words", "value": int}
        """
        message = (
            "TASK: Develop a professionally structured document using the guidance below.\n\n"
            f"HEADER (Purpose): {header}\n\n"
            "SOURCE BRIEF / RAW INPUT (may contain noisy formatting):\n"
            f"{body}\n\n"
            "INSTRUCTIONS:\n"
            "- Normalize formatting: remove excessive asterisks, redundant bold markers, and inline styling artifacts.\n"
            "- Derive a clean, concise Title (do not wrap in asterisks).\n"
            "- Provide an Executive Summary (3–5 sentences) that is self-contained.\n"
            "- Organize content into clear sections (see system prompt section ordering suggestions).\n"
            "- Rewrite content for clarity, concision, and professional tone.\n"
            "- Where the brief lists metrics/goals inline, convert to structured numbered or bulleted lists.\n"
            "- Avoid repeating the Title inside other sections.\n"
            "- Eliminate duplicated statements (e.g., repeated budget lines).\n"
            "- If KPIs or metrics are present, format them in a dedicated 'KPIs & Measurement' section.\n"
            "- ONLY include sections that add value; omit empty placeholders.\n"
            "- Do not enclose headings in asterisks or quotes.\n"
        )

        # if max_output_length:
        #     length_type = max_output_length.get("type", "characters")
        #     length_value = max_output_length.get("value", 2000)
        #     message += f"\n\nIMPORTANT: Keep your Document to a maximum of {length_value} {length_type}."

        return message + build_length_instruction(max_output_length)
    
    def get_generation_parameters(self) -> dict:
        # Use moderate temperature for balanced creativity and coherence
        return {"temperature": 0.7, "top_p": 0.9}
    
    async def process(
        self,
        header: str,
        body: str,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        """Generate a developed document from header + descriptive body.

        The handler guarantees header/body presence & type; we do a lightweight
        sanity check here to avoid empty strings reaching the model.
        """
        if not header.strip():
            raise ValueError("Header cannot be empty for Mode 6 document development.")
        if not body.strip():
            raise ValueError("Body (description) cannot be empty for Mode 6 document development.")
        system_prompt = self.get_system_prompt()
        gen_params = self.get_generation_parameters()
        plan = plan_output_length("mode_6", max_output_length, body=body)
        length_instruction_target = max_output_length or plan["constraint"]
        user_message = self.prepare_user_message(header, body, length_instruction_target)
        max_tokens = plan["token_budget"]

        completion = await generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=max_tokens,
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )
        # Post-process to enforce professional structural formatting
        return self.post_process(completion, header)

    # --- Formatting Utilities ---
    def post_process(self, text: str, header: str) -> str:
        """Normalize and structure the model output for professional readability.

        Operations (gentle to avoid damaging creative outputs):
        - Strip stray markdown bold markers
        - Isolate recognized section headings on their own line in UPPERCASE
        - Ensure a blank line AFTER every heading; no text on same heading line
        - Extract/derive a Title (first line) if the model merged it with the first heading
        - Normalize numbered and bullet lists (each item on its own line)
        - Collapse duplicate blank lines
        - Remove duplicated adjacent headings
        """
        import re

        original = text.strip()
        if not original:
            return original
        cleaned = original.replace('\r', '')
        cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)  # remove bold wrappers

        # Headings vocabulary (canonical uppercase form)
        canonical_headings = [
            'EXECUTIVE SUMMARY','INTRODUCTION','OBJECTIVES','GOALS','STRATEGY','IMPLEMENTATION PLAN',
            'KPIS & MEASUREMENT','RISKS & MITIGATION','RESOURCE & BUDGET','TIMELINE','CONCLUSION'
        ]

        # Build a heading regex without inline flags; apply IGNORECASE via flags to avoid
        # 'global flags not at the start of the expression' errors when embedded.
        heading_regex = r"\b(" + "|".join([re.escape(h) for h in canonical_headings]) + r")\b"

        # If title merged with EXECUTIVE SUMMARY etc., split it: insert newline before heading token
        cleaned = re.sub(
            rf"([^\n])\s*{heading_regex}",
            lambda m: f"{m.group(1)}\n{m.group(2).upper()}",
            cleaned,
            flags=re.IGNORECASE
        )

        # Uppercase all recognized headings on their own line
        def normalize_heading_line(match):
            return match.group(1).upper()
        cleaned = re.sub(
            rf"^\s*{heading_regex}\s*$",
            normalize_heading_line,
            cleaned,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Ensure headings start on their own line (add newline before if inline)
        cleaned = re.sub(
            rf"(?<!\n){heading_regex}(?= )",
            lambda m: f"\n{m.group(1).upper()}",
            cleaned,
            flags=re.IGNORECASE
        )

        # Put blank line after headings (remove trailing colons)
        def heading_with_spacing(match):
            h = match.group(1).upper().rstrip(':')
            return f"{h}\n\n"
        cleaned = re.sub(
            rf"^(\s*){heading_regex}[:]??\s*",
            lambda m: heading_with_spacing(m),
            cleaned,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Split numbered items onto new lines if crammed
        cleaned = re.sub(r"(?<!\n)(\d+\. )", r"\n\1", cleaned)

        # Normalize bullet markers: asterisk or dash -> dash
        cleaned = re.sub(r"^\s*[\*•]\s*", "- ", cleaned, flags=re.MULTILINE)

        # Ensure list items each on own line (if separated by '; ' or ' * ' inside a paragraph)
        cleaned = re.sub(r"(\d+\.\s[^\n]+?)\s+(\d+\.\s)", r"\1\n\2", cleaned)

        # Collapse multiple spaces inside lines
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)

        # Reduce excessive blank lines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # Split into lines for title handling
        lines = [ln.rstrip() for ln in cleaned.strip().split('\n') if ln.strip()]
        if not lines:
            return cleaned.strip()

        first_line = lines[0]
        # If first line is actually a heading, inject title from header
        if first_line.upper() in canonical_headings:
            title = self._derive_title(header)
            lines.insert(0, title)

        # Deduplicate consecutive identical headings
        deduped = []
        prev = None
        for ln in lines:
            if prev and ln.upper() == prev.upper() and ln.upper() in canonical_headings:
                continue
            deduped.append(ln)
            prev = ln

        # Rebuild with blank line after headings
        final_lines = []
        for i, ln in enumerate(deduped):
            final_lines.append(ln)
            if ln.upper() in canonical_headings:
                # Add blank line if next line exists and isn't blank already
                if i+1 < len(deduped) and deduped[i+1].strip():
                    final_lines.append("")

        result = '\n'.join(final_lines)
        return result.strip()

    def _derive_title(self, header: str) -> str:
        # Simple heuristic: Title Case header without trailing punctuation
        h = header.strip().rstrip(':').strip()
        if not h:
            return 'Document'
        # Title case while preserving ALL CAPS acronyms
        words = h.split()
        def tc(w):
            return w if (len(w) <= 3 and w.isupper()) else w.capitalize()
        return ' '.join(tc(w) for w in words)