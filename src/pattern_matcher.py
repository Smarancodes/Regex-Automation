"""
pattern_matcher.py - Load regex patterns from JSON and match them against page text.
"""
import json
import re
import logging
import os

logger = logging.getLogger(__name__)


def load_patterns(json_path: str) -> list:
    """
    Load patterns from the JSON config file.

    Expected JSON format:
    {
        "patterns": [
            {"name": "Invoice", "regex": "(?i)invoice ..."},
            ...
        ]
    }

    Returns:
        List of dicts: [{"name": str, "compiled": re.Pattern}, ...]
    """
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"Patterns JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    patterns = []
    for entry in data.get("patterns", []):
        name = entry.get("name", "Unknown")
        regex_str = entry.get("regex", "")
        try:
            compiled = re.compile(regex_str)
            patterns.append({"name": name, "compiled": compiled, "regex": regex_str})
            logger.debug("Loaded pattern '%s': %s", name, regex_str)
        except re.error as exc:
            logger.warning("Skipping pattern '%s' — invalid regex: %s", name, exc)

    logger.info("Loaded %d regex pattern(s) from %s", len(patterns), os.path.basename(json_path))
    return patterns


def match_page(text: str, patterns: list) -> str:
    """
    Match page text against all loaded patterns.

    Returns the NAME of the first matching pattern, or "Unmatched" if none match.
    Matching is first-match wins (patterns are checked in JSON order).
    """
    for pattern in patterns:
        if pattern["compiled"].search(text):
            return pattern["name"]
    return "Unmatched"


def match_all_pages(page_texts: list, patterns: list) -> list:
    """
    Match a list of page-text dicts against all patterns.

    Args:
        page_texts: List of {"page": int, "method": str, "text": str}
        patterns:   List from load_patterns()

    Returns:
        List of {"page": int, "method": str, "text": str, "label": str}
    """
    results = []
    for pt in page_texts:
        label = match_page(pt["text"], patterns)
        results.append({**pt, "label": label})
        logger.info(
            "  Page %3d │ %-8s │ %s",
            pt["page"] + 1,   # 1-indexed for display
            pt["method"],
            label,
        )
    return results
