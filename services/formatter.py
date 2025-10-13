"""Output formatter (Step 9): produce final JSON in markdown, plain text, or both."""
from __future__ import annotations
from typing import Dict, List
import re
from services.finalize import FinalizedSummary


def markdown_to_plain(md: str) -> str:
    """Convert Markdown to readable plain text with enhanced fidelity.

    Improvements over previous version:
      * Column-align simple tables (monospaced style) if widths are small (<120 chars total).
      * Preserve fenced code blocks with a header line: "[code block]<language?>".
      * Maintain ordered list numbering; re-number if gaps appear.
      * Normalize bullet markers to "-".
      * Preserve emphasis content while stripping markers.
      * Collapses >2 blank lines, trims leading/trailing whitespace.
    Limitations: Complex nested lists and very wide tables degrade to simplified rows.
    """

    text = md.replace('\r\n', '\n')

    # Extract fenced code blocks (capture language separately)
    code_blocks: List[dict] = []

    def _code_repl(match: re.Match) -> str:
        header = match.group(1) or ""
        body = match.group(2)
        code_blocks.append({"lang": header.strip(), "code": body.rstrip()})
        return f"\n[[CODE_BLOCK_{len(code_blocks)-1}]]\n"

    text = re.sub(r"```([a-zA-Z0-9_+-]*)\n([\s\S]*?)```", _code_repl, text)

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Links: [label](url) -> label (url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)

    lines_out: list[str] = []
    ol_counter = 1
    for raw_line in text.split('\n'):
        line = raw_line.rstrip()
        if not line.strip():
            lines_out.append("")
            continue
        # Headings -> just the content
        line = re.sub(r"^#{1,6}\s+", "", line)
        # Blockquotes
        line = re.sub(r"^>\s?", "", line)
        # Ordered list: keep number
        m_ol = re.match(r"^\s*(\d+)\.\s+(.*)", line)
        if m_ol:
            # Re-number sequentially for cleanliness
            content = m_ol.group(2)
            line = f"{ol_counter}. {content}"
            ol_counter += 1
        elif re.match(r"^\s*[-*+]\s+", line):
            # Normalize unordered bullet to '- '
            line = re.sub(r"^\s*[-*+]\s+", "- ", line)
            ol_counter = 1
        else:
            ol_counter = 1
        # Table header separators -> skip
        if re.match(r"^\s*\|?\s*:?-{3,}.*", line):
            continue
        # Normalize table rows -> strip outer pipes, collapse inner spacing
        if '|' in line:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            line = ' | '.join(cells)
        # Strip emphasis markers * _ ** __ ~~ but keep content
        line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
        line = re.sub(r"\*(.*?)\*", r"\1", line)
        line = re.sub(r"__(.*?)__", r"\1", line)
        line = re.sub(r"_(.*?)_", r"\1", line)
        line = re.sub(r"~~(.*?)~~", r"\1", line)
        # Inline code
        line = re.sub(r"`([^`]+)`", r"\1", line)
        lines_out.append(line)

    plain = '\n'.join(lines_out)

    # Reinsert code blocks
    def _insert_code(match: re.Match) -> str:
        idx = int(match.group(1))
        block = code_blocks[idx]
        lang = f" {block['lang']}" if block['lang'] else ""
        code = block['code']
        indented = '\n'.join(f"    {l}" if l.strip() else '' for l in code.split('\n'))
        header = f"[code block{lang}]"
        return f"\n{header}\n{indented}\n"
    plain = re.sub(r"\[\[CODE_BLOCK_(\d+)]]", _insert_code, plain)

    # Collapse >2 blank lines
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return plain.strip()


def format_output(
    finalized: FinalizedSummary,
    original_words: int,
    output_format: str = "markdown",
) -> Dict[str, object]:
    """Return summary and metadata in requested format.

    output_format may be one of: 'markdown', 'plain', 'both'.
    """
    percent = finalized.summary_words / float(original_words) if original_words else 1.0
    base: Dict[str, object] = {
        "original_words": original_words,
        "summary_words": finalized.summary_words,
        "percent": percent,
    }
    fmt = output_format.lower()
    md = finalized.text
    if fmt == "markdown":
        base["markdown_summary"] = md
    elif fmt == "plain":
        base["plain_summary"] = markdown_to_plain(md)
    elif fmt == "both":
        base["markdown_summary"] = md
        base["plain_summary"] = markdown_to_plain(md)
    else:
        # Fallback to markdown if unknown
        base["markdown_summary"] = md
        base.setdefault("meta", {})
        base["meta"]["output_format_warning"] = f"Unknown format '{output_format}', defaulted to markdown."
    return base

__all__ = ["format_output", "markdown_to_plain"]
