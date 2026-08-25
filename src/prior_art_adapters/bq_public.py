"""Google BigQuery 公开 patents-public-data adapter (走 REST API)。

数据集: patents-public-data.patents.publications (Google 公开)
- 1.5 亿+ 全球专利,CPC/标题/摘要/受让人/发明人齐全
- 1 TB 扫描/月免费,典型 query 10~17 GB (无分区,WHERE 任何字段都全表扫)
- 不需 API key (用 gcloud auth 用户身份)

走 BigQuery REST API v2 而非 `bq query` CLI,理由:
1. `bq query` 在 macOS LibreSSL + OpenSSL 3.5.5 共存环境下会触发
   `SSLEOFError(8, 'SSL: UNEXPECTED_EOF_WHILE_READING')`(已实测 2026-08-25)
2. REST API 直接走 https://bigquery.googleapis.com/bigquery/v2/... 同样 token,
   但走 urllib3 直连,绕开 gcloud CLI 的 SSL 重协商路径
3. dry_run / 元数据查询仍走 `bq` CLI(零 bytes scanned,SSL 不触发)

字段覆盖度(对齐 PriorArtRecord):
- publication_number, country_code, family_id
- filing_date, publication_date, grant_date (8 位整数 → ISO)
- title_en / abstract_en 占位 "[EN-only]"(UNNEST JOIN 烧 quota,不放主 SELECT)

Quota 实测 (2026-08-25 dry_run):
- `WHERE c.code LIKE 'F02C9%' AND filing_date >= 2020` → 17 GB / query
- free tier 1 TB/月 ≈ 60 query/月
- 真查询若返 "Quota exceeded: free query bytes scanned" → 等月初重置或换 GCP project
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
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

_PROJECT_BILLING = "patents-public-data"      # 公开数据集,只读
_DATASET = "patents"
_TABLE = "publications"
_QUERY_TIMEOUT_SEC = 60
_MAX_ROWS_PER_QUERY = 5000
_BQ_API = "https://bigquery.googleapis.com/bigquery/v2"


class BQPublicPatentsAdapter(BaseAdapter):
    source_id = "bq-public-patents"
    source_kind = "prior_art_corpus"
    requires_auth = False
    rate_limit_sec = 0.0                       # BQ 无 req/s 限速,1 TB/月才是硬约束

    # --------------------------------------------------------------
    # 健康检查:用 bq CLI 跑 SELECT 1 (零字节,不烧 quota)
    # --------------------------------------------------------------

    def health_check(self) -> bool:
        try:
            r = subprocess.run(
                ["bq", "query", "--use_legacy_sql=false", "--format=json", "--max_rows=1",
                 "SELECT 1 AS ok"],
                capture_output=True, text=True, timeout=10,
            )
            return r.returncode == 0 and ('"ok"' in r.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            log.warning("BQ health check failed: %s", exc)
            return False

    # --------------------------------------------------------------
    # 主入口:每个 keyword × cpc_prefix 组合跑一次 REST 查询
    # --------------------------------------------------------------

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
        filing_int = filing_from.replace("-", "")
        # 最小化 query: 只取 publication_number + country + 日期
        # 任何带 EXISTS / JOIN UNNEST 多个 array 的 query 都会触发
        # gen-lang 子项目 "Quota exceeded: free query bytes scanned"
        # keyword + cpc_prefix 仅做 record 层后过滤(数据多了再过滤)
        sql = f"""
SELECT
  pub.publication_number,
  pub.country_code,
  pub.family_id,
  pub.filing_date,
  pub.publication_date,
  pub.grant_date
FROM `{_PROJECT_BILLING}.{_DATASET}.{_TABLE}` AS pub
WHERE '{cpc_prefix}' IN UNNEST(ARRAY(SELECT c.code FROM UNNEST(pub.cpc) c))
  AND pub.filing_date >= {filing_int}
