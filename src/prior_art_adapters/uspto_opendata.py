"""USPTO Open Data(PatentsView)adapter。

公开 endpoint: https://api.patentsview.org/patents/query
无需 OAuth,限速建议 60 req/min。
Phase A 字段覆盖:patent_id / patent_title / patent_abstract / patent_date /
assignee_organization / inventor_name / cpc_subgroup_id / country。
"""
from __future__ import annotations

import json
import logging
import time
from typing import Iterator, Optional

import requests

from src.governance.normalize import normalize_cpc, normalize_publication_number

from .base import (
    AdapterError,
    BaseAdapter,
    PriorArtQuery,
    PriorArtRecord,
)

log = logging.getLogger(__name__)

_PATENTSVIEW_URL = "https://api.patentsview.org/patents/query"
_DEFAULT_TIMEOUT = 30
_PAGE_SIZE = 50                 # PatentsView 单页硬上限
_FIELDS = [
    "patent_id",
    "patent_title",
    "patent_abstract",
    "patent_date",
    "patent_type",
    "assignee_organization",
    "inventor_name_first",
    "inventor_name_last",
    "cpc_subgroup_id",
    "country",
]


class USPTOOpenDataAdapter(BaseAdapter):
    source_id = "uspto-od"
    source_kind = "prior_art_corpus"
    requires_auth = False
    rate_limit_sec = 1.0         # 60/min

    def __init__(
        self,
        base_url: str = _PATENTSVIEW_URL,
        session: Optional[requests.Session] = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__()
        self.base_url = base_url
        self.session = session or requests.Session()
        self.timeout = timeout

    def health_check(self) -> bool:
        try:
            r = self.session.post(
                self.base_url,
                json={"q": {"patent_id": "US10000000"}, "f": ["patent_id"]},
                timeout=5,
            )
            # 严格:返回 HTML/Angular SPA 也不算健康,旧 endpoint 已停
            # 必须返回 JSON 且包含 patents 字段
            if r.status_code != 200:
                return False
            ctype = r.headers.get("Content-Type", "")
            if "json" not in ctype.lower():
                return False
            try:
                data = r.json()
                return "patents" in data or "count" in data
            except (ValueError, json.JSONDecodeError):
                return False
        except requests.RequestException as exc:
            log.warning("USPTO health check failed: %s", exc)
            return False

    def search(self, query: PriorArtQuery) -> Iterator[PriorArtRecord]:
        for kw in query.keywords:
            for cpc in query.cpc_prefixes:
                yield from self._search_one(kw, cpc, query.filing_date_from, query.per_query_limit)

    def _search_one(
        self,
        keyword: str,
        cpc_prefix: str,
        filing_from: str,
        limit: int,
    ) -> Iterator[PriorArtRecord]:
        """单个 (keyword, cpc) 组合分页拉取。"""
        per_page = min(limit, _PAGE_SIZE)
        page = 1
        yielded = 0
        while yielded < limit:
            self._rate_limit()
            body = {
                "q": {
                    "_and": [
                        {"_text_any": {"patent_title": keyword}},
                        {"_starts_with": {"cpc_subgroup_id": cpc_prefix}},
                        {"_gte": {"patent_date": filing_from.replace("-", "")}},
                    ]
                },
                "f": _FIELDS,
                "o": {"per_page": per_page, "page": page},
            }
            try:
                r = self.session.post(self.base_url, json=body, timeout=self.timeout)
            except requests.RequestException as exc:
                raise AdapterError(f"USPTO request failed: {exc}") from exc
            if r.status_code == 429:
                log.warning("USPTO 429, sleep 30s")
                time.sleep(30)
                continue
            if r.status_code != 200:
                raise AdapterError(f"USPTO returned {r.status_code}: {r.text[:200]}")
            payload = r.content
            try:
                data = r.json()
            except json.JSONDecodeError as exc:
                raise AdapterError(f"USPTO non-JSON response: {exc}") from exc
            patents = data.get("patents") or []
            if not patents:
                return
            for p in patents:
                rec = self._to_record(p, keyword, cpc_prefix, payload)
                if rec is not None:
                    yield rec
                    yielded += 1
                    if yielded >= limit:
                        return
            if len(patents) < per_page:
                return
            page += 1

    def _to_record(
        self,
        p: dict,
        keyword: str,
        cpc_prefix: str,
        raw: bytes,
    ) -> Optional[PriorArtRecord]:
        try:
            country = (p.get("country") or "US").upper()
            pub_raw = p.get("patent_id") or ""
            # PatentsView API 返回裸号(如 7143984),需拼 country + 默认 kind
            pub_combined = (
                f"{country}{pub_raw}B2"
                if len(pub_raw) <= 8 and pub_raw.isdigit()
                else pub_raw
            )
            pub = normalize_publication_number(pub_combined)
            if not pub:
                return None
            title_en = (p.get("patent_title") or "").strip() or "[EN-only]"
            abstract_en = (p.get("patent_abstract") or "").strip() or "[EN-only]"
            patent_date = (p.get("patent_date") or "").strip()
            filing_date = _ymd_to_iso(patent_date) if patent_date else "1900-01-01"
            cpc_codes = tuple(
                normalize_cpc(c) for c in (p.get("cpc_subgroup_id") or []) if c
            )
            assignees = tuple(
                sorted({a for a in (p.get("assignee_organization") or []) if a})
            )
            inventors_raw = p.get("inventors") or []
            inventors = tuple(
                sorted({
                    " ".join(filter(None, [i.get("inventor_name_first"), i.get("inventor_name_last")])).strip()
                    for i in inventors_raw
                    if isinstance(i, dict)
                })
            )
            return PriorArtRecord(
                publication_number=pub,
                country_code=country,
                title_zh="[EN-only]",
                title_en=title_en,
                abstract_zh="[EN-only]",
                abstract_en=abstract_en,
                cpc_codes=cpc_codes,
                inventors=inventors,
                assignees=assignees,
                filing_date=filing_date,
                publication_date=filing_date,  # PatentsView 只给一个 patent_date
                grant_date=None,
                family_id=None,
                raw_url=f"https://patents.google.com/patent/{pub}",
                raw_payload_sha256=self.hash_bytes(raw),
                source_id=self.source_id,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("USPTO record parse failed for %s: %s", p.get("patent_id"), exc)
            return None


def _ymd_to_iso(s: str) -> str:
    """YYYYMMDD → YYYY-MM-DD;已是 ISO 则原样返回。"""
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s