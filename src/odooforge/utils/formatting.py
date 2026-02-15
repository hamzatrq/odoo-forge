"""Response formatting utilities for tool outputs."""

from __future__ import annotations

from typing import Any


def format_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Format data as a Markdown table."""
    if not rows:
        return "_No data_"

    # Calculate column widths
    str_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    # Build table
    header_line = "| " + " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "|" + "|".join("-" * (w + 2) for w in widths) + "|"

    data_lines = []
    for row in str_rows:
        padded = []
        for i, cell in enumerate(row):
            w = widths[i] if i < len(widths) else len(cell)
            padded.append(cell.ljust(w))
        data_lines.append("| " + " | ".join(padded) + " |")

    return "\n".join([header_line, sep_line, *data_lines])


def format_record(record: dict, title: str = "") -> str:
    """Format a single record as a readable block."""
    lines = []
    if title:
        lines.append(f"### {title}")
    for key, value in record.items():
        if isinstance(value, list) and len(value) > 5:
            value = f"[{len(value)} items]"
        lines.append(f"- **{key}**: {value}")
    return "\n".join(lines)


def format_records(records: list[dict], title: str = "", limit: int = 20) -> str:
    """Format multiple records with pagination info."""
    lines = []
    if title:
        lines.append(f"### {title}")

    total = len(records)
    shown = records[:limit]

    if not shown:
        return f"{title}\n_No records found_" if title else "_No records found_"

    # Use first record's keys as headers
    headers = list(shown[0].keys())
    rows = [[record.get(h, "") for h in headers] for record in shown]
    lines.append(format_table(headers, rows))

    if total > limit:
        lines.append(f"\n_Showing {limit} of {total} records. Use offset to see more._")

    return "\n".join(lines)


def truncate(text: str, max_length: int = 2000) -> str:
    """Truncate text with an indicator."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n\n... (truncated, {len(text) - max_length} more characters)"
