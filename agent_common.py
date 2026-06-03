import json
import os
import re
from typing import Any

import anthropic

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

_OPUS_MODEL = "claude-opus-4-7"
_HAIKU_MODEL = "claude-haiku-4-5-20251001"
_THINKING_BETA = "interleaved-thinking-2025-05-14"


def get_anthropic_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _extract_text(response) -> str:
    parts = []
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts)


def call_opus(prompt: str, system: str = "", max_tokens: int = 8000,
              effort: str = "medium") -> str:
    client = get_anthropic_client()
    kwargs: dict = {
        "model": _OPUS_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    try:
        response = client.beta.messages.create(
            betas=[_THINKING_BETA],
            thinking={"type": "adaptive", "effort": effort},
            **kwargs,
        )
    except Exception:
        response = client.messages.create(**kwargs)
    return _extract_text(response)


def call_opus_multimodal(content: list, system: str = "",
                         max_tokens: int = 8000, effort: str = "medium") -> str:
    client = get_anthropic_client()
    kwargs: dict = {
        "model": _OPUS_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}],
    }
    if system:
        kwargs["system"] = system
    try:
        response = client.beta.messages.create(
            betas=[_THINKING_BETA],
            thinking={"type": "adaptive", "effort": effort},
            **kwargs,
        )
    except Exception:
        response = client.messages.create(**kwargs)
    return _extract_text(response)


def call_haiku(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    client = get_anthropic_client()
    kwargs: dict = {
        "model": _HAIKU_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    response = client.messages.create(**kwargs)
    return _extract_text(response)


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

    preamble = override.strip() if override and override.strip() else before_sentinel.strip()

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
