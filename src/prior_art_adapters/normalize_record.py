"""跨源 record 归一与冲突解决工具。

Phase A 跨源同号 dedup 策略:
- 首次入库:is_primary=1,source_id = adapter.source_id
- 跨源重号:不在 prior_art_patents 改 source_id,只往桥表 append is_primary=0
- 字段冲突解决:日期取最晚、abstract 取最长、assignees 取并集去重
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Iterable

from .base import PriorArtRecord


# 复用治理模块现有的归一函数,避免重复实现
from src.governance.normalize import (  # noqa: E402
    normalize_cpc,
    normalize_publication_number,
)


# ============================================================
# 单 record 字段归一(adapter 输出 record 后走一次确保 schema-clean)
# ============================================================

def ensure_db_safe(record: PriorArtRecord) -> PriorArtRecord:
    """校验 record 满足 db schema,失败抛 ValueError。"""
    if not record.publication_number or len(record.publication_number) < 5:
        raise ValueError(f"invalid publication_number: {record.publication_number!r}")
    if not record.country_code or len(record.country_code) != 2:
        raise ValueError(f"invalid country_code: {record.country_code!r}")
    if not record.filing_date or not _is_iso_date(record.filing_date):
        raise ValueError(f"invalid filing_date: {record.filing_date!r}")
    if not record.publication_date or not _is_iso_date(record.publication_date):
        raise ValueError(f"invalid publication_date: {record.publication_date!r}")
    # cpc_codes 必须 JSON valid(governance prior_art_cpc_json 卡 json_valid=0)
    try:
        json.dumps(list(record.cpc_codes))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"cpc_codes not JSON serializable: {exc}")
    return record


def _is_iso_date(s: str) -> bool:
    """宽松的 YYYY-MM-DD 校验(也接受 YYYYMMDD 自动转换)。"""
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        try:
            datetime.strptime(s, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    if re.match(r"^\d{8}$", s):
        try:
            datetime.strptime(s, "%Y%m%d")
            return True
        except ValueError:
            return False
    return False


# ============================================================
# 跨源同号字段冲突解决
# ============================================================

def resolve_overlap(records: Iterable[PriorArtRecord]) -> PriorArtRecord:
    """同 publication_number 跨源 records 合并为 1 个 record。

    决策规则(plan §3.2):
    - title_en / title_zh: 取最长
    - abstract_en / abstract_zh: 取最长
    - filing_date / publication_date: 取最晚(信息更全)
    - grant_date: 优先非空
    - assignees / inventors: 并集去重
    - cpc_codes: 并集去重
    - family_id: 优先非空
    - source_id: 取第一个(主源语义,实际 loader 决定)
    - raw_url / raw_payload_sha256: 取最后一个(最新响应)
    """
    records = list(records)
    if not records:
        raise ValueError("resolve_overlap called with empty iterable")
    if len(records) == 1:
        return records[0]

    title_en = max((r.title_en for r in records), key=len, default="")
    title_zh = max((r.title_zh for r in records), key=len, default="")
    abstract_en = max((r.abstract_en for r in records), key=len, default="")
    abstract_zh = max((r.abstract_zh for r in records), key=len, default="")

    def _later(a: str, b: str) -> str:
        return a if a >= b else b

    filing_date = records[0].filing_date
    publication_date = records[0].publication_date
    for r in records[1:]:
        filing_date = _later(filing_date, r.filing_date)
        publication_date = _later(publication_date, r.publication_date)

    grant_date = next((r.grant_date for r in records if r.grant_date), None)
    family_id = next((r.family_id for r in records if r.family_id), None)

    assignees = tuple(sorted({a for r in records for a in r.assignees}))
    inventors = tuple(sorted({i for r in records for i in r.inventors}))
    cpc_codes = tuple(sorted({normalize_cpc(c) for r in records for c in r.cpc_codes}))

    last = records[-1]
    first = records[0]
    return PriorArtRecord(
        publication_number=first.publication_number,
        country_code=first.country_code,
        title_zh=title_zh,
        title_en=title_en,
        abstract_zh=abstract_zh,
        abstract_en=abstract_en,
        cpc_codes=cpc_codes,
        inventors=inventors,
        assignees=assignees,
        filing_date=filing_date,
        publication_date=publication_date,
        grant_date=grant_date,
        family_id=family_id,
        raw_url=last.raw_url,
        raw_payload_sha256=last.raw_payload_sha256,
        source_id=first.source_id,
    )


# ============================================================
# 数据库写入前 normalize(loader 调)
# ============================================================

def to_db_dict(record: PriorArtRecord) -> dict:
    """PriorArtRecord → dict,值已 JSON 安全。"""
    return {
        "publication_number": normalize_publication_number(record.publication_number),
        "country_code": record.country_code.upper(),
        "title_zh": record.title_zh or "[EN-only]",
        "title_en": record.title_en or "[ZH-only]",
        "abstract_zh": record.abstract_zh or "[EN-only]",
        "abstract_en": record.abstract_en or "[ZH-only]",
        "cpc_codes": json.dumps(list(record.cpc_codes), ensure_ascii=False),
        "inventors": json.dumps(list(record.inventors), ensure_ascii=False),
        "assignees": json.dumps(list(record.assignees), ensure_ascii=False),
        "filing_date": record.filing_date,
        "publication_date": record.publication_date,
        "grant_date": record.grant_date,
        "family_id": record.family_id,
        "source_id": record.source_id,
        "checked_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "disclaimer_zh": _default_disclaimer_zh(record.source_id),
        "raw_url": record.raw_url,
        "raw_payload_sha256": record.raw_payload_sha256,
    }


def _default_disclaimer_zh(source_id: str) -> str:
    """按 source_id 返回 disclaimer_zh,governance 17 守卫 source_license_and_boundaries 要求非空。"""
    base = "先有技术检索辅助,不构成新颖性、创造性、自由实施或侵权法律意见。"
    if "google" in source_id:
        return base + " Google Patents 数据受 ToS 约束,仅作工程检索,违反 ToS 风险由调用方承担。"
    return base