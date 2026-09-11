"""
Gemini-backed structured LLM client used by the verification pipeline.

VERITAS_SPEC.md Part 4.3 requires "LLM output must be structured JSON. Use
Anthropic's tool-use for schema-enforced output. Never accept free-form."
The prompts.py schemas (CLASSIFY_BATCH_TOOL, RENDER_VERDICT_TOOL, ...) are
therefore written as Anthropic tool_use `input_schema` dicts, copied
verbatim from the spec. This build's available LLM credential is a Gemini
API key rather than an Anthropic one, so this module adapts those same
schemas to Gemini's structured-output API (response_mime_type +
response_schema) instead of Anthropic's tool-use -- the schema-enforced,
never-free-form guarantee is the same; only the wire format differs.
"""
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and fill it in."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def to_gemini_schema(schema: Any) -> Any:
    """Recursively convert an Anthropic tool_use input_schema (as used in
    prompts.py) into the OpenAPI-subset schema Gemini's response_schema
    expects. Two incompatibilities are fixed here:
    (1) Anthropic's union-typed optional fields, e.g.
        {"type": ["string", "null"]}, become {"type": "STRING", "nullable": true};
    (2) Gemini's `type` values are upper-cased (STRING/OBJECT/ARRAY/...),
        not JSON Schema's lower-case (string/object/array/...)."""
    if isinstance(schema, dict):
        converted: dict[str, Any] = {}
        type_value = schema.get("type")
        if isinstance(type_value, list):
            non_null_types = [t for t in type_value if t != "null"]
            resolved_type = non_null_types[0] if non_null_types else "string"
            converted["type"] = resolved_type.upper()
            if "null" in type_value:
                converted["nullable"] = True
        elif isinstance(type_value, str):
            converted["type"] = type_value.upper()
        for key, value in schema.items():
            if key == "type":
                continue
            converted[key] = to_gemini_schema(value)
        return converted
    if isinstance(schema, list):
        return [to_gemini_schema(item) for item in schema]
    return schema


def call_structured(
    system_prompt: str,
    user_prompt: str,
    input_schema: dict,
    model: str | None = None,
) -> dict:
    """Call Gemini with a system + user prompt, constrained to return JSON
    matching `input_schema` (an Anthropic tool_use input_schema dict from
    prompts.py, e.g. CLASSIFY_BATCH_TOOL["input_schema"]). Returns the
    parsed JSON response as a plain dict."""
    client = get_client()
    response = client.models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=to_gemini_schema(input_schema),
        ),
    )
    return json.loads(response.text)
