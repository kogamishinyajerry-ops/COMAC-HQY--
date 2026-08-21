"""HQY → P-ACE 产物级 export:精选数据导出为 pace_export.yaml。

设计原则(对齐 engine-kb-bridge 零耦合消费 P-ACE 模式的镜像对称):
- 单一职责:读 SQLite + ontology yaml → 吐一个 pace_export.yaml
- P-ACE 只读产物,不 import HQY 代码,不连 HQY SQLite
- 精选 curated 数据(不是全量 prior_art_patents 检索池):
  * 8 条自建 curated 专利(patents 表)
  * 36 条 cross_match(专利↔条款,半自动三轨证据制)
  * 16 条 throttle_component 本体实体
  * 15 条 regulatory_clause 本体实体(5 条款号 × 3 authority)
- 原子写(tmp + os.replace)
- utf-8 编码(macOS Write 中文 GBK 坑)

入口:
    python -m src.export_for_pace
    python src/export_for_pace.py

产物路径:outputs/pace_export.yaml(HQY 自己 outputs/ 下)
P-ACE 通过 env var HQY_EXPORT_YAML 读(镜像 PACE_BRIDGE_YAML 模式)。
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "throttle_knowledge.db"
ONTOLOGY_DIR = ROOT / "ontology"
OUTPUT_PATH = ROOT / "outputs" / "pace_export.yaml"

EXPORT_VERSION = "0.1.0"


def _load_curated_patents(db_path: Path) -> list[dict]:
    """读 patents 表(8 条自建 curated 专利,不是 prior_art_patents 检索池)。"""
    if not db_path.exists():
        return []
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            "SELECT id, publication_no, jurisdiction, assignee, priority_date, "
            "title_zh, title_en, status_zh, status_en, applicable_aircraft_json, source_id "
            "FROM patents ORDER BY id"
        ).fetchall()
        return [{
            "id": r["id"],
            "publication_no": r["publication_no"],
            "jurisdiction": r["jurisdiction"],
            "assignee": r["assignee"],
            "priority_date": r["priority_date"],
            "title_zh": r["title_zh"],
            "title_en": r["title_en"],
            "status_zh": r["status_zh"],
            "status_en": r["status_en"],
            "applicable_aircraft": json.loads(r["applicable_aircraft_json"]) if r["applicable_aircraft_json"] else [],
            "source_id": r["source_id"],
        } for r in rows]
    finally:
        db.close()


def _load_cross_matches(db_path: Path) -> list[dict]:
    """读 cross_match 表 — 只 export curated(subject_type=patent) 36 条。

    设计意图(对齐 docstring & P-ACE 第六 panel 边界):
    - pace_export.yaml 是给 P-ACE 看的精选产物,只含 8 条 curated 专利的关联
    - prior_art_patent 的 cross_match(2026-08 FADEC/EEC v2 重抓后增至 1755 条)留在 DB RAG 池,
      供 WorkBuddy 等场景按需检索,但不进 PACE 第六 panel(边界一刀切避免 panel 被噪声稀释)
    - 想让 FADEC/EEC 升上 PACE panel?走"半自动 promote"流程:人工选 prior_art →
      patents 表 → 走 curated cross_match → 再 export
    """
    if not db_path.exists():
        return []
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            "SELECT id, subject_type, subject_id, object_type, object_id, "
            "match_strength, score, basis_json, source_credibility_tier, "
            "evidence_strength, verification_status, eligible_for_fact, created_at "
            "FROM cross_match WHERE subject_type='patent' "
            "ORDER BY subject_id, object_id"
        ).fetchall()
        out = []
        for r in rows:
            # basis_json 解析(含 matched_components / matched_terms / cpc_scope)
            try:
                basis = json.loads(r["basis_json"]) if r["basis_json"] else {}
            except json.JSONDecodeError:
                basis = {}
            out.append({
                "id": r["id"],
                "subject_type": r["subject_type"],
                "subject_id": r["subject_id"],
                "object_type": r["object_type"],
                "object_id": r["object_id"],  # HQY 本体 id 原样保留(clause:far-25.777)
                "match_strength": r["match_strength"],
                "score": r["score"],
                "basis": {
                    "matched_components": basis.get("matched_components", []),
                    "matched_terms": basis.get("matched_terms", []),
                    "cpc_scope": basis.get("cpc_scope", "unknown"),
                    "applicable_aircraft": basis.get("applicable_aircraft", []),
                    "rule": basis.get("rule", ""),
                },
                "source_credibility_tier": r["source_credibility_tier"],
                "evidence_strength": r["evidence_strength"],
                "verification_status": r["verification_status"],
                "eligible_for_fact": bool(r["eligible_for_fact"]),
                "created_at": r["created_at"],
            })
        return out
    finally:
        db.close()


def _load_throttle_components(ontology_dir: Path) -> list[dict]:
    """读 ontology/throttle_components.yaml 的 16 实体(精简版,含 FADEC/EEC 子层)。"""
    path = ontology_dir / "throttle_components.yaml"
    if not path.exists():
        return []
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = []
    for ent in doc.get("entities", []):
        # 优先读本体里的 component_id 字段(下划线命名,与 cross_match.basis.matched_components 一致)
        # 不从 id 切(切出来是连字符,会与 matched_components 命名空间不一致)
        cid = ent.get("component_id", "")
        if not cid and ":" in ent.get("id", ""):
            # 兜底:无 component_id 字段时从 id 切(老格式兼容)
            cid = ent.get("id", "").split(":", 1)[-1]
        out.append({
            "id": ent.get("id", ""),
            "label_zh": ent.get("label_zh", ""),
            "label_en": ent.get("label_en", ""),
            "component_id": cid,  # 用于 join cross_match.basis.matched_components
            "scope_level": ent.get("scope_level", ""),
        })
    return out


def _load_clause_entities(ontology_dir: Path) -> list[dict]:
    """读 ontology/regulatory_clauses.yaml 的 15 实体(5 条款号 × 3 authority)。"""
    path = ontology_dir / "regulatory_clauses.yaml"
    if not path.exists():
        return []
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = []
    for ent in doc.get("entities", []):
        out.append({
            "id": ent.get("id", ""),  # clause:far-25.777
            "label_zh": ent.get("label_zh", ""),
            "label_en": ent.get("label_en", ""),
            "authority": ent.get("authority", ""),
            "regulation": ent.get("regulation", ""),
            "clause_number": ent.get("clause_number", ""),
        })
    return out


def build_export(
    db_path: Path = DB_PATH,
    ontology_dir: Path = ONTOLOGY_DIR,
) -> dict:
    """构建 export 数据结构(dict,尚未序列化)。"""
    patents = _load_curated_patents(db_path)
    cross_matches = _load_cross_matches(db_path)
    components = _load_throttle_components(ontology_dir)
    clause_entities = _load_clause_entities(ontology_dir)

    return {
        "_meta": {
            "source": "HQY-throttle-patent-assistant",
            "version": EXPORT_VERSION,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "db_path": str(db_path.relative_to(ROOT)) if db_path.is_relative_to(ROOT) else str(db_path),
            "hqy_note": "curated 专利与适航条款的人工/半自动关联,非全量检索池",
        },
        "coverage": {
            "curated_patents": len(patents),
            "cross_matches": len(cross_matches),
            "throttle_components": len(components),
            "clause_entities": len(clause_entities),
        },
        "curated_patents": patents,
        "cross_matches": cross_matches,
        "throttle_components": components,
        "clause_entities": clause_entities,
    }


def write_export(
    data: dict,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """原子写 yaml(tmp + os.replace,utf-8 编码)。返回写入路径。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    # 原子写:先写 tmp 再 replace(macOS Write 中文 GBK 坑,用 open encoding=utf-8)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, output_path)
    return output_path


def export(output_path: Path = OUTPUT_PATH) -> Path:
    """完整 export 流程:build + write。"""
    data = build_export()
    return write_export(data, output_path)


def main() -> int:
    """CLI 入口:python -m src.export_for_pace。"""
    out = export()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    cov = data.get("coverage", {})
    print(f"=== HQY → P-ACE export 完成 ===")
    print(f"产物: {out}")
    print(f"  curated_patents:      {cov.get('curated_patents', 0)}")
    print(f"  cross_matches:        {cov.get('cross_matches', 0)}")
    print(f"  throttle_components:  {cov.get('throttle_components', 0)}")
    print(f"  clause_entities:      {cov.get('clause_entities', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
