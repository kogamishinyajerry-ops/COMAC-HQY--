"""Phase A:prior_art 检索池通用 loader。

调用 3 个 adapter(USPTO / EPO / Google),统一入库到:
  - prior_art_patents(主表,按 publication_number INSERT OR IGNORE)
  - prior_art_publication_sources(桥表,记录多源 + raw_payload + is_primary)
  - chunks(检索片段,可选)

决策原则(plan §3.2):
- 首次入库:is_primary=1,source_id = adapter.source_id
- 跨源重号:不在 prior_art_patents 改 source_id,只往桥表 append is_primary=0
- 字段冲突:resolve_overlap() 跨源合并

用法:
    python scripts/import_prior_art_phase_a.py --dry-run
    python scripts/import_prior_art_phase_a.py --source uspto-od --keyword FADEC --cpc F02C9/00
    python scripts/import_prior_art_phase_a.py --bridge-migrate
"""
from __future__ import annotations

import json
import logging
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.governance.data_integrity import require_all_pass
from src.governance.normalize import normalize_publication_number
from src.prior_art_adapters import (  # noqa: E402
    ADAPTERS,
    AdapterError,
    BaseAdapter,
    PriorArtQuery,
    PriorArtRecord,
    all_adapters,
    resolve_overlap,
    to_db_dict,
)

DB_PATH = ROOT / "data" / "throttle_knowledge.db"
RAW_DIR = ROOT / "data" / "source_archive" / "raw"
LOG = logging.getLogger("phase_a")


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _adapter_by_name(name: str) -> BaseAdapter:
    if name not in ADAPTERS:
        raise SystemExit(f"unknown adapter: {name}; choices: {list(ADAPTERS)}")
    return ADAPTERS[name]()


# ============================================================
# health + collect
# ============================================================

def health_check_all() -> dict[str, bool]:
    out = {}
    for cls_name, cls in ADAPTERS.items():
        try:
            adapter = cls()
            ok = adapter.health_check()
            out[cls_name] = ok
            LOG.info("health_check %s: %s", cls_name, "OK" if ok else "FAIL")
        except Exception as exc:  # noqa: BLE001
            LOG.warning("health_check %s raised: %s", cls_name, exc)
            out[cls_name] = False
    return out


def collect_records(
    adapter: BaseAdapter,
    query: PriorArtQuery,
) -> list[PriorArtRecord]:
    out = []
    try:
        for r in adapter.search(query):
            out.append(r)
    except AdapterError as exc:
        LOG.warning("adapter %s raised AdapterError: %s", adapter.source_id, exc)
    return out


# ============================================================
# 入库 + 桥表
# ============================================================

def write_records(
    conn: sqlite3.Connection,
    records: list[PriorArtRecord],
    dry_run: bool = False,
) -> dict:
    """按 publication_number 分组,跨源 resolve_overlap,然后入库。

    返回 {inserted, skipped_existing, bridge_rows, orphans}
    """
    if not records:
        return {"inserted": 0, "skipped_existing": 0, "bridge_rows": 0, "orphans": 0}

    grouped: dict[str, list[PriorArtRecord]] = defaultdict(list)
    for r in records:
        grouped[r.publication_number].append(r)

    inserted = 0
    skipped = 0
    bridge_rows = 0

    for pub, recs in grouped.items():
        primary_source = recs[0].source_id
        merged = resolve_overlap(recs)
        existing = conn.execute(
            "SELECT source_id FROM prior_art_patents WHERE publication_number = ?", (pub,)
        ).fetchone()

        if existing:
            existing_source = existing[0]
            merged_dict = to_db_dict(merged)
            merged_dict["source_id"] = existing_source
            skipped += 1
            for r in recs:
                bridge_rows += _write_bridge(conn, pub, r, is_primary=False, dry_run=dry_run)
            LOG.info("[%s] skip-existing pub=%s (keep source_id=%s)", primary_source, pub, existing_source)
            continue

        merged_dict = to_db_dict(merged)
        if dry_run:
            inserted += 1
            LOG.info("[dry-run] would insert pub=%s source=%s", pub, primary_source)
            continue

        conn.execute(
            """
            INSERT INTO prior_art_patents (
                publication_number, country_code, title_zh, title_en,
                abstract_zh, abstract_en, cpc_codes, inventors, assignees,
                filing_date, publication_date, grant_date, family_id,
                source_id, checked_at, disclaimer_zh
            ) VALUES (
                :publication_number, :country_code, :title_zh, :title_en,
                :abstract_zh, :abstract_en, :cpc_codes, :inventors, :assignees,
                :filing_date, :publication_date, :grant_date, :family_id,
                :source_id, :checked_at, :disclaimer_zh
            )
            """,
            merged_dict,
        )
        inserted += 1
        bridge_rows += _write_bridge(conn, pub, merged, is_primary=True, dry_run=dry_run)
        for r in recs:
            if r.source_id != primary_source:
                bridge_rows += _write_bridge(conn, pub, r, is_primary=False, dry_run=dry_run)

    if not dry_run:
        conn.commit()
    return {"inserted": inserted, "skipped_existing": skipped, "bridge_rows": bridge_rows, "orphans": 0}


