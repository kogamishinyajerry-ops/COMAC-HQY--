from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "throttle_knowledge.db"
OUTPUT_DIR = ROOT / "outputs" / "governance"

from src.cross_match_builder import build_cross_matches, export_review_csv
from src.governance.data_integrity import run_all_checks
from src.governance.scope import classify_patent_scope


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def atomic_csv(path: Path, rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8-sig", newline="", dir=path.parent, delete=False
    ) as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    names = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        if not row[0].endswith(("_data", "_idx", "_content", "_docsize", "_config"))
    ]
    return {name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0] for name in names}


def scope_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for (raw,) in conn.execute("SELECT cpc_codes FROM prior_art_patents"):
        try:
            codes = json.loads(raw)
        except json.JSONDecodeError:
            counts["invalid_json"] += 1
            continue
        counts[classify_patent_scope(codes if isinstance(codes, list) else [])] += 1
    return dict(sorted(counts.items()))


def run_tests() -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["AWKB_ENABLED"] = "0"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(ROOT / "tests" / "test_governance.py")],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    return {"passed": result.returncode == 0, "returncode": result.returncode, "summary": output[-1000:]}


def refresh_cross_match(conn: sqlite3.Connection, db_path: Path) -> dict[str, int]:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = db_path.with_name(f"{db_path.name}.bak.patrol-{stamp}")
    shutil.copy2(db_path, backup)
    stats = build_cross_matches(conn)
    return {**stats.__dict__, "backup": str(backup)}


def patrol(db_path: Path = DB_PATH, refresh: bool = False) -> dict[str, object]:
    if not db_path.exists():
        raise FileNotFoundError(db_path)
    started = datetime.now().astimezone()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    refresh_stats: dict[str, object] = {}
    if refresh:
        conn.execute("BEGIN IMMEDIATE")
        try:
            refresh_stats = refresh_cross_match(conn, db_path)
            conn.commit()
        except Exception:
            conn.rollback()
            conn.close()
            raise

    checks = run_all_checks(conn)
    counts = table_counts(conn)
    scopes = scope_counts(conn)
    ontology = dict(conn.execute("SELECT ontology_type, entity_count FROM ontology_registry"))
    match_strength = dict(conn.execute("SELECT match_strength, COUNT(*) FROM cross_match GROUP BY match_strength"))
    legacy_b64d13 = conn.execute(
        """SELECT COUNT(DISTINCT p.publication_number)
           FROM prior_art_patents p, json_each(p.cpc_codes) c
           WHERE UPPER(REPLACE(REPLACE(REPLACE(c.value, ' ', ''), '–', '-'), '—', '-')) LIKE 'B64D13%'"""
    ).fetchone()[0]
    eligible_facts = conn.execute(
        "SELECT COUNT(*) FROM cross_match WHERE eligible_for_fact=1"
    ).fetchone()[0]
    unverified_facts = conn.execute(
        "SELECT COUNT(*) FROM cross_match WHERE eligible_for_fact=1 AND verification_status!='official_crosschecked'"
    ).fetchone()[0]
    excluded_legacy = scopes.get("out_of_scope", 0)
    tests = run_tests()

    audit_rows: list[list[object]] = [["check", "status", "detail"]]
    for check in checks:
        audit_rows.append([check.name, "PASS" if check.passed else "FAIL", check.detail])
    atomic_csv(OUTPUT_DIR / "data_quality_audit.csv", audit_rows)
    review_rows = export_review_csv(conn, OUTPUT_DIR / "cross_match_review.csv")
    conn.close()

    inventory = {
        "generated_at": started.isoformat(timespec="seconds"),
        "database": str(db_path),
        "table_counts": counts,
        "ontology_counts": ontology,
        "legacy_b64d13_records": legacy_b64d13,
        "prior_art_scope": scopes,
        "cross_match_strength": match_strength,
        "cross_match_review_rows": review_rows,
        "eligible_fact_rows": eligible_facts,
        "unverified_fact_rows": unverified_facts,
        "governance_checks": {
            "passed": sum(check.passed for check in checks),
            "total": len(checks),
            "failed": [check.name for check in checks if not check.passed],
        },
        "tests": tests,
        "refresh": refresh_stats,
    }
    atomic_text(
        OUTPUT_DIR / "knowledge_inventory.json",
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
    )

    status = "通过" if all(check.passed for check in checks) and tests["passed"] else "异常"
    report = f"""# HQY 油门台专利知识库巡检

- 巡检时间：{started.strftime('%Y-%m-%d %H:%M:%S %z')}
- 总体状态：{status}
- 治理守卫：{sum(check.passed for check in checks)}/{len(checks)}
- 回归测试：{'通过' if tests['passed'] else '失败'}
- 先有技术：{counts.get('prior_art_patents', 0)} 件
- 本体实体：{sum(ontology.values())} 个，4 个本体域
- 跨源建议：{counts.get('cross_match', 0)} 条，其中中等证据 {match_strength.get('MEDIUM', 0)} 条、弱证据 {match_strength.get('WEAK', 0)} 条
- 自动事实认定：{eligible_facts} 条；所有未核验建议默认不进入事实口径

## 关键边界

1. 历史 BigQuery 切片中有 {legacy_b64d13} 件带 `B64D13` 分类，其中 {excluded_legacy} 件仅落在非核心范围。本体层已将 `B64D13/00` 标为非油门台核心范围。
2. 这些原始记录继续可检索，但不会自动生成法规条款关联。
3. `cross_match` 只产待审建议。只有官方交叉核验后的强证据才允许进入事实口径。
4. 本库用于先有技术与工程检索，不构成专利法律意见，也不替代适航条款原文核对。

## 四路产物

- `knowledge_inventory.json`：机器可读资产清单
- `data_quality_audit.csv`：16 项治理守卫
- `cross_match_review.csv`：专利与法规条款待审建议
- `patrol_latest.md`：本巡检报告
"""
    atomic_text(OUTPUT_DIR / "patrol_latest.md", report)
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--refresh-cross-match", action="store_true")
    args = parser.parse_args()
    result = patrol(args.db, args.refresh_cross_match)
    checks = result["governance_checks"]
    tests = result["tests"]
    print(f"HQY知识库巡检 {result['generated_at']}")
    print(f"治理守卫 {checks['passed']}/{checks['total']}")
    print(f"回归测试 {'通过' if tests['passed'] else '失败'}")
    print(f"先有技术 {result['table_counts'].get('prior_art_patents', 0)} 件")
    print(f"跨源待审 {result['cross_match_review_rows']} 条")
    print(f"历史非核心范围 {result['prior_art_scope'].get('out_of_scope', 0)} 件")
    print(f"产物目录 {OUTPUT_DIR}")
    return 0 if checks["passed"] == checks["total"] and tests["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
