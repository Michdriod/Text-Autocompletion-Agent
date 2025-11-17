from typing import Optional
import re
from utils.generator import generate
from services.input_validation import validate_kb_inputs
from services.context_extraction import extract_context
from services.article_planner import plan_article_length
from services.coverage_audit import check_keyword_coverage


class Mode6:
    """KB Article Generation - Creates structured knowledge base articles from title + description."""

    async def generate_article(
        self,
        title: str,
        description: str,
        length: str = 'medium',
        keywords: Optional[list[str]] = None,
        output_format: str = "markdown"
    ) -> dict:
        """Generate KB article. Returns dict with markdown, sections, and metrics."""
        # Step 1: Validate inputs
        validation = validate_kb_inputs(title, description, length, keywords)
        if not validation['valid']:
            raise ValueError(
                f"Input validation failed:\n" +
                "\n".join(f"- {issue}" for issue in validation['issues']) +
                "\n\nSuggestions:\n" +
                "\n".join(f"• {s}" for s in validation['suggestions'])
            )
        
        # Step 2: Extract context
        context = extract_context(description, keywords)
        
        # Step 3: Plan length and sections based on user choice
        plan = plan_article_length(length, context)
        
        # Step 4: Generate sections
        sections = {}
        for section in plan['sections']:
            target_words = plan['allocation'][section]
            sections[section] = await self._generate_section(
                title, description, section, target_words, context
            )
        
        # Step 5: Audit coverage
        full_text = ' '.join(sections.values())
        coverage = check_keyword_coverage(full_text, context['keywords'])
        
        # Step 6: Regenerate if coverage fails
        if not coverage['passed'] and coverage['missing']:
            # Regenerate notes with missing keywords
            fallback_section = 'notes' if 'notes' in sections else plan['sections'][-1]
            sections[fallback_section] = await self._regenerate_with_keywords(
                title, description, fallback_section, 
                plan['allocation'].get(fallback_section, 100),
                context, coverage['missing']
            )
        
        # Step 7: Assemble article
        markdown = self._assemble_markdown(title, sections, plan['sections'])
        
        return {
            'title': title.strip(),
            'sections': sections,
            'markdown': markdown,
            'html': self._markdown_to_html(markdown) if output_format in ('html', 'all') else None,
            'metrics': {
                'total_words': len(full_text.split()),
                'target_words': plan['total_target_words'],
                'length_choice': length,
                'word_range': f"{plan['word_range'][0]}-{plan['word_range'][1]}",
                'keyword_coverage': coverage['coverage'],
                'complexity': context['complexity']
            }
        }

    async def _generate_section(
        self, title: str, description: str, section: str,
        target_words: int, context: dict
    ) -> str:
        """Generate a single section."""
        system_prompt = self._build_section_system_prompt(section)
        user_prompt = self._build_section_user_prompt(
            title, description, section, target_words, context
        )
        
        # Token budget: words / 0.75 * 1.4 buffer
        max_tokens = int((target_words / 0.75) * 1.4)
        
        result = await generate(
            system_prompt=system_prompt,
            user_message=user_prompt,
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=0.9
        )
        
        return result.strip()

    async def _regenerate_with_keywords(
        self, title: str, description: str, section: str,
        target_words: int, context: dict, missing_keywords: list[str]
    ) -> str:
        """Regenerate section with emphasis on missing keywords."""
        system_prompt = self._build_section_system_prompt(section)
        user_prompt = self._build_section_user_prompt(
            title, description, section, target_words, context
        )
        user_prompt += f"\n\nCRITICAL: Ensure these keywords appear: {', '.join(missing_keywords)}"
        
        max_tokens = int((target_words / 0.75) * 1.4)
        
        result = await generate(
            system_prompt=system_prompt,
            user_message=user_prompt,
            max_tokens=max_tokens,
            temperature=0.4,
            top_p=0.9
        )
        
        return result.strip()

    def _build_section_system_prompt(self, section: str) -> str:
        """Build system prompt for specific section."""
        base = """You are a technical documentation specialist creating IT knowledge base articles.

CORE RULES:
- Use ONLY information from the provided description and context
- If specific details are missing, use placeholders: "(Specify version)" or "(Confirm path)"
- Never invent commands, paths, versions, or technical details
- Write clearly and professionally for IT professionals
- Be concise and actionable
"""
        
        section_guides = {
            'prerequisites': """
SECTION: Prerequisites
- Bullet list of required access, tools, or conditions
- Each item: resource + minimum version/level
- Format: "- Resource (minimum requirement)"
- Example: "- Administrative access to the server", "- Apache 2.4+ installed"
- Keep technical and specific""",
            
            'purpose': """
SECTION: Purpose
- Write 1-2 flowing paragraphs (60-100 words total) without forced line breaks
- Explain what this article covers and who it's for (IT audience)
- State the technical problem or goal clearly in complete sentences
- Mention the system/platform involved
- Keep paragraphs natural and readable, not wrapped artificially""",
            
            'symptoms': """
SECTION: Symptoms (Troubleshooting Context)
- Write a concise introductory sentence, then bullet list of technical issues
- Each symptom: what IT staff/users observe + operational impact
- Format: "- [Symptom description] (impact on system/operations)"
- Include error codes, log entries, or system behavior
- Write naturally without forced line breaks between items""",
            
            'steps': """
SECTION: Step-by-Step Instructions
- Write a brief section title/intro if needed, then numbered list (1. 2. 3.)
- Each step: Action + Rationale + Expected Outcome
- Format: "1. **Action**: Technical description with specific details (system names, paths, commands). *Why*: Reason. *Expected*: Result."
- Use bold for actions, italics for rationale/expected
- Include specific systems, commands, configuration paths where applicable
- Be technically precise - avoid generic phrases like 'Set up account' - specify WHERE and HOW
- Each step should be actionable by an IT professional
- Keep each step as a complete, properly formatted numbered item
- Write naturally without artificial line wrapping""",
            
            'validation': """
SECTION: Validation Steps
- Write a brief intro sentence explaining validation purpose
- Then use checklist format: "- [ ] Item"
- Each item: technical test action + success criteria
- Format: "- [ ] Check X (should show Y)"
- Write each checkbox item as a complete, properly formatted line
- No forced line breaks within checklist items""",
            
            'troubleshooting': """
SECTION: Troubleshooting Tips
- Write a brief section intro, then bullet list of issues and fixes
- Format: "- **Issue**: Description → **Fix**: Solution"
- Each bullet should be complete and properly formatted
- Include error messages, symptoms, and resolutions
- Write naturally with proper sentence flow, no artificial wrapping""",
            
            'notes': """
SECTION: Additional Notes
- Write flowing paragraphs or use organized bullet sections (e.g., Prerequisites:, Common Pitfalls:)
- Include technical caveats, tips, warnings, dependencies
- Each bullet or paragraph should be complete and naturally written
- Use proper subheadings with bold (e.g., **Prerequisites:**) to organize content
- No forced line breaks, keep text readable and professional""",
            
            'best_practices': """
SECTION: Best Practices
- Bullet list of recommended IT standards or approaches
- Each item: practice + technical benefit
- Format: "- **Practice**: Description (benefit)"
- Focus on security, performance, maintainability
- Keep aligned with IT industry standards""",
            
            'faq': """
SECTION: Frequently Asked Questions
- Q&A format for common technical questions
- Format: "**Q: Question?** A: Technical answer."
- Address IT administrator concerns
- Keep answers concise but technically accurate
- Include references to relevant sections if needed"""
        }
        
        return base + section_guides.get(section, '')

    def _build_section_user_prompt(
        self, title: str, description: str, section: str,
        target_words: int, context: dict
    ) -> str:
        """Build user prompt for section generation."""
        context_block = self._format_context_block(context)
        
        return f"""ARTICLE TITLE: {title}

DESCRIPTION:
{description}

{context_block}

TASK: Generate the '{section}' section (~{target_words} words)

CONSTRAINTS:
- Stay within {int(target_words * 0.9)}-{int(target_words * 1.1)} words
- Use only facts from description above
- If details missing, use "(Specify)" placeholder
- Output section content only (no meta-commentary)

Generate the {section} section now:"""

    def _format_context_block(self, context: dict) -> str:
        """Format extracted context for prompt."""
        lines = ["CONTEXT FACTS:"]
        
        if context['keywords']:
            lines.append(f"Keywords: {', '.join(context['keywords'])}")
        
        entities = context['entities']
        if entities.get('paths'):
            lines.append(f"Paths: {', '.join(entities['paths'][:3])}")
        if entities.get('versions'):
            lines.append(f"Versions: {', '.join(entities['versions'][:3])}")
        if entities.get('error_codes'):
            lines.append(f"Error Codes: {', '.join(entities['error_codes'][:3])}")
        
        lines.append(f"Complexity: {context['complexity']}")
        
        return '\n'.join(lines)

    def _assemble_markdown(self, title: str, sections: dict, section_order: list[str]) -> str:
        """Assemble final markdown article."""
        lines = [f"# {title}", ""]
        
        section_headers = {
            'prerequisites': '## Prerequisites',
            'purpose': '## Purpose',
            'symptoms': '## Symptoms',
            'steps': '## Step-by-Step Instructions',
            'validation': '## Validation Steps',
            'troubleshooting': '## Troubleshooting Tips',
            'notes': '## Additional Notes',
            'best_practices': '## Best Practices',
            'faq': '## Frequently Asked Questions'
        }
        
        for section in section_order:
            if section in sections:
                lines.append(section_headers.get(section, f"## {section.replace('_', ' ').title()}"))
                lines.append("")
                lines.append(sections[section])
                lines.append("")
        
        return '\n'.join(lines).strip()

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple markdown to HTML conversion."""
        html = markdown
        
        # Headers
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        
        # Bold and italic
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        
        # Lists (simple)
        html = re.sub(r'^- \[ \] (.+)$', r'<li>☐ \1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html, flags=re.MULTILINE)
        
        # Wrap consecutive <li> in <ul>
        lines = html.split('\n')
        result = []
        in_list = False
        for line in lines:
            if '<li>' in line:
                if not in_list:
                    result.append('<ul>')
                    in_list = True
                result.append(line)
            else:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                result.append(line if line.strip() else '<br/>')
        
        if in_list:
            result.append('</ul>')
        
        return '\n'.join(result)


# Legacy compatibility wrapper
class Mode6Legacy:
    """Legacy Mode6 wrapper for backward compatibility."""
    async def process(self, header: str, body: str, max_output_length=None) -> str:
        """Legacy interface - generates article and returns markdown only."""
        mode6 = Mode6()
        result = await mode6.generate_article(
            title=header,
            description=body,
            keywords=None,
            output_format="markdown"
        )
        return result['markdown']