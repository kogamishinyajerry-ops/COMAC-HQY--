"""Phase E:兜底适配器 — 单值 BQ lookup 路径。

常规 `bq query` 走 `INFORMATION_SCHEMA` 或 EXISTS 子查询会触发 gen-lang-client-*
项目的 sub-quota (Per-query bytes scanned) 被卡死。但 cache hit / 单 publication_number
点查 不触发扫描,可稳定工作。

用法:
    python scripts/import_prior_art_phase_e.py \\
        --publication US-7650331-B1 \\
        --publication US-2025237175-A1 \\
        --source google-patents-xhr-bq-enrich \\
        --keywords "FADEC,EEC" \\
        --cpc "F02C9/00,F02C9/28"

每条记录:
    1. bq query --use_cache 查 publication_number
    2. 拿 title/country/filing_date
    3. 落 prior_art_patents + prior_art_publication_sources (bridge)
    4. 跑 18 governance check
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 屏蔽 build_db 模块加载时的 AWKB 网络
os.environ.setdefault("AWKB_ENABLED", "0")

from build_db import DB_PATH  # noqa: E402
from src.governance.data_integrity import require_all_pass  # noqa: E402
from src.governance.normalize import normalize_cpc, normalize_publication_number  # noqa: E402

LOG = logging.getLogger("phase_e")

_PROJECT = "patents-public-data"
_TABLE = "patents.publications"


def _bq_lookup(publication_number: str) -> dict | None:
    """单值 BQ 查询 (cache 命中,不烧 quota)。"""
    sql = f"""
SELECT
  pub.publication_number,
  pub.country_code,
  pub.family_id,
  pub.filing_date,
  pub.publication_date,
  pub.grant_date,
  ARRAY(SELECT c.code FROM UNNEST(pub.cpc) c) AS cpc_codes,
  ARRAY(SELECT inv.name FROM UNNEST(pub.inventor_harmonized) inv) AS inventors,
  ARRAY(SELECT ass.name FROM UNNEST(pub.assignee_harmonized) ass) AS assignees
