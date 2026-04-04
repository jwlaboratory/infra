"""Load Codeforces-style official_tests payloads (JSON or Python literal)."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any


class TestsParseError(ValueError):
    pass


def parse_tests_payload(raw: str) -> list[dict[str, str]]:
    """
    Accepts:
      - JSON array of objects or a single object with input/output keys
      - Python literal (list/dict) compatible with ast.literal_eval
    """
    raw = raw.strip()
    if not raw:
        return []

    items = _try_parse_json(raw)
    if items is None:
        items = _try_parse_literal(raw)

    if items is None:
        raise TestsParseError("Unable to parse tests payload as JSON or Python literal.")

    if isinstance(items, dict):
        items = [items]

    if not isinstance(items, list):
        raise TestsParseError("Tests payload must be a list or a single object.")

    tests: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        tests.append(
            {
                "input": str(item.get("input", "")),
                "output": str(item.get("output", "")),
            }
        )
    return tests


def parse_tests_file(path: Path) -> list[dict[str, str]]:
    return parse_tests_payload(path.read_text(encoding="utf-8"))


def _try_parse_json(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _try_parse_literal(raw: str) -> Any | None:
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return None
