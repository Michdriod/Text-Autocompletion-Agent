"""
Mode 6 - Sectional Generation Strategy
Generates articles section-by-section for better length control
"""
from typing import Optional, Union, List, Dict
import re
from utils.kag_generator import generate_kag
from config.settings import LENGTH_RANGES

OUTLINE_SYSTEM_PROMPT = """You are creating an outline for a knowledge base article.
Generate a clear, logical outline with 6-10 main sections.
Format: Return ONLY section names, one per line, no numbers or bullets.
Example output:
Introduction
Prerequisites
Step-by-Step Implementation
Configuration
Troubleshooting
Best Practices
Conclusion"""

SECTION_SYSTEM_PROMPT = """You are writing ONE SECTION of a knowledge base article.
Write comprehensive, detailed content for this specific section.
Use proper markdown with headings, lists, code blocks, and examples.
Be thorough and professional. Include specific details and actionable guidance."""


class Mode6Sectional:
    """Generates KB articles section-by-section for precise length control."""
    
    async def generate_article(
        self,
        title: str,
        description: str,
        keywords: Optional[Union[list[str], str]] = None,
        length_mode: str = 'medium',
        audience: Optional[str] = None
    ) -> str:
        """Generate article section-by-section with optimizations."""
        
        # Validate and process inputs
        if length_mode not in LENGTH_RANGES:
            raise ValueError(f"Invalid length_mode: {length_mode}")
        
        if isinstance(keywords, str):
            keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
        elif keywords is None:
            keywords_list = []
        else:
            keywords_list = keywords
        
        # Get target lengths
        min_words, max_words = LENGTH_RANGES[length_mode]
        target_words = int((min_words + max_words) / 2)
        
        # OPTIMIZATION 1: Use predefined outlines for common patterns to skip outline generation
        sections = self._get_smart_outline(title, description, length_mode)
        
        # OPTIMIZATION 2: Calculate words per section
        words_per_section = target_words // len(sections)
        
        # OPTIMIZATION 3: Generate multiple sections in parallel batches
        article_parts = [f"# {title}\n"]
        
        # Batch sections for parallel generation
        import asyncio
        batch_size = 3  # Generate 3 sections at a time
        
        for batch_start in range(0, len(sections), batch_size):
            batch_end = min(batch_start + batch_size, len(sections))
            batch_sections = sections[batch_start:batch_end]
            
            # Create tasks for parallel generation
            tasks = []
            for i, section_name in enumerate(batch_sections):
                actual_index = batch_start + i
                
                # Adjust word targets
                if actual_index == 0:  # Introduction
                    section_target = int(words_per_section * 0.8)
                elif actual_index == len(sections) - 1:  # Conclusion
                    section_target = int(words_per_section * 0.7)
                else:
                    section_target = int(words_per_section * 1.1)
                
                task = self._generate_section(
                    section_name,
                    title,
                    description,
                    keywords_list,
                    section_target,
                    actual_index == 0,  # is_intro
                    audience
                )
                tasks.append((section_name, task))
            
            # Wait for batch to complete
            results = await asyncio.gather(*[task for _, task in tasks])
            
            # Add results to article
            for (section_name, _), content in zip(tasks, results):
                article_parts.append(f"\n## {section_name}\n\n{content}")
        
        # Combine all parts
        full_article = '\n'.join(article_parts)
        
        # Clean up
        full_article = self._clean_output(full_article)
        
        return full_article.strip()
    
    def _get_smart_outline(self, title: str, description: str, length_mode: str) -> List[str]:
        """Generate outline using predefined templates or simple logic (skip LLM call)."""
        
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # Detect article type and use predefined structures
        if 'install' in title_lower or 'setup' in title_lower or 'configure' in title_lower:
            # Installation/Setup guide
            outline = [
                'Introduction',
                'Prerequisites',
                'Installation Steps',
                'Configuration',
                'Verification',
                'Troubleshooting',
                'Best Practices',
                'Conclusion'
            ]
        elif 'troubleshoot' in title_lower or 'debug' in title_lower or 'fix' in title_lower:
            # Troubleshooting guide
            outline = [
                'Introduction',
                'Problem Overview',
                'Root Cause Analysis',
                'Solution Steps',
                'Verification',
                'Prevention',
                'Additional Resources',
                'Conclusion'
            ]
        elif 'workflow' in title_lower or 'process' in title_lower or 'onboarding' in title_lower:
            # Process/Workflow guide
            outline = [
                'Introduction',
                'Overview',
                'Prerequisites',
                'Step-by-Step Workflow',
                'Key Responsibilities',
                'Common Issues',
                'Best Practices',
                'Validation',
                'Conclusion'
            ]
        elif 'security' in title_lower or 'authentication' in title_lower or 'authorization' in title_lower:
            # Security guide
            outline = [
                'Introduction',
                'Security Overview',
                'Prerequisites',
                'Implementation Steps',
                'Configuration',
                'Testing',
                'Best Practices',
                'Conclusion'
            ]
        elif 'migration' in title_lower or 'upgrade' in title_lower:
            # Migration/Upgrade guide
            outline = [
                'Introduction',
                'Planning and Assessment',
                'Prerequisites',
                'Migration Steps',
                'Validation',
                'Rollback Procedures',
                'Post-Migration Tasks',
                'Troubleshooting',
                'Conclusion'
            ]
        else:
            # Generic guide
            outline = [
                'Introduction',
                'Background',
                'Prerequisites',
                'Implementation',
                'Configuration',
                'Validation',
                'Troubleshooting',
                'Best Practices',
                'Conclusion'
            ]
        
        # Adjust number of sections based on length
        section_count = {
            'short': 5,
            'medium': 7,
            'long': 9,
            'very_long': 11
        }[length_mode]
        
        # Trim or extend outline to match target
        if len(outline) > section_count:
            # Keep intro, conclusion, and most important middle sections
            outline = [outline[0]] + outline[2:section_count-1] + [outline[-1]]
        elif len(outline) < section_count:
            # Add common sections
            extra_sections = ['Advanced Configuration', 'Performance Optimization', 'Security Considerations', 'FAQ']
            outline = outline[:-1] + extra_sections[:section_count - len(outline)] + [outline[-1]]
        
        return outline[:section_count]
    
    async def _generate_outline(
        self,
        title: str,
        description: str,
        keywords: List[str],
        length_mode: str
    ) -> List[str]:
        """Generate article outline."""
        
        section_count = {
            'short': 5,
            'medium': 7,
            'long': 9,
            'very_long': 11
        }[length_mode]
        
        outline_prompt = f"""Create an outline for this article:

Title: {title}
Description: {description}
Keywords: {', '.join(keywords)}

Generate exactly {section_count} section names that logically cover this topic.
Return ONLY the section names, one per line, no formatting."""
        
        outline_text = await generate_kag(
            system_prompt=OUTLINE_SYSTEM_PROMPT,
            user_message=outline_prompt,
            temperature=0.3,
            max_tokens=500
        )
        
        # Parse sections
        sections = [
            line.strip().lstrip('0123456789.-) ').strip()
            for line in outline_text.strip().split('\n')
            if line.strip() and len(line.strip()) > 3
        ]
        
        # Ensure we have good sections
        if len(sections) < 4:
            sections = [
                'Introduction',
                'Prerequisites',
                'Implementation Steps',
                'Troubleshooting',
                'Best Practices',
                'Conclusion'
            ][:section_count]
        
        return sections[:section_count]
    
    async def _generate_section(
        self,
        section_name: str,
        article_title: str,
        description: str,
        keywords: List[str],
        target_words: int,
        is_intro: bool,
        audience: Optional[str]
    ) -> str:
        """Generate content for one section with optimized prompts."""
        
        audience_str = audience or "technical users"
        
        # OPTIMIZATION: Shorter, more focused prompts = fewer tokens
        if is_intro:
            section_prompt = f"""Introduction for: {article_title}

Context: {description}
Audience: {audience_str}
Length: ~{target_words} words

Write a professional introduction that explains what this article covers, why it matters, and what readers will learn."""
        else:
            # Simplified prompt for other sections
            section_prompt = f"""Section: {section_name}

Article: {article_title}
Keywords: {', '.join(keywords[:5])}  # Limit keywords
Length: ~{target_words} words

Write detailed, actionable content for this section. Include specific steps, examples, and professional guidance."""
        
        content = await generate_kag(
            system_prompt=SECTION_SYSTEM_PROMPT,
            user_message=section_prompt,
            temperature=0.4,
            max_tokens=int(target_words * 1.5)  # Reduced from 2x to 1.5x
        )
        
        # Remove any section headings the AI might add
        lines = content.strip().split('\n')
        cleaned_lines = []
        skip_first_heading = True
        
        for line in lines:
            # Skip the first heading if it matches the section name
            if skip_first_heading and line.strip().startswith('#'):
                skip_first_heading = False
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _clean_output(self, markdown: str) -> str:
        """Clean up the output."""
        # Remove word count mentions
        lines = markdown.split('\n')
        cleaned = []
        
        for line in lines:
            if re.search(r'\bword count\b|\d+\s*words?\b', line.lower()):
                continue
            cleaned.append(line)
        
        markdown = '\n'.join(cleaned)
        
        # Convert any **Bold Headings** to proper markdown
        lines = markdown.split('\n')
        fixed = []
        
        for line in lines:
            if re.match(r'^\*\*([^*]+)\*\*:?\s*$', line.strip()):
                heading = re.match(r'^\*\*([^*]+)\*\*:?\s*$', line.strip()).group(1)
                fixed.append(f"### {heading}")
            else:
                fixed.append(line)
        
        return '\n'.join(fixed)


# Legacy compatibility
async def process_kb_article(header: str, body: str) -> str:
    """Legacy interface."""
    mode6 = Mode6Sectional()
    return await mode6.generate_article(
        title=header,
        description=body,
        keywords=None,
        length_mode='medium'
    )