def _write_bridge(
    conn: sqlite3.Connection,
    pub: str,
    record: PriorArtRecord,
    is_primary: bool,
    dry_run: bool,
) -> int:
    if dry_run:
        return 1
    fetched_at = _utc_now()
    matched_query = f"{pub}"        # 简化,实际可记录 keyword+cpc
    conn.execute(
        """
        INSERT OR IGNORE INTO prior_art_publication_sources (
            publication_number, source_id, fetched_at, raw_url,
            raw_payload_sha256, raw_local_path, matched_query, is_primary
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            pub, record.source_id, fetched_at, record.raw_url,
            record.raw_payload_sha256, "", matched_query, int(is_primary),
        ),
    )
    return 1


# ============================================================
# 主流程
# ============================================================

def run_import(
    source: str = "all",
    keywords: tuple[str, ...] = ("reverse thrust", "FADEC", "EEC"),
    cpcs: tuple[str, ...] = ("B64D31/00", "F02C9/00", "F02C9/28", "F02C9/46"),
    limit_per_query: int = 500,
    filing_from: str = "2000-01-01",
    dry_run: bool = False,
) -> int:
    health = health_check_all()
    sources = list(ADAPTERS) if source == "all" else [source]

    q = PriorArtQuery(
        keywords=keywords,
        cpc_prefixes=cpcs,
        filing_date_from=filing_from,
        per_query_limit=limit_per_query,
    )
    total_stats = {"inserted": 0, "skipped_existing": 0, "bridge_rows": 0, "orphans": 0}
    for src in sources:
        if not health.get(src, False):
            LOG.warning("skip unhealthy adapter: %s", src)
            continue
        adapter = ADAPTERS[src]()
        records = collect_records(adapter, q)
        LOG.info("[%s] collected %d records", src, len(records))
        conn = _connect()
        try:
            stats = write_records(conn, records, dry_run=dry_run)
            for k, v in stats.items():
                total_stats[k] += v
        finally:
            conn.close()

    LOG.info("=== phase A summary ===")
    LOG.info("source=%s keywords=%s cpcs=%s dry_run=%s", source, keywords, cpcs, dry_run)
    LOG.info("inserted=%d skipped_existing=%d bridge_rows=%d orphans=%d",
             total_stats["inserted"], total_stats["skipped_existing"],
             total_stats["bridge_rows"], total_stats["orphans"])

    if not dry_run:
        conn = _connect()
        try:
            require_all_pass(conn)
            LOG.info("governance: 18/18 PASS")
        finally:
            conn.close()
    return 0


def run_bridge_migrate() -> int:
    """对老 prior_art_patents 行反向生成桥表(占位 bq-legacy)。"""
    conn = _connect()
    try:
        from build_db import install_prior_art_dedup_bridge
        install_prior_art_dedup_bridge(conn)
        n = conn.execute("SELECT COUNT(*) FROM prior_art_publication_sources").fetchone()[0]
        LOG.info("bridge rows after migrate: %d", n)
    finally:
        conn.close()
    return 0


def main() -> int:
    import argparse
    p = argparse.ArgumentParser(description="Phase A prior_art loader")
    p.add_argument("--source", default="all", choices=["all"] + list(ADAPTERS))
    p.add_argument("--keyword", action="append", default=None)
    p.add_argument("--cpc", action="append", default=None)
    p.add_argument("--limit-per-query", type=int, default=500)
    p.add_argument("--filing-from", default="2000-01-01")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--bridge-migrate", action="store_true",
                   help="只跑桥表反向回填,不入新数据")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    if args.bridge_migrate:
        return run_bridge_migrate()

    keywords = tuple(args.keyword) if args.keyword else ("reverse thrust", "FADEC", "EEC")
    cpcs = tuple(args.cpc) if args.cpc else ("B64D31/00", "F02C9/00", "F02C9/28", "F02C9/46")
    return run_import(
        source=args.source,
        keywords=keywords,
        cpcs=cpcs,
        limit_per_query=args.limit_per_query,
        filing_from=args.filing_from,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())