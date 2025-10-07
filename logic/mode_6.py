"""
Mode 6 - Document Development Agent
-----------------------------------
Generates polished, professional, publication-ready documents 
from a given header (title/purpose) and descriptive body text.

This module interacts directly with the generator utility to call 
the LLM and return a fully structured document output.
"""

from typing import Optional, Dict, Union
from utils.generator import generate
from utils.validator import build_length_instruction, plan_output_length
import re


class Mode6:
    """
    Document Development Agent
    Produces polished, professional, publication-ready documents from header and body.
    """

    # --- SYSTEM PROMPT ---
    def get_system_prompt(self) -> str:
        """Defines behavior and structure guidelines for the document developer agent."""
        return (
            """You are a senior-level document development assistant.
            Your job is to produce structured, professional, and polished documents 
            ready for presentation or publication.

            CORE PRINCIPLES:
            - Follow standard business or formal writing structures.
            - Use clear section headers (avoid Markdown ### unless explicitly requested).
            - Write with confidence, conciseness, and logical flow.
            - Prioritize readability over length.
            - Always start with a concise TITLE followed by an EXECUTIVE SUMMARY.
            - Use numbered lists for ordered items, bullets for unordered items.
            - Avoid unnecessary repetition and over-formatting.
            - Maintain consistent tone and tense.

            SECTION ORDER (adapt as needed):
            1. Title
            2. Executive Summary
            3. Introduction or Context
            4. Objectives or Goals
            5. Strategy or Implementation
            6. KPIs or Metrics
            7. Risks & Mitigation
            8. Timeline
            9. Conclusion / Next Steps

            For creative or technical documents, adapt structure naturally.
            """
        )

    # --- USER MESSAGE BUILDER ---
    def prepare_user_message(
        self,
        header: str,
        body: str,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        """Builds the user-facing instruction message for the model."""
        message = (
            "TASK: Develop a professionally structured document using the guidance below.\n\n"
            f"HEADER (Purpose): {header}\n\n"
            f"INPUT DETAILS:\n{body}\n\n"
            "INSTRUCTIONS:\n"
            "- Normalize formatting and remove redundant styling.\n"
            "- Provide an Executive Summary (3–5 sentences) that captures the core idea.\n"
            "- Organize content into clear sections using standard titles.\n"
            "- Rewrite for professional tone and smooth flow.\n"
            "- Avoid restating the title in other sections.\n"
            "- If any metrics or KPIs are present, place them in a 'KPIs & Measurement' section.\n"
            "- Do not wrap headings in quotes or asterisks.\n"
        )
        return message + build_length_instruction(max_output_length)

    # --- GENERATION CONFIG ---
    def get_generation_parameters(self) -> dict:
        """Set generation behavior (controls creativity and coherence)."""
        return {"temperature": 0.7, "top_p": 0.9}

    # --- MAIN PROCESS METHOD ---
    async def process(
        self,
        header: str,
        body: str,
        max_output_length: Optional[Dict[str, Union[str, int]]] = None
    ) -> str:
        """Generate a structured, professional document from given header and body."""
        if not header.strip():
            raise ValueError("Header cannot be empty for Mode 6 document development.")
        if not body.strip():
            raise ValueError("Body (description) cannot be empty for Mode 6 document development.")

        system_prompt = self.get_system_prompt()
        gen_params = self.get_generation_parameters()
        plan = plan_output_length("mode_6", max_output_length, body=body)
        length_target = max_output_length or plan["constraint"]
        user_message = self.prepare_user_message(header, body, length_target)

        completion = await generate(
            system_prompt=system_prompt,
            user_message=user_message,
            max_tokens=plan["token_budget"],
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"]
        )

        return self.post_process(completion, header)

    # --- POST-PROCESSING (FORMATTING CLEANUP) ---
    def post_process(self, text: str, header: str) -> str:
        """Normalize and structure model output for readability and consistency."""
        if not text:
            return ""

        cleaned = text.strip().replace('\r', '')
        cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)  # remove bold wrappers
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)  # reduce excessive blank lines
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)  # normalize spacing

        # Insert title if the model started directly with a heading
        lines = [ln.strip() for ln in cleaned.split('\n') if ln.strip()]
        if not lines:
            return cleaned

        first_line = lines[0]
        if first_line.isupper() or first_line.lower().startswith(("executive summary", "introduction")):
            title = self._derive_title(header)
            lines.insert(0, title)

        # Deduplicate consecutive identical headings
        deduped = []
        prev = None
        for ln in lines:
            if prev and ln.upper() == prev.upper():
                continue
            deduped.append(ln)
            prev = ln

        return "\n".join(deduped).strip()

    # --- TITLE BUILDER ---
    def _derive_title(self, header: str) -> str:
        """Generate a clean title from the given header."""
        h = header.strip().rstrip(':')
        if not h:
            return "Document"
        words = h.split()
        def tc(w): return w if (len(w) <= 3 and w.isupper()) else w.capitalize()
        return ' '.join(tc(w) for w in words)
