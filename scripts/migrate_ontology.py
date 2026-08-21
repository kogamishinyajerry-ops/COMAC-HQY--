from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "throttle_knowledge.db"

from src.cross_match_builder import build_cross_matches, create_schema, export_review_csv
from src.governance.data_integrity import require_all_pass
from src.ontology_loader import install_ontology


def column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def add_column(conn: sqlite3.Connection, table: str, definition: str) -> None:
    name = definition.split()[0]
    if name not in column_names(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {definition}")


def snapshot_counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    result = {}
    for table in ("prior_art_patents", "chunks", "prior_art_relevance"):
        if table in tables:
            result[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if "prior_art_patents" in tables:
        result["translated_prior_art"] = conn.execute(
            """SELECT COUNT(*) FROM prior_art_patents
               WHERE abstract_zh NOT IN ('', '[EN-only]', '[zh pending]')"""
        ).fetchone()[0]
    return result


def migrate(db_path: Path, backup: bool = True, build_matches: bool = True) -> dict:
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.bak.ontology-{stamp}")
    if backup:
        shutil.copy2(db_path, backup_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    before = snapshot_counts(conn)
    try:
        conn.execute("BEGIN IMMEDIATE")
        add_column(conn, "sources", "license TEXT NOT NULL DEFAULT 'See source terms'")
        add_column(
            conn,
            "sources",
            "disclaimer_zh TEXT NOT NULL DEFAULT 'Engineering retrieval summary; verify original source before formal use.'",
        )
        add_column(
            conn,
            "sources",
            "disclaimer_en TEXT NOT NULL DEFAULT 'Engineering retrieval summary; verify original source before formal use.'",
        )
        add_column(conn, "components", "source_id TEXT REFERENCES sources(id)")
        add_column(conn, "invention_patterns", "source_id TEXT REFERENCES sources(id)")

        conn.execute(
            """INSERT OR IGNORE INTO sources
               (id, kind, quality, organization, title_zh, title_en, url, note_zh, note_en,
                checked_at, license, disclaimer_zh, disclaimer_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "hqy-curated-ontology", "curated_ontology", "curated", "HQY Throttle Atlas",
                "HQY 油门台专利助手工程本体 v1",
                "HQY Throttle Atlas Engineering Ontology v1",
                "local://ontology/hqy-throttle-atlas-v1",
                "项目内部整理的飞机族、油门台组件、法规条款与 CPC 范围本体。[archive_policy=metadata_only]",
                "Project-curated aircraft, throttle-component, regulatory-clause and CPC scope ontology.",
                "2026-07-29", "Project internal curated data",
                "仅用于工程检索和概念对齐，不替代适航、法律或原厂设计结论。",
                "For engineering retrieval and concept alignment only; not an airworthiness, legal or OEM design determination.",
            ),
        )
        conn.execute(
            "UPDATE components SET source_id='hqy-curated-ontology' WHERE source_id IS NULL OR source_id=''"
        )
        conn.execute(
            "UPDATE invention_patterns SET source_id='hqy-curated-ontology' WHERE source_id IS NULL OR source_id=''"
        )
        conn.execute(
            """UPDATE sources
               SET license='CC BY 4.0',
                   disclaimer_zh='先有技术检索辅助，不构成新颖性、创造性、自由实施或侵权法律意见。',
                   disclaimer_en='Prior-art search aid only; not a novelty, inventive-step, freedom-to-operate or infringement opinion.',
                   note_zh='Google Patents 公开数据集，CC BY 4.0 许可。历史切片包含 B64D13/00、B60K26/00、B60K41/00；B64D13/00 已在本体层标为非油门台核心范围，原始记录保留检索但不自动进入跨源事实口径。[archive_policy=download]',
                   note_en='Google Patents public dataset under CC BY 4.0. The historical slice includes B64D13/00, B60K26/00 and B60K41/00. B64D13/00 is out of scope for throttle controls; records remain searchable but cannot enter cross-source fact output automatically. [archive_policy=download]'
               WHERE id='google-patents-bigquery'"""
        )

        create_schema(conn)
        conn.execute("DELETE FROM cross_match")
        conn.execute("DELETE FROM clause_mentions")
        ontology_counts = install_ontology(conn)
        match_stats = build_cross_matches(conn) if build_matches else None
        checks = require_all_pass(conn)
        after = snapshot_counts(conn)
        if before != after:
            raise RuntimeError(f"protected data counts changed: before={before}, after={after}")
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise

    review_count = export_review_csv(conn, ROOT / "outputs" / "governance" / "cross_match_review.csv")
    conn.close()

    manifest_path = db_path.parent / "rag_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    manifest.update(
        {
            "version": 7,
            "generated_at": "2026-07-29",
            "ontology_tables": ["ontology_registry", "ontology_entities", "ontology_aliases", "ontology_relations"],
            "cross_source_tables": ["clause_mentions", "cross_match"],
            "ontology_files": [
                "aircraft_families.yaml", "throttle_components.yaml",
                "regulatory_clauses.yaml", "cpc_taxonomy.yaml",
            ],
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "database": str(db_path),
        "backup": str(backup_path) if backup else "",
        "protected_counts": before,
        "ontology_counts": ontology_counts,
        "cross_match": match_stats.__dict__ if match_stats else {},
        "review_rows": review_count,
        "checks": len(checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--skip-cross-match", action="store_true")
    args = parser.parse_args()
    result = migrate(args.db, not args.no_backup, not args.skip_cross_match)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