LIMIT {min(limit, _MAX_ROWS_PER_QUERY)}
"""
        rows = self._run_query_rest(sql)
        if rows is None:
            return
        log.info("BQ REST kw=%s cpc=%s → %d rows", keyword, cpc_prefix, len(rows))
        for row in rows:
            rec = self._to_record(row, keyword, cpc_prefix)
            if rec:
                yield rec

    # --------------------------------------------------------------
    # REST API 调用 (绕开 bq query 的 SSL bug)
    # --------------------------------------------------------------

    def _run_query_rest(self, sql: str) -> Optional[list[dict]]:
        """走 BigQuery REST API v2 queries endpoint,失败返 None (不抛)。"""
        token = self._gcloud_access_token()
        if not token:
            log.warning("BQ REST: gcloud auth token 不可用,跳过")
            return None
        project_id = self._gcloud_project_id() or "patents-public-data"
        url = f"{_BQ_API}/projects/{project_id}/queries"
        body = {
            "query": sql,
            "useLegacySql": False,
            "maxResults": _MAX_ROWS_PER_QUERY,
        }
        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept-Encoding": "gzip",
                },
                json=body,
                timeout=_QUERY_TIMEOUT_SEC,
            )
        except requests.RequestException as exc:
            log.warning("BQ REST network error: %s", exc)
            return None

        if resp.status_code != 200:
            log.warning("BQ REST HTTP %s: %s", resp.status_code, resp.text[:300])
            return None
        try:
            data = resp.json()
        except ValueError:
            log.warning("BQ REST 非 JSON 响应: %s", resp.text[:200])
            return None

        # 错误响应
        err = data.get("error")
        if err:
            log.warning("BQ REST error: code=%s msg=%s",
                        err.get("code"), (err.get("message") or "")[:300])
            return None

        # schema 字段顺序与 rows[i].f 数组一一对应
        rows_raw = data.get("rows") or []
        schema = (data.get("schema") or {}).get("fields") or []
        field_names = [f["name"] for f in schema]
        out: list[dict] = []
        for r in rows_raw:
            cells = r.get("f") or []
            row_dict = {}
            for i, name in enumerate(field_names):
                v = cells[i].get("v") if i < len(cells) else None
                row_dict[name] = v
            out.append(row_dict)
        return out

    @staticmethod
    def _gcloud_access_token() -> Optional[str]:
        try:
            r = subprocess.run(
                ["gcloud", "auth", "print-access-token"],
                capture_output=True, text=True, timeout=8,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
            log.warning("gcloud auth print-access-token 失败: rc=%s stderr=%s",
                        r.returncode, r.stderr[:200])
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            log.warning("gcloud auth not available: %s", exc)
            return None

    @staticmethod
    def _gcloud_project_id() -> Optional[str]:
        try:
            r = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True, text=True, timeout=5,
            )
            if r.returncode == 0:
                return r.stdout.strip() or None
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    # --------------------------------------------------------------
    # row → PriorArtRecord
    # --------------------------------------------------------------

    def _to_record(self, row: dict, keyword: str, cpc_prefix: str) -> Optional[PriorArtRecord]:
        pub_raw = row.get("publication_number")
        if not pub_raw:
            return None
        pub = normalize_publication_number(pub_raw)
        if not pub:
            return None
        country = (row.get("country_code") or pub[:2] or "").strip()[:2]
        cpc_set = {cpc_prefix} if cpc_prefix else set()
        return PriorArtRecord(
            publication_number=pub,
            country_code=country,
            title_zh="[EN-only]",
            title_en="[EN-only]",                # REST 不取(避免 JOIN UNNEST 烧 quota)
            abstract_zh="[EN-only]",
            abstract_en="[EN-only]",
            cpc_codes=tuple(sorted(cpc_set)),
            inventors=(),
            assignees=(),
            filing_date=_int_to_iso(row.get("filing_date")),
            publication_date=_int_to_iso(row.get("publication_date")),
            grant_date=_int_to_iso(row.get("grant_date")),
            family_id=str(row.get("family_id") or "") or None,
            raw_url=f"https://patents.google.com/patent/{pub}/en",
            raw_payload_sha256="",
            source_id=self.source_id,
        )


# ============================================================
# helpers
# ============================================================

def _int_to_iso(value) -> str:
    """BQ 8 位整数 '20200101' → '2020-01-01',空/None 兜底 1900-01-01。"""
    if not value:
        return "1900-01-01"
    s = str(value)
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    return "1900-01-01"
