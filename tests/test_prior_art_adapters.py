"""Phase A prior art adapter 单元测试。

15 测覆盖:
- 3 adapter 的字段映射 / normalize_publication_number / normalize_cpc / per_query_limit
- EPO Keychain 取凭据 / token 缓存 / 401 刷新
- Google Playwright HTML 解析 / 限速 / captcha 跳过
- normalize_record.resolve_overlap 跨源字段冲突
- health_check / registry 3 adapter 都能建
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.prior_art_adapters import (  # noqa: E402
    ADAPTERS,
    EPOOpsAdapter,
    GooglePatents_playwrightAdapter,
    PriorArtQuery,
    PriorArtRecord,
    USPTOOpenDataAdapter,
    all_adapters,
    ensure_db_safe,
    resolve_overlap,
    to_db_dict,
)
from src.prior_art_adapters.base import AdapterError  # noqa: E402
from src.prior_art_adapters.uspto_opendata import _ymd_to_iso  # noqa: E402


FIXTURES = Path(__file__).resolve().parent / "fixtures"


# ============================================================
# USPTO
# ============================================================

def test_uspto_adapter_parses_response_to_record():
    raw = (FIXTURES / "uspto_od_sample.json").read_bytes()
    mock_session = MagicMock()
    mock_session.post.return_value = MagicMock(
        status_code=200, content=raw, json=lambda: json.loads(raw)
    )
    adapter = USPTOOpenDataAdapter(session=mock_session)
    q = PriorArtQuery(
        keywords=("thrust lever",), cpc_prefixes=("B64D31",),
        per_query_limit=10,
    )
    results = list(adapter.search(q))
    assert len(results) >= 1
    rec = results[0]
    assert rec.publication_number == "US7143984B2"
    assert rec.country_code == "US"
    assert "thrust" in rec.title_en.lower()


def test_uspto_adapter_normalizes_publication_number():
    raw = (FIXTURES / "uspto_od_sample.json").read_bytes()
    mock_session = MagicMock()
    mock_session.post.return_value = MagicMock(
        status_code=200, content=raw, json=lambda: json.loads(raw)
    )
    adapter = USPTOOpenDataAdapter(session=mock_session)
    q = PriorArtQuery(keywords=("thrust lever",), cpc_prefixes=("B64D31",))
    results = list(adapter.search(q))
    for r in results:
        assert " " not in r.publication_number  # normalize 去空格


def test_uspto_adapter_cpc_normalization():
    raw = (FIXTURES / "uspto_od_sample.json").read_bytes()
    mock_session = MagicMock()
    mock_session.post.return_value = MagicMock(
        status_code=200, content=raw, json=lambda: json.loads(raw)
    )
    adapter = USPTOOpenDataAdapter(session=mock_session)
    q = PriorArtQuery(keywords=("thrust lever",), cpc_prefixes=("B64D31",))
    results = list(adapter.search(q))
    for r in results:
        for c in r.cpc_codes:
            assert " " not in c       # normalize_cpc 去空格


def test_uspto_adapter_respects_per_query_limit():
    """500 上限硬约束 — adapter search 单 keyword+cpc 命中数应 ≤ limit。"""
    raw = (FIXTURES / "uspto_od_sample.json").read_bytes()
    mock_session = MagicMock()
    mock_session.post.return_value = MagicMock(
        status_code=200, content=raw, json=lambda: json.loads(raw)
    )
    adapter = USPTOOpenDataAdapter(session=mock_session)
    q = PriorArtQuery(
        keywords=("thrust lever",), cpc_prefixes=("B64D31",),
        per_query_limit=2,
    )
    results = list(adapter.search(q))
    assert len(results) <= 2


# ============================================================
# EPO
# ============================================================

def test_epo_adapter_oauth_token_from_keychain(monkeypatch):
    captured = {}

    def fake_post(url, data=None, auth=None, headers=None, timeout=None):
        captured["auth"] = auth
        captured["data"] = data
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"access_token": "FAKE_TOKEN_123", "expires_in": 1200}
        return resp

    monkeypatch.setattr("subprocess.run", lambda *a, **kw: MagicMock(returncode=0, stdout="FAKE"))
    session = MagicMock()
    session.post.side_effect = fake_post
    adapter = EPOOpsAdapter(session=session)
    adapter._ensure_token()
    assert adapter._access_token == "FAKE_TOKEN_123"


def test_epo_adapter_token_cached_and_refreshed():
    """token 不重复请求:第二次 _ensure_token 应直接返回缓存。"""
    session = MagicMock()
    session.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "T1", "expires_in": 1200},
    )
    adapter = EPOOpsAdapter(session=session)
    with patch("subprocess.run", lambda *a, **kw: MagicMock(returncode=0, stdout="x")):
        adapter._ensure_token()
        adapter._ensure_token()  # 第二次,应不重复请求
    assert session.post.call_count == 1


def test_epo_adapter_parses_biblio_to_record():
    raw = (FIXTURES / "epo_ops_sample.xml").read_bytes()
    session = MagicMock()
    session.get.return_value = MagicMock(status_code=200, content=raw)
    session.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "T", "expires_in": 1200},
    )
    adapter = EPOOpsAdapter(session=session)
    with patch("subprocess.run", lambda *a, **kw: MagicMock(returncode=0, stdout="x")):
        # monkey-patch rate_limit 防 sleep 拖慢测试
        adapter._rate_limit = lambda: None
        q = PriorArtQuery(
            keywords=("FADEC",), cpc_prefixes=("F02C9",),
            per_query_limit=5,
        )
        results = list(adapter.search(q))
    assert len(results) >= 1
    rec = results[0]
    assert rec.country_code in ("EP", "WO")
    assert rec.title_en
    assert "F02C9" in rec.cpc_codes[0]


def test_epo_adapter_handles_401_reauth():
    """401 → 刷新 token → 重试。"""
    session = MagicMock()
    session.post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "T_NEW", "expires_in": 1200},
    )
    # GET 第一次 401,第二次 200
    call_count = {"n": 0}
    ok_xml = (FIXTURES / "epo_ops_sample.xml").read_bytes()

    def fake_get(*a, **kw):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return MagicMock(status_code=401, content=b"")
        return MagicMock(status_code=200, content=ok_xml)

    session.get.side_effect = fake_get

    adapter = EPOOpsAdapter(session=session)
    with patch("subprocess.run", lambda *a, **kw: MagicMock(returncode=0, stdout="x")):
        adapter._rate_limit = lambda: None
        q = PriorArtQuery(keywords=("FADEC",), cpc_prefixes=("F02C9",), per_query_limit=2)
        results = list(adapter.search(q))
    assert call_count["n"] >= 2
    assert adapter._access_token == "T_NEW"


# ============================================================
# Google Patents via Playwright
# ============================================================

def test_google_playwright_search_html_parse():
    """HTML 解析 → record,3 个 patent。"""
    from bs4 import BeautifulSoup
    html = (FIXTURES / "google_patents_search_sample.html").read_text()
    soup = BeautifulSoup(html, "html.parser")
    results = soup.select("article.search-result")
    assert len(results) == 3
    pubs = []
    for r in results:
        link = r.select_one("a[href*='/patent/']")
        import re as _re
        m = _re.search(r"/patent/([A-Z]{2}\d+[A-Z]?\d?)/", link["href"])
        pubs.append(m.group(1))
    assert "US7143984B2" in pubs
    assert "EP1234567B1" in pubs


def test_google_playwright_rate_limit_respected():
    """_rate_limit 强制 sleep ≥ rate_limit_sec。"""
    a = GooglePatents_playwrightAdapter()
    a.rate_limit_sec = 0.1
    t0 = time.monotonic()
    a._rate_limit()
    a._rate_limit()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.1


def test_google_playwright_captcha_skips_gracefully():
    """captcha 关键字出现 → adapter health_check 返回 False,不 raise。"""
    a = GooglePatents_playwrightAdapter()
    mock_ctx = MagicMock()
    page = mock_ctx.new_page.return_value
    page.content.return_value = "Our systems have detected unusual traffic from your computer."
    page.goto.return_value = None
    a._browser = MagicMock()
    a._context = mock_ctx
    assert a.health_check() is False


# ============================================================
# normalize_record 跨源合并
# ============================================================

def test_normalize_record_resolves_overlap():
    """同 publication_number 跨 3 源 → resolve_overlap 字段合并正确。"""
    r1 = PriorArtRecord(
        publication_number="US7143984B2", country_code="US",
        title_zh="[EN-only]", title_en="short title",
        abstract_zh="[EN-only]", abstract_en="short",
        cpc_codes=("B64D31/10",), inventors=("A",), assignees=("Co1",),
        filing_date="2006-01-01", publication_date="2006-12-19",
        grant_date=None, family_id=None, raw_url="u1",
        raw_payload_sha256="h1", source_id="uspto-od",
    )
    r2 = PriorArtRecord(
        publication_number="US7143984B2", country_code="US",
        title_zh="[EN-only]", title_en="much longer title from Google",
        abstract_zh="[EN-only]", abstract_en="a much longer abstract",
        cpc_codes=("B64D31/10", "F02C9/28"), inventors=("A", "B"), assignees=("Co1", "Co2"),
        filing_date="2006-01-15", publication_date="2006-12-19",
        grant_date="2007-01-01", family_id="FAM123",
        raw_url="u2", raw_payload_sha256="h2", source_id="google-patents-playwright",
    )
    merged = resolve_overlap([r1, r2])
    assert merged.title_en == "much longer title from Google"     # 最长
    assert merged.abstract_en == "a much longer abstract"
    assert merged.filing_date == "2006-01-15"                    # 最晚
    assert merged.grant_date == "2007-01-01"
    assert merged.family_id == "FAM123"
    assert "F02C9/28" in merged.cpc_codes                        # 并集
    assert "Co2" in merged.assignees
    assert "B" in merged.inventors


def test_ensure_db_safe_rejects_bad_record():
    bad = PriorArtRecord(
        publication_number="X", country_code="USA",  # 3 位 country
        title_zh="", title_en="",
        abstract_zh="", abstract_en="",
        cpc_codes=(), inventors=(), assignees=(),
        filing_date="not-a-date", publication_date="not-a-date",
        source_id="x",
    )
    with pytest.raises(ValueError):
        ensure_db_safe(bad)


def test_to_db_dict_json_safe():
    rec = PriorArtRecord(
        publication_number="US7143984B2", country_code="US",
        title_zh="[EN-only]", title_en="t",
        abstract_zh="[EN-only]", abstract_en="a",
        cpc_codes=("B64D31/10",), inventors=("A",), assignees=("Co",),
        filing_date="2006-01-01", publication_date="2006-12-19",
        source_id="uspto-od",
    )
    d = to_db_dict(rec)
    json.dumps(d)          # 必须 JSON valid,governance prior_art_cpc_json 卡
    assert d["country_code"] == "US"
    assert d["cpc_codes"] == '["B64D31/10"]'


# ============================================================
# 公共:registry + health_check + adapter 注册
# ============================================================

def test_health_check_returns_bool():
    """3 adapter 都实现 health_check 签名。"""
    for cls in [USPTOOpenDataAdapter, EPOOpsAdapter, GooglePatents_playwrightAdapter]:
        a = cls()
        result = a.health_check()
        assert isinstance(result, bool)


def test_adapter_registry_instantiates_all_five():
    # 2026-08-25 Phase E 加 bq-public-patents + google-patents-xhr 共 5 个
    assert "uspto-od" in ADAPTERS
    assert "epo-ops" in ADAPTERS
    assert "google-patents-playwright" in ADAPTERS
    assert "google-patents-xhr" in ADAPTERS
    assert "bq-public-patents" in ADAPTERS
    a_list = all_adapters()
    assert len(a_list) == 5


def test_ymd_to_iso_helper():
    assert _ymd_to_iso("20061219") == "2006-12-19"
    assert _ymd_to_iso("2006-12-19") == "2006-12-19"
    assert _ymd_to_iso("") == ""


# ============================================================
# BigQuery Public Adapter (Phase E, REST API 路径)
# ============================================================

def test_bq_adapter_rest_parses_schema_and_rows(monkeypatch):
    """BQ REST API 返 schema + rows → _run_query_rest 正确解析为 dict 列表。"""
    from src.prior_art_adapters.bq_public import BQPublicPatentsAdapter

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "schema": {"fields": [
            {"name": "publication_number", "type": "STRING"},
            {"name": "country_code", "type": "STRING"},
            {"name": "filing_date", "type": "INTEGER"},
        ]},
        "rows": [
            {"f": [{"v": "US-10000001-B2"}, {"v": "US"}, {"v": "20200115"}]},
            {"f": [{"v": "US-10000002-B2"}, {"v": "US"}, {"v": "20200201"}]},
        ],
        "totalBytesProcessed": "15600000000",
        "jobComplete": True,
    }

    monkeypatch.setattr(
        "src.prior_art_adapters.bq_public.requests.post",
        lambda *a, **kw: fake_resp,
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_access_token",
        staticmethod(lambda: "FAKE_TOKEN"),
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_project_id",
        staticmethod(lambda: "test-project"),
    )

    adapter = BQPublicPatentsAdapter()
    rows = adapter._run_query_rest("SELECT 1")
    assert rows is not None
    assert len(rows) == 2
    assert rows[0]["publication_number"] == "US-10000001-B2"
    assert rows[0]["country_code"] == "US"
    assert rows[0]["filing_date"] == "20200115"


def test_bq_adapter_rest_returns_none_on_quota_error(monkeypatch):
    """Quota exceeded → _run_query_rest 返 None,不抛异常。"""
    from src.prior_art_adapters.bq_public import BQPublicPatentsAdapter

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "error": {
            "code": 403,
            "message": "Quota exceeded: free query bytes scanned",
            "status": "PERMISSION_DENIED",
        },
    }

    monkeypatch.setattr(
        "src.prior_art_adapters.bq_public.requests.post",
        lambda *a, **kw: fake_resp,
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_access_token",
        staticmethod(lambda: "FAKE_TOKEN"),
    )

    adapter = BQPublicPatentsAdapter()
    rows = adapter._run_query_rest("SELECT 1")
    assert rows is None


def test_bq_adapter_rest_returns_none_on_no_token(monkeypatch):
    """无 gcloud token → _run_query_rest 返 None,不发起网络请求。"""
    from src.prior_art_adapters.bq_public import BQPublicPatentsAdapter

    post_called = {"n": 0}

    def fake_post(*a, **kw):
        post_called["n"] += 1
        return MagicMock()

    monkeypatch.setattr(
        "src.prior_art_adapters.bq_public.requests.post",
        fake_post,
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_access_token",
        staticmethod(lambda: None),  # token 不可用
    )

    adapter = BQPublicPatentsAdapter()
    rows = adapter._run_query_rest("SELECT 1")
    assert rows is None
    assert post_called["n"] == 0


def test_bq_adapter_rest_returns_empty_list_on_no_rows(monkeypatch):
    """查询成功但 rows 为空 → 返 [] (不是 None),search() 正常完成。"""
    from src.prior_art_adapters.bq_public import BQPublicPatentsAdapter

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "schema": {"fields": [{"name": "publication_number", "type": "STRING"}]},
        "rows": [],       # 空结果集
    }

    monkeypatch.setattr(
        "src.prior_art_adapters.bq_public.requests.post",
        lambda *a, **kw: fake_resp,
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_access_token",
        staticmethod(lambda: "T"),
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_project_id",
        staticmethod(lambda: "p"),
    )

    adapter = BQPublicPatentsAdapter()
    rows = adapter._run_query_rest("SELECT publication_number FROM tbl LIMIT 0")
    assert rows == []


def test_bq_adapter_search_yields_records_from_rest(monkeypatch):
    """search() 端到端:REST 返 1 行 → yield 1 个 PriorArtRecord,字段映射正确。"""
    from src.prior_art_adapters.bq_public import BQPublicPatentsAdapter

    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "schema": {"fields": [
            {"name": "publication_number", "type": "STRING"},
            {"name": "country_code", "type": "STRING"},
            {"name": "family_id", "type": "INTEGER"},
            {"name": "filing_date", "type": "INTEGER"},
            {"name": "publication_date", "type": "INTEGER"},
            {"name": "grant_date", "type": "INTEGER"},
        ]},
        "rows": [
            {"f": [{"v": "US-10000001-B2"}, {"v": "US"}, {"v": "12345"},
                   {"v": "20200115"}, {"v": "20200615"}, {"v": "20200801"}]},
        ],
    }

    monkeypatch.setattr(
        "src.prior_art_adapters.bq_public.requests.post",
        lambda *a, **kw: fake_resp,
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_access_token",
        staticmethod(lambda: "T"),
    )
    monkeypatch.setattr(
        BQPublicPatentsAdapter, "_gcloud_project_id",
        staticmethod(lambda: "p"),
    )

    adapter = BQPublicPatentsAdapter()
    q = PriorArtQuery(
        keywords=("reverse thrust",), cpc_prefixes=("F02C9",),
        per_query_limit=5, filing_date_from="2020-01-01",
    )
    results = list(adapter.search(q))
    assert len(results) == 1
    rec = results[0]
    assert rec.publication_number == "US10000001B2"   # normalize 去 '-'
    assert rec.country_code == "US"
    assert rec.filing_date == "2020-01-15"
    assert rec.grant_date == "2020-08-01"
    assert rec.family_id == "12345"
    assert rec.source_id == "bq-public-patents"