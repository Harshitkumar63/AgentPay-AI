"""Prompt Injection & Untrusted Data Defense Layer (Phase 16)."""

import re
from typing import Dict, Any, Tuple

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior)\s+rules?",
    r"override\s+(system|policy|security)",
    r"transfer\s+₹?\d+",
    r"set\s+price\s+to\s+0",
    r"100%\s+discount",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"system\s*:\s*admin",
    r"bypass\s+(approval|limit|budget)",
    r"sudo\s+",
    r"act\s+as\s+DAN",
    r"jailbreak",
]


def detect_prompt_injection(text: str) -> Dict[str, Any]:
    """
    Scans user input or product descriptions for prompt injection or system override attempts.
    """
    if not text:
        return {"is_injection": False, "matched_patterns": []}

    cleaned = text.strip()
    matched = []

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            matched.append(pattern)

    is_injection = len(matched) > 0
    return {
        "is_injection": is_injection,
        "matched_patterns": matched,
        "risk_level": "HIGH" if is_injection else "LOW",
        "reason": "UNTRUSTED CONTENT CANNOT MODIFY SYSTEM POLICY: Prompt injection pattern detected." if is_injection else "Safe input.",
    }


def sanitize_untrusted_content(text: str) -> str:
    """
    Sanitizes user input or external merchant text to prevent instruction leakage.
    Wraps text with semantic data delimiters.
    """
    if not text:
        return ""
    # Strip potential control markers
    sanitized = text.replace("```system", "```data").replace("<<SYS>>", "").replace("<|im_start|>", "")
    return sanitized.strip()