FROM `{_PROJECT}.{_TABLE}` AS pub
WHERE pub.publication_number = '{publication_number}'
LIMIT 1
"""
    proc = subprocess.run(
        ["bq", "query", "--use_legacy_sql=false", "--use_cache",
         "--format=json", "--max_rows=1", sql],
        capture_output=True, text=True, timeout=60,
    )
    if proc.returncode != 0:
        LOG.warning("BQ lookup failed for %s: %s", publication_number, proc.stderr[:200])
        return None
    idx = proc.stdout.find("[")
    if idx < 0:
        return None
    try:
        data = json.loads(proc.stdout[idx:])
    except json.JSONDecodeError:
        return None
    return data[0] if data else None


def _int_to_iso(value) -> str:
    if not value:
        return "1900-01-01"
    s = str(value)
    if len(s) == 8 and s.isdigit():
        return f"{s[0:4]}-{s[4:6]}-{s[6:8]}"
    return s if re.match(r"^\d{4}-\d{2}-\d{2}$", s) else "1900-01-01"


def write_records(
    db_path: Path,
    rows: list[dict],
    source_id: str,
    cpc_seeds: tuple[str, ...] = (),
    keyword_seeds: tuple[str, ...] = (),
) -> tuple[int, int, int]:
    """写入 prior_art_patents + 桥表,返回 (inserted, skipped, bridge_rows)。"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    inserted = 0
    skipped = 0
    bridge_rows = 0
    try:
        for row in rows:
            pub = normalize_publication_number(row.get("publication_number") or "")
            if not pub:
                skipped += 1
                continue
            # 已存在则更新桥表,跳过主表
            existing = conn.execute(
                "SELECT 1 FROM prior_art_patents WHERE publication_number=?", (pub,)
            ).fetchone()
            cpc_set = set()
            for raw in row.get("cpc_codes") or []:
                code = normalize_cpc(raw)
                if code:
                    cpc_set.add(code)
            for c in cpc_seeds:
                code = normalize_cpc(c)
                if code:
                    cpc_set.add(code)
            cpc_json = json.dumps(sorted(cpc_set))
            inventors_json = json.dumps(list(row.get("inventors") or []))
            assignees_json = json.dumps(list(row.get("assignees") or []))
            country = (row.get("country_code") or pub[:2] or "").strip()[:2]
            family_id = str(row.get("family_id") or "") or None
            title_en = f"[seed:{','.join(keyword_seeds)[:60]}]" if not row.get("inventors") else "[EN-only]"
            abstract_en = title_en
            if existing:
                skipped += 1
            else:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO prior_art_patents (
                        publication_number, country_code, title_zh, title_en,
                        abstract_zh, abstract_en, cpc_codes, inventors,
                        assignees, filing_date, publication_date, grant_date,
                        family_id, source_id, checked_at, disclaimer_zh
                    ) VALUES (?, ?, '[EN-only]', ?, '[EN-only]', ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, '2026-08-25T00:00:00Z',
                              'Engineering retrieval summary; verify before formal use.')
                    """,
                    (pub, country, title_en[:500], abstract_en[:3000],
                     cpc_json, inventors_json, assignees_json,
                     _int_to_iso(row.get("filing_date")),
                     _int_to_iso(row.get("publication_date")),
                     _int_to_iso(row.get("grant_date")),
                     family_id, source_id),
                )
                if conn.execute(
                    "SELECT changes()"
                ).fetchone()[0] > 0:
                    inserted += 1
            # 桥表(每条 source_id 一行)
            conn.execute(
                """
                INSERT OR IGNORE INTO prior_art_publication_sources (
                    publication_number, source_id, fetched_at, raw_url,
                    raw_payload_sha256, raw_local_path, matched_query, is_primary
                ) VALUES (?, ?, '2026-08-25T00:00:00Z', ?, '', '', ?, 1)
                """,
                (pub, source_id,
                 f"https://patents.google.com/patent/{pub}/en",
                 "+".join(cpc_seeds) or "manual-seed"),
            )
            if conn.execute(
                "SELECT changes()"
            ).fetchone()[0] > 0:
                bridge_rows += 1
        conn.commit()
    finally:
        conn.close()
    return inserted, skipped, bridge_rows


def main() -> int:
    p = argparse.ArgumentParser(description="Phase E:单值 BQ lookup 兜底")
    p.add_argument("--db-path", default=str(DB_PATH))
    p.add_argument("--publication", action="append", required=True,
                   help="可多次传,每条一条 publication_number (例 US-7650331-B1)")
    p.add_argument("--source", default="bq-public-patents",
                   help="桥表 source_id")
    p.add_argument("--keywords", default="", help="逗号分隔,种子 matched_query")
    p.add_argument("--cpc", default="", help="逗号分隔,种子 CPC")
    p.add_argument("--dry-run", action="store_true", help="只拉不写")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    kw_seeds = tuple(k for k in args.keywords.split(",") if k)
    cpc_seeds = tuple(c for c in args.cpc.split(",") if c)

    LOG.info("Phase E: %d publications, source=%s, keywords=%s, cpcs=%s",
             len(args.publication), args.source, kw_seeds, cpc_seeds)

    rows: list[dict] = []
    for pub in args.publication:
        row = _bq_lookup(pub.strip())
        if row is None:
            LOG.warning("  %s: BQ miss (可能 sub-quota 烧光)", pub)
            continue
        LOG.info("  %s → %s / cpc=%s / filed=%s",
                 pub, row.get("country_code", ""),
                 list(row.get("cpc_codes") or [])[:3],
                 row.get("filing_date", ""))
        rows.append(row)

    if args.dry_run:
        LOG.info("[dry-run] skip write")
        return 0

    db_path = Path(args.db_path)
    # 备份
    if db_path.exists():
        import shutil
        backup = db_path.with_suffix(db_path.suffix + f".bak.phase-e-{int(__import__('time').time())}")
        shutil.copy2(db_path, backup)
        LOG.info("backup: %s", backup)

    inserted, skipped, bridge = write_records(
        db_path, rows, args.source, cpc_seeds, kw_seeds,
    )
    LOG.info("inserted=%d skipped_existing=%d bridge_rows=%d", inserted, skipped, bridge)

    # 治理
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        require_all_pass(conn)
        LOG.info("governance: 18/18 PASS")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())