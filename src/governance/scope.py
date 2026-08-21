from __future__ import annotations

from collections.abc import Iterable

from .normalize import normalize_cpc

CORE_PREFIXES = ("B64D31", "B64D33")
ADJACENT_PREFIXES = ("B60K26", "B60K41", "G05D1", "H01H13", "H01H19", "H01H21")
EXCLUDED_PREFIXES = ("B64D13",)


def classify_cpc(code: str) -> str:
    normalized = normalize_cpc(code)
    if normalized.startswith(EXCLUDED_PREFIXES):
        return "out_of_scope"
    if normalized.startswith(CORE_PREFIXES):
        return "core"
    if normalized.startswith(ADJACENT_PREFIXES):
        return "adjacent"
    return "unknown"


def classify_patent_scope(codes: Iterable[str]) -> str:
    levels = {classify_cpc(code) for code in codes}
    if "core" in levels:
        return "core"
    if "adjacent" in levels:
        return "adjacent"
    if levels and levels <= {"out_of_scope"}:
        return "out_of_scope"
    return "unknown"
