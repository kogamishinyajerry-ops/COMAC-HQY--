"""Google Patents via Playwright adapter。

反爬严,降级使用:captcha 出现 → log + skip,不 raise。
rate_limit_sec 默认 3.0(避免触发 Google 风控)。
"""
from __future__ import annotations

import json
import logging
import re
from typing import Iterator, Optional

from bs4 import BeautifulSoup

from src.governance.normalize import normalize_cpc, normalize_publication_number

from .base import (
    AdapterError,
    BaseAdapter,
    PriorArtQuery,
    PriorArtRecord,
)

log = logging.getLogger(__name__)

_BASE = "https://patents.google.com"
_SEARCH_PATH = "/"
_DEFAULT_TIMEOUT = 30_000          # Playwright timeout 单位 ms
_CAPTCHA_MARKERS = ("captcha", "unusual traffic", "/sorry/", "robot check")


class GooglePatents_playwrightAdapter(BaseAdapter):
    source_id = "google-patents-playwright"
    source_kind = "prior_art_corpus"
    requires_auth = False
    rate_limit_sec = 3.0          # 谨慎,避免 captcha

    def __init__(
        self,
        base_url: str = _BASE,
        headless: bool = True,
        proxy: Optional[str] = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__()
        self.base_url = base_url
        self.headless = headless
        self.proxy = proxy
        self.timeout = timeout
        self._browser = None
        self._context = None

    def _ensure_browser(self):
        """懒启动 Playwright Chromium browser。"""
        if self._browser is None:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start()
            launch_kwargs = {"headless": self.headless}
            if self.proxy:
                launch_kwargs["proxy"] = {"server": self.proxy}
            self._browser = pw.chromium.launch(**launch_kwargs)
            self._context = self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            )
        return self._context

    def health_check(self) -> bool:
        try:
            ctx = self._ensure_browser()
            page = ctx.new_page()
            page.goto(self.base_url, timeout=self.timeout)
            html = page.content()
            page.close()
            return not any(m in html.lower() for m in _CAPTCHA_MARKERS)
        except Exception as exc:  # noqa: BLE001
            log.warning("Google health check failed: %s", exc)
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
        ctx = self._ensure_browser()
        page = ctx.new_page()
        try:
            yielded = 0
            for start in range(0, limit, 10):
                if yielded >= limit:
                    return
                self._rate_limit()
                # Google Patents URL:q=FADEC cpc=F02C9 before=priority:20200101
                url = (
                    f"{self.base_url}/?q={keyword}+cpc:{cpc_prefix}"
                    f"&before=priority:{filing_from.replace('-', '')}"
                    f"&start={start}"
                )
                try:
                    page.goto(url, timeout=self.timeout)
                except Exception as exc:  # noqa: BLE001
                    log.warning("Google navigate failed: %s", exc)
                    return
                html = page.content()
                if any(m in html.lower() for m in _CAPTCHA_MARKERS):
                    log.warning("Google captcha triggered, skip rest of this query")
                    return
                soup = BeautifulSoup(html, "html.parser")
                results = soup.select("article.search-result, [data-result]")
                if not results:
                    return
                for r in results:
                    rec = self._to_record(r, keyword, cpc_prefix, html.encode("utf-8"))
                    if rec is not None:
                        yield rec
                        yielded += 1
                        if yielded >= limit:
                            return
                if len(results) < 10:
                    return
        finally:
            page.close()

    def _to_record(
        self,
        result_elem,
        keyword: str,
        cpc_prefix: str,
        raw: bytes,
    ) -> Optional[PriorArtRecord]:
        try:
            link = result_elem.select_one("a[href*='/patent/']")
            if not link or not link.get("href"):
                return None
            href = link["href"]
            m = re.search(r"/patent/([A-Z]{2}\d+[A-Z]?\d?)/", href)
            if not m:
                return None
            pub_raw = m.group(1)
            pub = normalize_publication_number(pub_raw)
            country = pub[:2]
            title_en = (link.get_text(strip=True) or "[EN-only]").strip() or "[EN-only]"
            abstract_en = ""        # 详情页才有,Phase A 简化不抓
            # dates: 检索页不显式列日期,留 1900-01-01 兜底
            filing_date = "1900-01-01"
            publication_date = "1900-01-01"
            # CPC:列表页 metadata 没有 cpc_code 字段,Phase A 跳过
            cpc_codes: tuple[str, ...] = ()
            assignees: tuple[str, ...] = ()
            inventors: tuple[str, ...] = ()
            detail_url = f"https://patents.google.com/patent/{pub}/en"
            return PriorArtRecord(
                publication_number=pub,
                country_code=country,
                title_zh="[EN-only]",
                title_en=title_en[:500],
                abstract_zh="[EN-only]",
                abstract_en=abstract_en,
                cpc_codes=cpc_codes,
                inventors=inventors,
                assignees=assignees,
                filing_date=filing_date,
                publication_date=publication_date,
                grant_date=None,
                family_id=None,
                raw_url=detail_url,
                raw_payload_sha256=self.hash_bytes(raw),
                source_id=self.source_id,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("Google record parse failed: %s", exc)
            return None

    def close(self) -> None:
        if self._context is not None:
            try:
                self._context.close()
            except Exception:  # noqa: BLE001
                pass
            self._context = None
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:  # noqa: BLE001
                pass
            self._browser = None

    def __del__(self) -> None:
        self.close()