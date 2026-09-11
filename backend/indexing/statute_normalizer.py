"""
Normalizes raw statute JSON files (cpc.json, cpc_orders.json, contract_act.json,
specific_relief_act.json) into SourceChunk objects with uniform metadata.

Input file formats:
- cpc.json: list of {"section": int|str, "title": str, "description": str}
  (Sections 1-158 of the Code of Civil Procedure, 1908 main body.)
- cpc_orders.json: list of {"order": str, "rule": str, "title": str, "description": str}
  (Order/Rule provisions from the First Schedule, hand-curated where the
  primary source dataset does not cover them.)
- contract_act.json / specific_relief_act.json: list of
  {"section": str, "title": str, "description": str, "source_url": str}
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from backend.models.schemas import SourceChunk, SourceType

INDIA_CODE_CPC_URL = "https://www.indiacode.nic.in/handle/123456789/2191"


def _clean_section(raw: str | int) -> str:
    return str(raw).strip().rstrip(".")


def normalize_cpc_sections(path: Path) -> Iterator[SourceChunk]:
    """Yield SourceChunks for the bare-body CPC sections in cpc.json."""
    entries = json.loads(path.read_text())
    for entry in entries:
        section = _clean_section(entry["section"])
        title = entry.get("title", "").strip()
        description = entry.get("description", "").strip()
        text = f"Section {section}. {title}\n\n{description}" if description else f"Section {section}. {title}"
        yield SourceChunk(
            chunk_id=f"cpc-s{section}",
            source_type=SourceType.STATUTE,
            text=text,
            act_name="CPC",
            section_number=section,
            source_url=INDIA_CODE_CPC_URL,
        )


def normalize_cpc_orders(path: Path) -> Iterator[SourceChunk]:
    """Yield SourceChunks for the Order/Rule provisions in cpc_orders.json."""
    entries = json.loads(path.read_text())
    for entry in entries:
        order = entry["order"].strip()
        rule = entry["rule"].strip()
        title = entry.get("title", "").strip()
        description = entry.get("description", "").strip()
        header = f"Order {order} Rule {rule}. {title}"
        text = f"{header}\n\n{description}" if description else header
        yield SourceChunk(
            chunk_id=f"cpc-o{order}-r{rule}",
            source_type=SourceType.STATUTE,
            text=text,
            act_name="CPC",
            order_number=order,
            rule_number=rule,
            source_url=INDIA_CODE_CPC_URL,
        )


def normalize_act_sections(path: Path, act_name: str, chunk_prefix: str) -> Iterator[SourceChunk]:
    """Yield SourceChunks for a flat act file (contract_act.json / specific_relief_act.json)."""
    entries = json.loads(path.read_text())
    for entry in entries:
        section = _clean_section(entry["section"])
        title = entry.get("title", "").strip()
        description = entry.get("description", "").strip()
        source_url = entry.get("source_url")
        text = f"Section {section}. {title}\n\n{description}" if description else f"Section {section}. {title}"
        yield SourceChunk(
            chunk_id=f"{chunk_prefix}-s{section}",
            source_type=SourceType.STATUTE,
            text=text,
            act_name=act_name,
            section_number=section,
            source_url=source_url,
        )


def normalize_all_statutes(statutes_dir: Path) -> list[SourceChunk]:
    """Load every known statute file in statutes_dir and return normalized SourceChunks."""
    chunks: list[SourceChunk] = []

    cpc_path = statutes_dir / "cpc.json"
    if cpc_path.exists():
        chunks.extend(normalize_cpc_sections(cpc_path))

    cpc_orders_path = statutes_dir / "cpc_orders.json"
    if cpc_orders_path.exists():
        chunks.extend(normalize_cpc_orders(cpc_orders_path))

    contract_act_path = statutes_dir / "contract_act.json"
    if contract_act_path.exists():
        chunks.extend(
            normalize_act_sections(contract_act_path, "Contract Act", "ica")
        )

    sra_path = statutes_dir / "specific_relief_act.json"
    if sra_path.exists():
        chunks.extend(
            normalize_act_sections(sra_path, "Specific Relief Act", "sra")
        )

    return chunks
