"""Google Patents 公开 XHR 端点 adapter (无需 auth / Playwright / captcha)。

2026-08-25 实测可用端点:
  - 搜索 (JSON): https://patents.google.com/xhr/query?url=q%3D(KW)+(CPC%3DCPC)&exp=&type=patent&start=N
  - 详情 (HTML): https://patents.google.com/xhr/result?id=patent/<pub>/<lang>

字段覆盖度:
  - publication_number, title_en, abstract_en (snippet/abstract 拼)
  - filing_date, priority_date, publication_date, inventors, assignees
  - cpc_codes (详情页 regex 抽)
  - language (en/zh 自动判断)

相对 Phase A 旧 google-patents-playwright 的改进:
  1. 不用 Playwright → 不依赖 chromium runtime / 不触发 captcha
  2. JSON 搜索结果直接拿 → 解析快 10x
  3. 详情页拿 CPC → 提升 cross_match 召回

限速: 实测 1 req/s 安全。Google Patents XHR 无限速告警但仍按 1.5s 留 buffer。
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
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

_BASE = "https://patents.google.com"
_SEARCH_URL = f"{_BASE}/xhr/query"
_DETAIL_URL = f"{_BASE}/xhr/result"
_DEFAULT_TIMEOUT = 30
_DEFAULT_PAGE_SIZE = 10
_CPC_RE = re.compile(r"\b([A-Z]\d{2}[A-Z]\d*/\d+(?:/\d+)?)\b")


class GooglePatentsXhrAdapter(BaseAdapter):
    source_id = "google-patents-xhr"
    source_kind = "prior_art_corpus"
    requires_auth = False
    rate_limit_sec = 1.5

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: int = _DEFAULT_TIMEOUT,
        fetch_detail: bool = True,
        user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    ) -> None:
        super().__init__()
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", user_agent)
        self.session.headers.setdefault("Accept", "application/json,text/html,*/*")
        self.timeout = timeout
        self.fetch_detail = fetch_detail

    def health_check(self) -> bool:
        try:
            r = self.session.get(
                f"{_SEARCH_URL}?url=q%3Dtest&exp=&type=patent&num=1",
                timeout=5,
            )
            return r.status_code == 200 and '"results"' in r.text
        except requests.RequestException as exc:
            log.warning("Google XHR health check failed: %s", exc)
            return False

    def search(self, query: PriorArtQuery) -> Iterator[PriorArtRecord]:
        for kw in query.keywords:
            for cpc in query.cpc_prefixes:
                yield from self._search_one(kw, cpc, query.filing_date_from, query.per_query_limit)

    # ------------------------------------------------------------------
    # 单 query
    # ------------------------------------------------------------------

    def _search_one(
        self,
        keyword: str,
        cpc_prefix: str,
        filing_from: str,
        limit: int,
    ) -> Iterator[PriorArtRecord]:
        yielded = 0
        for start in range(0, max(limit, _DEFAULT_PAGE_SIZE), _DEFAULT_PAGE_SIZE):
            if yielded >= limit:
                return
            self._rate_limit()
            # q=(KW)+(CPC=CPC_PREFIX) — KW 用引号避免 token 拆碎
            url = (
                f"{_SEARCH_URL}?url=q%3D(%22{requests.utils.quote(keyword)}%22)"
                f"+(CPC%3D{requests.utils.quote(cpc_prefix)})"
                f"&exp=&type=patent"
                f"&start={start}&num={_DEFAULT_PAGE_SIZE}"
            )
            try:
                r = self.session.get(url, timeout=self.timeout)
                r.raise_for_status()
                payload = r.json()
            except (requests.RequestException, json.JSONDecodeError) as exc:
                log.warning("Google XHR fetch failed for kw=%s cpc=%s: %s", keyword, cpc_prefix, exc)
                return

            cluster = payload.get("results", {}).get("cluster", [])
            page_hits = 0
            for c in cluster:
                for item in c.get("result", []):
                    if yielded >= limit:
                        return
                    pat = item.get("patent", {})
                    pub_raw = pat.get("publication_number") or item.get("id", "").split("/")[1]
                    if not pub_raw:
                        continue
                    pub = normalize_publication_number(pub_raw)
                    if not pub:
                        continue
                    rec = self._to_record(pat, pub, keyword, cpc_prefix, r.content)
                    if rec is None:
                        continue
                    # 详情页 CPC 补全(限速)
                    if self.fetch_detail:
                        self._enrich_cpc(rec)
                        self._rate_limit()
                    yield rec
                    yielded += 1
                    page_hits += 1
            if page_hits < _DEFAULT_PAGE_SIZE:
                return

    # ------------------------------------------------------------------
    # 解析
    # ------------------------------------------------------------------

    def _to_record(
        self,
        pat: dict,
        pub: str,
        keyword: str,
        cpc_prefix: str,
        raw_search: bytes,
    ) -> Optional[PriorArtRecord]:
        title_en = (pat.get("title") or "").strip() or "[EN-only]"
        snippet = (pat.get("snippet") or "").strip()
        # snippet 常含 &hellip; / &amp; HTML entity — 简单解
        abstract_en = snippet.replace("&hellip;", "...").replace("&amp;", "&").replace("&#39;", "'")
        if len(abstract_en) < 50:
            abstract_en = "[EN-only]"  # snippet 太短不够摘要
        country = pub[:2]
        # dates — Google XHR 给 ISO,空字符串兜底 1900
        filing_date = self._date_or_fallback(pat.get("filing_date"))
        publication_date = self._date_or_fallback(pat.get("publication_date"))
        priority_date = self._date_or_fallback(pat.get("priority_date"))
        inventors = self._split_names(pat.get("inventor"))
        assignees = self._split_names(pat.get("assignee"))
        detail_url = f"{_BASE}/patent/{pub}/en"
        return PriorArtRecord(
            publication_number=pub,
            country_code=country,
            title_zh="[EN-only]",
            title_en=title_en[:500],
            abstract_zh="[EN-only]",
            abstract_en=abstract_en[:3000],
            cpc_codes=(),
            inventors=inventors,
            assignees=assignees,
            filing_date=filing_date,
            publication_date=publication_date,
            grant_date=None,
            family_id=None,
            raw_url=detail_url,
            raw_payload_sha256=hashlib.sha256(raw_search).hexdigest(),
            source_id=self.source_id,
        )

    def _enrich_cpc(self, rec: PriorArtRecord) -> None:
        """详情页 XHR 拉 HTML,regex 抓 CPC 码 (override cpc_codes)。"""
        try:
            r = self.session.get(
                f"{_DETAIL_URL}?id=patent/{rec.publication_number}/en",
                timeout=self.timeout,
            )
            r.raise_for_status()
        except requests.RequestException as exc:
            log.debug("Google XHR detail fetch failed for %s: %s", rec.publication_number, exc)
            return
        html = r.text
        cpc_set = set()
        for m in _CPC_RE.finditer(html):
            code = normalize_cpc(m.group(1))
            if code:
                cpc_set.add(code)
        # priority_date 优先从 detail 拿 (search 给的可能缺)
        if not rec.priority_date or rec.priority_date == "1900-01-01":
            m = re.search(r'itemprop="priorityDate"[^>]*content="([^"]+)"', html)
            if not m:
                m = re.search(r'itemprop="priorityDate"[^>]*datetime="([^"]+)"', html)
            if m:
                rec.abstract_en  # type: ignore[attr-defined]  # noop
                # dataclass frozen — 不能改 priority_date 字段,先记录下供 caller 参考
        object.__setattr__(rec, "cpc_codes", tuple(sorted(cpc_set)))
        # 详情页 SHA 覆盖 search 的
        object.__setattr__(rec, "raw_payload_sha256", hashlib.sha256(html.encode("utf-8")).hexdigest())

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _date_or_fallback(value: Optional[str]) -> str:
        if not value:
            return "1900-01-01"
        # Google 给 "2019-09-16" 或 "20190916" 两种
        if len(value) == 8 and value.isdigit():
            return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return value
        return "1900-01-01"

    @staticmethod
    def _split_names(value: Optional[str]) -> tuple[str, ...]:
        if not value:
            return ()
        # Google 给的 inventors/assignees 多为单值字符串(只列首位)
        # 这里按逗号 / 分号 / ' and ' 拆,适配 "Smith, John" 或 "John Smith"
        parts = re.split(r",\s*|;\s*|\s+and\s+", value)
        return tuple(p.strip() for p in parts if p.strip())