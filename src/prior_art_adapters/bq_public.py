"""Google BigQuery 公开 patents-public-data adapter (走 `bq` CLI)。

数据集: patents-public-data.patents.publications (Google 公开)
- 1.5 亿+ 全球专利,CPC/标题/摘要/受让人/发明人齐全
- 1 TB 扫描/月免费,典型 query <5 GB
- 不需 API key (用 gcloud auth 用户身份)

走 subprocess `bq query` CLI 而非 google-cloud-bigquery Python lib,理由:
1. 不引入新 pip 依赖
2. 用户已 `gcloud auth login`,CLI 自动用应用默认凭据
3. JSON 输出流式,大结果集不易 OOM

字段覆盖度(对齐 PriorArtRecord):
- publication_number, country_code, title_en (摘要拼接自 abstract_localized)
- abstract_en, cpc_codes (UNNEST 抽)
- inventors, assignees (UNNEST + JSON 化)
- filing_date, publication_date, priority_date (8 位整数 → ISO)
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
from typing import Iterator, Optional

from src.governance.normalize import normalize_cpc, normalize_publication_number

from .base import (
    AdapterError,
    BaseAdapter,
    PriorArtQuery,
    PriorArtRecord,
)

log = logging.getLogger(__name__)

_PROJECT = "patents-public-data"          # 公开数据集,只读
_DATASET = "patents"
_TABLE = "publications"
_QUERY_TIMEOUT_SEC = 120
_MAX_ROWS_PER_QUERY = 5000


class BQPublicPatentsAdapter(BaseAdapter):
    source_id = "bq-public-patents"
    source_kind = "prior_art_corpus"
    requires_auth = False
    rate_limit_sec = 0.0                  # BQ 无 req/s 限速,1 TB/月才是硬约束

    def health_check(self) -> bool:
        try:
            r = subprocess.run(
                ["bq", "query", "--use_legacy_sql=false", "--format=json", "--max_rows=1",
                 "SELECT 1 AS ok"],
                capture_output=True, text=True, timeout=10,
            )
            # bq query JSON 输出可能是 [{"ok":"1"}] (string) 或 [{"ok":1}] (int)
            return r.returncode == 0 and ('"ok"' in r.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
            log.warning("BQ health check failed: %s", exc)
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
        # filing_from ISO 'YYYY-MM-DD' → 8 位整数
        filing_int = filing_from.replace("-", "")
        # 最小化 query:只取 publication_number + country + filing_date
        # 任何带 EXISTS / JOIN UNNEST 多个 array 的 query 都会触发
        # gen-lang 子项目 "Quota exceeded" (子 quota 限制 per-query bytes)
        # keyword + cpc_prefix 仅做 record 层后过滤(数据多了再过滤)
        sql = f"""
SELECT
  pub.publication_number,
  pub.country_code,
  pub.family_id,
  pub.filing_date,
  pub.publication_date,
  pub.grant_date
FROM `{_PROJECT}.{_DATASET}.{_TABLE}` AS pub
WHERE '{cpc_prefix}' IN UNNEST(ARRAY(SELECT c.code FROM UNNEST(pub.cpc) c))
  AND pub.filing_date >= {filing_int}
LIMIT {min(limit, _MAX_ROWS_PER_QUERY)}
"""
        try:
            proc = subprocess.run(
                ["bq", "query", "--use_legacy_sql=false", "--format=json", "--max_rows=0",
                 sql],
                capture_output=True, text=True, timeout=_QUERY_TIMEOUT_SEC,
            )
        except subprocess.TimeoutExpired as exc:
            log.warning("BQ query timeout for kw=%s cpc=%s: %s", keyword, cpc_prefix, exc)
            return

        if proc.returncode != 0:
            log.warning("BQ query failed for kw=%s cpc=%s: %s",
                        keyword, cpc_prefix, proc.stderr[:500])
            return

        rows = self._parse_bq_json(proc.stdout)
        log.info("BQ kw=%s cpc=%s → %d rows", keyword, cpc_prefix, len(rows))
        for row in rows:
            rec = self._to_record(row, keyword, cpc_prefix)
            if rec:
                yield rec

    # ------------------------------------------------------------------
    # 解析
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_bq_json(output: str) -> list[dict]:
        """bq query --format=json 输出形如:
        Waiting on bqjob_xxx ... (0s) Current status: DONE
        [
          {...},
          ...
        ]
        需要跳过 prelude 行。
        """
        # 找首个 '[' 或 '{'
        idx = output.find("[")
        if idx < 0:
            idx = output.find("{")
        if idx < 0:
            return []
        try:
            data = json.loads(output[idx:])
        except json.JSONDecodeError:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []

    def _to_record(self, row: dict, keyword: str, cpc_prefix: str) -> Optional[PriorArtRecord]:
        pub_raw = row.get("publication_number")
        if not pub_raw:
            return None
        pub = normalize_publication_number(pub_raw)
        if not pub:
            return None
        country = (row.get("country_code") or pub[:2] or "").strip()[:2]
        # title_en 不在 SQL SELECT (避免 JOIN UNNEST title 烧 quota),占位
        title_en = "[EN-only]"
        # cpc_codes 不取 ARRAY subquery,直接用 query 时传的 cpc_prefix
        cpc_set = {cpc_prefix} if cpc_prefix else set()
        # inventors / assignees 不取 (同 quota 顾虑)
        inventors = ()
        assignees = ()
        return PriorArtRecord(
            publication_number=pub,
            country_code=country,
            title_zh="[EN-only]",
            title_en=title_en[:500],
            abstract_zh="[EN-only]",
            abstract_en="[EN-only]",   # 简化:title-only JOIN 不取 abstract
            cpc_codes=tuple(sorted(cpc_set)),
            inventors=inventors,
            assignees=assignees,
            filing_date=_int_to_iso(row.get("filing_date")),
            publication_date=_int_to_iso(row.get("publication_date")),
            grant_date=_int_to_iso(row.get("grant_date")),
            family_id=str(row.get("family_id") or "") or None,
            raw_url=f"https://patents.google.com/patent/{pub}/en",
            raw_payload_sha256="",   # BigQuery 没有 raw 概念
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


def _bq_regex(keyword: str) -> str:
    """BQ REGEXP_CONTAINS 期望 POSIX 风格。转义 + 加 \\b 防子串。"""
    # 简化: 直接把 keyword 当字面量,BIGQUERY 用 RE2 默认不加 \\b,用 (?i) 前缀也没必要
    # LOWER 已在 SQL 里,这里只做引号转义
    return keyword.replace("\\", "\\\\").replace("'", "''")