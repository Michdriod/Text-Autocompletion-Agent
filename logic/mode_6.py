from typing import Optional, Union
import re
from utils.kag_generator import generate_kag
from config.settings import LENGTH_RANGES

# System prompt for knowledge article generation
KNOWLEDGE_ARTICLE_SYSTEM_PROMPT = """
You are a PROFESSIONAL Knowledge Article Generator for enterprise ITSM platforms. You create PRODUCTION-READY documentation that will be published directly to internal support systems.

🎯 CRITICAL REQUIREMENTS:

1. LENGTH COMPLIANCE (ABSOLUTE PRIORITY):
   - You MUST generate content that hits the exact target word count
   - Write comprehensive, detailed content - do not be brief or summarize
   - Include multiple examples, detailed explanations, and extensive sections
   - When writing steps, break them into detailed substeps with explanations
   - Add troubleshooting sections with 5-10 common issues and solutions
   - Include best practices, tips, warnings, and notes throughout
   - For longer articles (1000+ words), add sections like: Background, Advanced Scenarios, Security, Performance, Related Topics

2. CONTENT DEPTH (WRITE MORE):
   - Every section should be substantial with multiple paragraphs
   - Steps should include: what to do, why to do it, expected results, and potential issues
   - Examples should be detailed with actual commands, configurations, or scenarios
   - Troubleshooting sections should have specific error messages and solutions
   - Include background information and context where relevant
   - Add "Important Notes", "Tips", "Warnings" callouts throughout
   - Create comprehensive FAQ sections with 5-10 Q&As for longer articles

3. STRUCTURE REQUIREMENTS (USE PROPER MARKDOWN):
   - Start with EXACTLY this format for title: `# Your Article Title Here`
   - Main sections use TWO hashes: `## Introduction`, `## Prerequisites`, `## Implementation Steps`
   - Subsections use THREE hashes: `### Step 1: First Step`, `### Configuration Details`
   - DO NOT use **Bold Text** or `**Section Name:**` for headings
   - ALWAYS use # symbols for ALL section headings
   - Example structure:
     ```
     # Article Title
     ## Introduction
     ## Prerequisites  
     ## Implementation Steps
     ### Step 1: First Task
     ### Step 2: Second Task
     ## Troubleshooting
     ## Conclusion
     ```
   - Include numbered lists (1. 2. 3.) and bullet points (- item)
   - For long articles, create 8-12 main sections using ##

4. PROFESSIONAL QUALITY (ENTERPRISE-GRADE):
   - Write for immediate publication - no drafts or placeholders
   - Include specific, actionable steps with clear outcomes
   - Use professional technical language appropriate for IT environments
   - Provide complete, usable information - no generic placeholders
   - Include relevant command examples, file paths, and configuration details
   - Add security considerations and compliance notes where relevant

🚨 ABSOLUTE REQUIREMENTS:
- Generate ONLY the final markdown article - no meta-commentary, no word counts, no process notes
- Write COMPREHENSIVE content - err on the side of too much detail rather than too little
- Keep writing until you reach the target word count - add more sections if needed
- Include extensive examples, detailed troubleshooting, and comprehensive coverage
- NEVER include word count at the end or mention article length in the content
- For longer articles, be expansive - include everything the reader might need
"""


