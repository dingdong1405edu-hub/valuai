import json
import os
import re
from typing import Any

from openai import OpenAI

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_groq_client() -> OpenAI:
    return OpenAI(api_key=GROQ_API_KEY, base_url=_GROQ_BASE_URL)


def build_prompt(default_preamble: str, schema_block: str,
                 ctx: dict, override: str = "") -> str:
    preamble = override.strip() if override and override.strip() else default_preamble
    try:
        filled = preamble.format(**ctx)
    except KeyError:
        filled = preamble
    return f"{filled}\n\n{schema_block}"


def with_locked_schema(default_full_prompt: str,
                        schema_sentinel: str,
                        override: str = "") -> str:
    if schema_sentinel in default_full_prompt:
        before_sentinel, after_sentinel = default_full_prompt.split(schema_sentinel, 1)
    else:
        before_sentinel = default_full_prompt
        after_sentinel = ""

    if override and override.strip():
        preamble = override.strip()
    else:
        preamble = before_sentinel.strip()

    if after_sentinel:
        return f"{preamble}\n\n{schema_sentinel}{after_sentinel}"
    return preamble


def parse_json_response(raw: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def extract_text_from_message(message) -> str:
    """Extract text content from OpenAI/Groq response."""
    if hasattr(message, "choices") and message.choices:
        return message.choices[0].message.content or ""
    # Legacy Anthropic format fallback
    parts = []
    for block in getattr(message, "content", []):
        if hasattr(block, "type") and block.type == "text":
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts)
