from __future__ import annotations

import re
from typing import Iterable


def normalize_cpc(code: str) -> str:
    value = re.sub(r"\s+", "", str(code or "").upper())
    value = value.replace("–", "-").replace("—", "-")
    return value


def normalize_publication_number(value: str) -> str:
    return re.sub(r"[^0-9A-Z]", "", str(value or "").upper())


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").casefold()).strip()


def unique_normalized(values: Iterable[str], normalizer=normalize_text) -> list[str]:
    return list(dict.fromkeys(normalizer(value) for value in values if normalizer(value)))