class Mode6:
    """KB Article Generation - Creates structured knowledge base articles from scratch using single LLM call."""

    async def generate_article(
        self,
        title: str,
        description: str,
        keywords: Optional[Union[list[str], str]] = None,
        length_mode: str = 'medium',
        audience: Optional[str] = None
    ) -> str:
        """Generate a complete knowledge article from scratch using a single LLM call.
        
        Args:
            title: Article title
            description: Article description  
            keywords: List of keywords or comma-separated string
            length_mode: Length setting (short/medium/long/very_long)
            audience: Target audience (optional)
            
        Returns:
            Raw Markdown string
        """
        # Validate length mode
        if length_mode not in LENGTH_RANGES:
            raise ValueError(f"Invalid length_mode '{length_mode}'. Must be one of: {', '.join(LENGTH_RANGES.keys())}")
        
        # Process keywords
        if isinstance(keywords, str):
            keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
        elif keywords is None:
            keywords_list = []
        else:
            keywords_list = keywords
            
        # Build user prompt with all inputs
        user_prompt = self._build_user_prompt(
            title=title,
            description=description, 
            keywords=keywords_list,
            length_mode=length_mode,
            audience=audience
        )
        
        # Get target word counts
        min_words, max_words = LENGTH_RANGES[length_mode]
        target_words = int((min_words + max_words) / 2)
        
        # Strategy: Generate with generous token limit and retry if too short
        max_attempts = 3
        markdown = None
        
        for attempt in range(max_attempts):
            # Generate article
            temp_markdown = await generate_kag(
                system_prompt=KNOWLEDGE_ARTICLE_SYSTEM_PROMPT,
                user_message=user_prompt,
                temperature=0.4 + (attempt * 0.1),  # Increase temperature slightly on retries for more content
                max_tokens=self._get_max_tokens_for_length(length_mode)
            )
            
            current_words = len(temp_markdown.split())
            
            # If within acceptable range, use it
            if min_words <= current_words <= max_words:
                markdown = temp_markdown
                break
            
            # If we got good length, use it
            if current_words >= min_words * 0.85:  # At least 85% of minimum
                markdown = temp_markdown
                
                # Try one expansion if still a bit short
                if current_words < min_words:
                    expanded = await self._expand_article(temp_markdown, min_words, max_words, length_mode)
                    expanded_words = len(expanded.split())
                    if expanded_words >= min_words:
                        markdown = expanded
                break
            
            # If too short and not last attempt, try again with modified prompt
            if attempt < max_attempts - 1:
                user_prompt = self._build_user_prompt(
                    title=title,
                    description=description + f" Provide comprehensive, detailed coverage with multiple examples and extensive explanations.",
                    keywords=keywords_list,
                    length_mode=length_mode,
                    audience=audience
                )
        
        # If still no good result, use what we have and try expansion
        if markdown is None:
            markdown = temp_markdown
            if len(markdown.split()) < min_words * 0.85:
                markdown = await self._expand_article(markdown, min_words, max_words, length_mode)
        
        # Clean up any word count mentions the AI might have added
        markdown = self._clean_article_output(markdown)
        
        return markdown.strip()

    def _build_user_prompt(
        self,
        title: str,
        description: str,
        keywords: list[str],
        length_mode: str,
        audience: Optional[str]
    ) -> str:
        """Build user prompt dynamically from inputs with strict length requirements."""
        
        # Get length configuration
        min_words, max_words = LENGTH_RANGES[length_mode]
        target_words = int((min_words + max_words) / 2)  # Calculate target midpoint
        
        # Format keywords
        keywords_str = ', '.join(keywords) if keywords else 'None provided'
        
        # Format audience
        audience_str = audience or 'General technical audience'
        
        # Add length-specific content guidance
        length_guidance = {
            'short': 'Focus on essential steps only. Be concise but complete. Include: Introduction, Prerequisites, Main Steps, Validation.',
            'medium': 'Include detailed steps, common issues, and validation. Add examples and troubleshooting. Sections: Introduction, Prerequisites, Detailed Steps (with substeps), Examples, Troubleshooting, Validation, Conclusion.',
            'long': 'Provide comprehensive coverage with prerequisites, detailed procedures, multiple examples, extensive troubleshooting, best practices, and validation steps. Include background context and advanced scenarios. Sections: Introduction, Background, Prerequisites, Detailed Implementation Steps, Multiple Examples, Common Issues & Troubleshooting, Best Practices, Security/Performance Considerations, Validation Steps, Related Topics, Conclusion.',
            'very_long': 'Create exhaustive documentation with full background, multiple approaches, detailed examples, comprehensive troubleshooting, security considerations, compliance notes, best practices, FAQ section, and related resources. Sections: Executive Summary, Introduction, Background & Context, Prerequisites & Requirements, Detailed Step-by-Step Implementation, Multiple Real-World Examples, Advanced Scenarios, Comprehensive Troubleshooting Guide, Best Practices, Security Considerations, Performance Optimization, Compliance & Governance, Validation & Testing, FAQ, Related Resources, Conclusion.'
        }
        
        return f"""🎯 ARTICLE GENERATION REQUEST

📝 TITLE: {title}

📄 DESCRIPTION:
{description}

🔑 KEYWORDS: {keywords_str}

👥 TARGET AUDIENCE: {audience_str}

📏 STRICT LENGTH REQUIREMENTS:
- Length Mode: {length_mode.upper()}
- Target Word Count: {target_words} words (THIS IS MANDATORY - COUNT AS YOU WRITE)
- Acceptable Range: {min_words}-{max_words} words
- YOU MUST HIT THIS TARGET: Write until you reach {target_words} words

📦 CONTENT SCOPE FOR {length_mode.upper()}:
{length_guidance[length_mode]}

🚨 CRITICAL LENGTH ENFORCEMENT:
- Write content until you reach EXACTLY {target_words} words
- If you're short, add more examples, details, troubleshooting, or best practices
- If you're over, you've failed - stay within {max_words} words maximum
- Check your word count multiple times as you write
- For {length_mode} articles, you MUST provide substantial, detailed content

✅ DELIVERABLE:
Generate a {target_words}-word professional knowledge base article that provides complete, actionable guidance and meets the exact word count requirement."""

    def _get_max_tokens_for_length(self, length_mode: str) -> int:
        """Get appropriate max tokens based on length mode."""
        _, max_words = LENGTH_RANGES[length_mode]
        # Convert words to tokens (rough estimate: 1 word = 1.3 tokens) with buffer
        return int(max_words * 1.3 * 1.4)
    
    async def _expand_article(self, markdown: str, min_words: int, max_words: int, length_mode: str) -> str:
        """Expand an article that's too short by adding more content."""
        current_words = len(markdown.split())
        target_words = int((min_words + max_words) / 2)
        needed_words = target_words - current_words
        
        expansion_prompt = f"""Expand this knowledge article from {current_words} to approximately {target_words} words.

REQUIREMENTS:
- Add {needed_words} more words of valuable content
- Expand existing sections with more details, examples, and explanations
- Add new relevant sections like: Advanced Scenarios, Common Mistakes, Security Considerations, Performance Tips, Related Resources
- Maintain the same professional tone and structure
- Keep all existing content and headings
- DO NOT add word counts or meta-commentary

Current article:
{markdown}

Expanded version ({target_words} words):"""
        
        expanded = await generate_kag(
            system_prompt="You are expanding a knowledge article. Add substantial, useful content while maintaining professional quality. Output only the enhanced article - no word counts or commentary.",
            user_message=expansion_prompt,
            temperature=0.4,
            max_tokens=self._get_max_tokens_for_length(length_mode)
        )
        
        return expanded
    
    def _clean_article_output(self, markdown: str) -> str:
        """Remove any word count mentions or meta-commentary that the AI might add, and fix heading format."""
        import re
        
        # Remove lines that mention word count
        lines = markdown.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines that contain word count mentions
            if re.search(r'\bword count\b|\bwords?\s*:\s*\d+|\d+\s*words?\b', line.lower()):
                continue
            # Skip lines that look like meta-commentary about the article
            if re.search(r'this article (contains|has|is)', line.lower()):
                continue
            cleaned_lines.append(line)
        
        markdown = '\n'.join(cleaned_lines)
        
        # Fix heading format: Convert **Title:** to proper markdown headings
        # Pattern: Line starts with **Text** or **Text:**
        lines = markdown.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Check if line is a bold heading (starts with ** and ends with ** or **:)
            if re.match(r'^\*\*([^*]+)\*\*:?\s*$', stripped):
                # Extract the heading text
                heading_match = re.match(r'^\*\*([^*]+)\*\*:?\s*$', stripped)
                heading_text = heading_match.group(1).strip()
                
                # Determine heading level based on context
                # If it's the first line or looks like a title, make it H1
                if i == 0 or heading_text.istitle() and len(heading_text) > 20:
                    fixed_lines.append(f'# {heading_text}')
                # If previous line was H1 or empty, likely a main section (H2)
                elif i > 0 and (not lines[i-1].strip() or lines[i-1].strip().startswith('#')):
                    fixed_lines.append(f'## {heading_text}')
                # Otherwise H3
                else:
                    fixed_lines.append(f'### {heading_text}')
            else:
                fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

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
async def process_kb_article(header: str, body: str) -> str:
    """Legacy interface - generates article and returns markdown only."""
    mode6 = Mode6()
    return await mode6.generate_article(
        title=header,
        description=body,
        keywords=None,
        length_mode='medium'
    )