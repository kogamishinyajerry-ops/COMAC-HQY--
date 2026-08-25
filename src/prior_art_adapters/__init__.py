"""Phase A prior art adapter 统一入口。

3 个 adapter 共用同一签名,loader 端从 ADAPTERS registry 拿。
"""
from __future__ import annotations

from typing import Type

from .base import (
    AdapterError,
    BaseAdapter,
    PriorArtQuery,
    PriorArtRecord,
)
from .epo_ops import EPOOpsAdapter
from .google_patents_playwright import GooglePatents_playwrightAdapter
from .normalize_record import ensure_db_safe, resolve_overlap, to_db_dict
from .uspto_opendata import USPTOOpenDataAdapter


ADAPTERS: dict[str, Type[BaseAdapter]] = {
    USPTOOpenDataAdapter.source_id: USPTOOpenDataAdapter,
    EPOOpsAdapter.source_id: EPOOpsAdapter,
    GooglePatents_playwrightAdapter.source_id: GooglePatents_playwrightAdapter,
}


def all_adapters() -> list[BaseAdapter]:
    return [cls() for cls in ADAPTERS.values()]


__all__ = [
    "AdapterError",
    "BaseAdapter",
    "PriorArtQuery",
    "PriorArtRecord",
    "ADAPTERS",
    "all_adapters",
    "USPTOOpenDataAdapter",
    "EPOOpsAdapter",
    "GooglePatents_playwrightAdapter",
    "ensure_db_safe",
    "resolve_overlap",
    "to_db_dict",
]