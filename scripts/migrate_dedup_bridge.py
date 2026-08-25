"""Phase A:一次性桥表反向迁移脚本。

对已存在的 prior_art_patents 行(主要来自 google-patents-bigquery 老切片)
反向生成 prior_art_publication_sources 桥表行,raw_payload_sha256 占位 'bq-legacy'。

用法:
    python scripts/migrate_dedup_bridge.py [--db-path PATH]

内部调 build_db.install_prior_art_dedup_bridge,无重复执行保护。
"""
from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# 屏蔽 build_db 模块加载时的 AWKB 网络(同 agent_cli.py 行为)
import os  # noqa: E402
os.environ.setdefault("AWKB_ENABLED", "0")

from build_db import DB_PATH, install_prior_art_dedup_bridge  # noqa: E402

LOG = logging.getLogger("bridge_migrate")


def main() -> int:
    p = argparse.ArgumentParser(description="桥表反向迁移")
    p.add_argument("--db-path", type=Path, default=DB_PATH)
    p.add_argument("--dry-run", action="store_true", help="只统计,不入库")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.db_path.exists():
        LOG.error("db not found: %s", args.db_path)
        return 1

    # 备份
    backup = args.db_path.with_suffix(args.db_path.suffix + f".bak.bridge-{int(__import__('time').time())}")
    import shutil
    shutil.copy2(args.db_path, backup)
    LOG.info("backup created: %s", backup)

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        table_exists = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='prior_art_publication_sources'"
        ).fetchone()[0]
        if table_exists:
            before = conn.execute("SELECT COUNT(*) FROM prior_art_publication_sources").fetchone()[0]
        else:
            before = 0
        LOG.info("bridge rows before: %d (table_exists=%s)", before, bool(table_exists))

        if args.dry_run:
            LOG.info("[dry-run] skip migration")
            return 0

        install_prior_art_dedup_bridge(conn)
        after = conn.execute("SELECT COUNT(*) FROM prior_art_publication_sources").fetchone()[0]
        LOG.info("bridge rows after: %d (delta=%d)", after, after - before)
    finally:
        conn.close()

    # 验证 18 守卫
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        from src.governance.data_integrity import require_all_pass
        require_all_pass(conn)
        LOG.info("governance: 18/18 PASS")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())