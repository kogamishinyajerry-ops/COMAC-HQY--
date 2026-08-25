"""EPO Open Patent Services (OPS) v3.2 adapter。

公开 endpoint: https://ops.epo.org/3.2/
OAuth2 client_credentials,凭据从 macOS Keychain 读(EPO_CONSUMER_KEY/SECRET)。
限速 50 req/min,4 GB/IP/年(非商用免费)。
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import time
import xml.etree.ElementTree as XmlET
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

_BASE = "https://ops.epo.org/3.2"
_TOKEN_URL = f"{_BASE}/auth/accesstoken"
_SEARCH_URL = f"{_BASE}/rest-services/published-data/search/biblio"
_DEFAULT_TIMEOUT = 30
_KEYCHAIN_SERVICE = "epo-ops"
_KEYCHAIN_KEY_ACCOUNT = "EPO_CONSUMER_KEY"
_KEYCHAIN_SECRET_ACCOUNT = "EPO_CONSUMER_SECRET"
_NS = {"ops": "http://www.epo.org/exchange"}     # EPO XML 默认 namespace


class EPOOpsAdapter(BaseAdapter):
    source_id = "epo-ops"
    source_kind = "prior_art_corpus"
    requires_auth = True
    rate_limit_sec = 1.5         # 40/min(限速 50,留 buffer)

    def __init__(
        self,
        base_url: str = _BASE,
        session: Optional[requests.Session] = None,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        super().__init__()
        self.base_url = base_url
        self.session = session or requests.Session()
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def health_check(self) -> bool:
        try:
            self._ensure_token()
            r = self.session.get(
                f"{self.base_url}/rest-services/ping",
                headers=self._auth_headers(),
                timeout=5,
            )
            return r.status_code == 200
        except (AdapterError, requests.RequestException) as exc:
            log.warning("EPO health check failed: %s", exc)
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
        self._ensure_token()
        # EPO CQL syntax: cpc=(F02C9) and ti="FADEC", range 分页
        per_page = min(limit, 25)
        range_start = 1
        yielded = 0
        while yielded < limit:
            self._rate_limit()
            range_str = f"{range_start}-{range_start + per_page - 1}"
            params = {
                "q": f'cpc="{cpc_prefix}" and ti="{keyword}"',
                "Range": range_str,
            }
            try:
                r = self.session.get(
                    _SEARCH_URL,
                    params=params,
                    headers=self._auth_headers(),
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise AdapterError(f"EPO request failed: {exc}") from exc
            if r.status_code == 401:
                log.info("EPO 401, refresh token")
                self._access_token = None
                self._ensure_token()
                continue
            if r.status_code == 429:
                log.warning("EPO 429, sleep 30s")
                time.sleep(30)
                continue
            if r.status_code != 200:
                raise AdapterError(f"EPO returned {r.status_code}: {r.text[:200]}")
            raw = r.content
            try:
                root = XmlET.fromstring(raw)
            except XmlET.ParseError as exc:
                raise AdapterError(f"EPO XML parse failed: {exc}") from exc
            documents = root.findall(".//ops:exchange-document", _NS)
            if not documents:
                return
            for doc in documents:
                rec = self._to_record(doc, keyword, cpc_prefix, raw)
                if rec is not None:
                    yield rec
                    yielded += 1
                    if yielded >= limit:
                        return
            if len(documents) < per_page:
                return
            range_start += per_page

    def _to_record(
        self,
        doc: XmlET.Element,
        keyword: str,
        cpc_prefix: str,
        raw: bytes,
    ) -> Optional[PriorArtRecord]:
        try:
            # publication_reference
            pub_ref = doc.find("ops:publication-reference", _NS)
            doc_id = pub_ref.find("ops:document-id", _NS) if pub_ref is not None else None
            if doc_id is None:
                return None
            country = (doc_id.findtext("ops:country", default="", namespaces=_NS) or "").upper()
            doc_number = doc_id.findtext("ops:doc-number", default="", namespaces=_NS) or ""
            kind = doc_id.findtext("ops:kind", default="", namespaces=_NS) or ""
            pub_raw = f"{country}{doc_number}{kind}".strip()
            pub = normalize_publication_number(pub_raw)
            if not pub:
                return None

            # title(英文优先)
            title_en = ""
            for t in doc.findall("ops:invention-title", _NS):
                if t.get("{http://www.w3.org/XML/1998/namespace}lang") == "en":
                    title_en = (t.text or "").strip()
                    break
            if not title_en:
                first = doc.find("ops:invention-title", _NS)
                title_en = (first.text or "").strip() if first is not None else ""
            title_en = title_en or "[EN-only]"

            # abstract (Phase A 不强求,后续 抽)
            abstract_en = ""

            # dates
            filing_date = _xml_date(doc, "ops:application-reference/ops:date") or "1900-01-01"
            publication_date = _xml_date(doc, "ops:publication-reference/ops:date") or filing_date

            # CPC codes
            cpc_codes = tuple(
                normalize_cpc(c.text)
                for c in doc.findall(".//ops:cpc-text", _NS)
                if c.text
            )

            # assignees / inventors
            assignees = tuple(sorted({
                a.text.strip() for a in doc.findall(".//ops:applicant/ops:applicant-name", _NS)
                if a.text
            }))
            inventors = tuple(sorted({
                i.text.strip() for i in doc.findall(".//ops:inventor/ops:inventor-name", _NS)
                if i.text
            }))

            return PriorArtRecord(
                publication_number=pub,
                country_code=country or "??"[:2],
                title_zh="[EN-only]",
                title_en=title_en,
                abstract_zh="[EN-only]",
                abstract_en=abstract_en,
                cpc_codes=cpc_codes,
                inventors=inventors,
                assignees=assignees,
                filing_date=filing_date,
                publication_date=publication_date,
                grant_date=None,
                family_id=None,
                raw_url=f"https://worldwide.espacenet.com/patent/search?q={pub}",
                raw_payload_sha256=self.hash_bytes(raw),
                source_id=self.source_id,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("EPO record parse failed: %s", exc)
            return None

    # ============================================================
    # OAuth + Keychain
    # ============================================================

    def _ensure_token(self) -> None:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return
        key = _keychain_get(_KEYCHAIN_SERVICE, _KEYCHAIN_KEY_ACCOUNT)
        secret = _keychain_get(_KEYCHAIN_SERVICE, _KEYCHAIN_SECRET_ACCOUNT)
        try:
            r = self.session.post(
                _TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(key, secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise AdapterError(f"EPO token request failed: {exc}") from exc
        if r.status_code != 200:
            raise AdapterError(f"EPO token HTTP {r.status_code}: {r.text[:200]}")
        try:
            token_data = r.json()
        except json.JSONDecodeError as exc:
            raise AdapterError(f"EPO token non-JSON: {exc}") from exc
        self._access_token = token_data["access_token"]
        # default 20 min, 保守按 18 min 提前刷
        self._token_expires_at = time.time() + 18 * 60

    def _auth_headers(self) -> dict:
        if not self._access_token:
            raise AdapterError("EPO token not initialized; call _ensure_token first")
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/xml",
        }


def _xml_date(doc: XmlET.Element, path: str) -> Optional[str]:
    """从 XML 路径取 YYYYMMDD 日期,转 ISO。"""
    elem = doc.find(path, _NS)
    if elem is None or not elem.text:
        return None
    s = elem.text.strip()
    if re.match(r"^\d{8}$", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return s


def _keychain_get(service: str, account: str) -> str:
    """从 macOS Keychain 取 generic password。失败抛 AdapterError。"""
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise AdapterError(f"Keychain access failed: {exc}") from exc
    if result.returncode != 0:
        raise AdapterError(
            f"Keychain {service}/{account} not found. "
            f"Add with: security add-generic-password -s {service} -a {account} -w '<value>'"
        )
    return result.stdout.strip()