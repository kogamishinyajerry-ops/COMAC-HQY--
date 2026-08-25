from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass

# cross_match.subject_type 允许的取值集合; 数据完整性防御
# 新增 subject_type 必须同时更新 cross_match_builder.py 的 _build_cross_matches()
# 与此处常量, 否则会被 cross_match_subject_type_allow_list 守卫标红
ALLOWED_CROSS_MATCH_SUBJECT_TYPES: tuple[str, ...] = ("patent", "prior_art_patent")


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def _result(name: str, count: int, expectation: str = "zero") -> CheckResult:
    passed = count == 0 if expectation == "zero" else count > 0
    return CheckResult(name, passed, str(count))


def run_all_checks(conn: sqlite3.Connection) -> list[CheckResult]:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required = {
        "sources", "components", "invention_patterns", "prior_art_patents",
        "ontology_registry", "ontology_entities", "ontology_aliases", "ontology_relations",
        "clause_mentions", "cross_match",
    }
    checks: list[CheckResult] = []

    fk_issues = len(conn.execute("PRAGMA foreign_key_check").fetchall())
    checks.append(_result("foreign_key_integrity", fk_issues))
    checks.append(CheckResult("required_tables", required <= tables, ",".join(sorted(required - tables))))

    registry_count = conn.execute("SELECT COUNT(*) FROM ontology_registry").fetchone()[0]
    checks.append(CheckResult("ontology_registry_four", registry_count == 4, str(registry_count)))

    floors = {"aircraft_family": 9, "throttle_component": 16, "regulatory_clause": 15, "cpc_class": 20}
    floor_failures = []
    for ontology_type, floor in floors.items():
        count = conn.execute(
            "SELECT COUNT(*) FROM ontology_entities WHERE ontology_type=?", (ontology_type,)
        ).fetchone()[0]
        if count < floor:
            floor_failures.append(f"{ontology_type}:{count}<{floor}")
    model_ids = {row[0] for row in conn.execute("SELECT id FROM models")}
    for entity_id, raw_attributes in conn.execute(
        "SELECT id, attributes_json FROM ontology_entities WHERE ontology_type='aircraft_family'"
    ):
        for model_id in json.loads(raw_attributes).get("model_ids", []):
            if model_id not in model_ids:
                floor_failures.append(f"{entity_id}:unknown_model:{model_id}")
    checks.append(CheckResult("ontology_entity_floors", not floor_failures, ";".join(floor_failures)))

    source_missing = conn.execute(
        """SELECT COUNT(*) FROM sources
           WHERE id='' OR organization='' OR url='' OR quality=''"""
    ).fetchone()[0]
    checks.append(_result("source_provenance", source_missing))

    component_missing = conn.execute(
        "SELECT COUNT(*) FROM components WHERE source_id IS NULL OR source_id=''"
    ).fetchone()[0]
    checks.append(_result("component_source_id", component_missing))

    pattern_missing = conn.execute(
        "SELECT COUNT(*) FROM invention_patterns WHERE source_id IS NULL OR source_id=''"
    ).fetchone()[0]
    checks.append(_result("invention_pattern_source_id", pattern_missing))

    alias_orphans = conn.execute(
        """SELECT COUNT(*) FROM ontology_aliases a
           LEFT JOIN ontology_entities e ON e.id=a.entity_id WHERE e.id IS NULL"""
    ).fetchone()[0]
    checks.append(_result("ontology_alias_orphans", alias_orphans))

    relation_orphans = conn.execute(
        """SELECT COUNT(*) FROM ontology_relations r
           LEFT JOIN ontology_entities s ON s.id=r.subject_id
           LEFT JOIN ontology_entities o ON o.id=r.object_id
           WHERE s.id IS NULL OR o.id IS NULL"""
    ).fetchone()[0]
    checks.append(_result("ontology_relation_orphans", relation_orphans))

    excluded_bad = conn.execute(
        """SELECT COUNT(*) FROM ontology_entities
           WHERE id LIKE 'cpc:B64D13%' AND scope_level!='out_of_scope'"""
    ).fetchone()[0]
    checks.append(_result("cpc_b64d13_excluded", excluded_bad))

    core_bad = conn.execute(
        """SELECT COUNT(*) FROM ontology_entities
           WHERE id LIKE 'cpc:B64D31%' AND scope_level!='core'"""
    ).fetchone()[0]
    checks.append(_result("cpc_b64d31_core", core_bad))

    trace_missing = conn.execute(
        """SELECT COUNT(*) FROM prior_art_patents p
           LEFT JOIN sources s ON s.id=p.source_id WHERE s.id IS NULL"""
    ).fetchone()[0]
    checks.append(_result("prior_art_traceability", trace_missing))

    invalid_cpc = conn.execute(
        "SELECT COUNT(*) FROM prior_art_patents WHERE json_valid(cpc_codes)=0"
    ).fetchone()[0]
    checks.append(_result("prior_art_cpc_json", invalid_cpc))

    unverified_fact = conn.execute(
        """SELECT COUNT(*) FROM cross_match
           WHERE eligible_for_fact=1 AND verification_status!='official_crosschecked'"""
    ).fetchone()[0]
    checks.append(_result("cross_match_fail_closed", unverified_fact))

    match_without_mention = conn.execute(
        """SELECT COUNT(*) FROM cross_match x
           LEFT JOIN clause_mentions m
             ON m.subject_type=x.subject_type AND m.subject_id=x.subject_id
            AND m.clause_id=x.object_id
           LEFT JOIN patents p ON x.subject_type='patent' AND p.id=x.subject_id
           LEFT JOIN prior_art_patents pa
             ON x.subject_type='prior_art_patent' AND pa.publication_number=x.subject_id
           WHERE m.id IS NULL
              OR (x.subject_type='patent' AND p.id IS NULL)
              OR (x.subject_type='prior_art_patent' AND pa.publication_number IS NULL)"""
    ).fetchone()[0]
    checks.append(_result("cross_match_has_evidence", match_without_mention))

    # 显式枚举允许的 subject_type; 任何越界值(手工注入或未来 schema 漂移)都会被标红
    placeholders = ",".join("?" * len(ALLOWED_CROSS_MATCH_SUBJECT_TYPES))
    unknown_subject_type = conn.execute(
        f"SELECT COUNT(*) FROM cross_match WHERE subject_type NOT IN ({placeholders})",
        ALLOWED_CROSS_MATCH_SUBJECT_TYPES,
    ).fetchone()[0]
    checks.append(_result("cross_match_subject_type_allow_list", unknown_subject_type))

    boundary_missing = conn.execute(
        """SELECT COUNT(*) FROM sources
           WHERE license='' OR disclaimer_zh='' OR disclaimer_en=''"""
    ).fetchone()[0]
    checks.append(_result("source_license_and_boundaries", boundary_missing))

    # Phase A 跨源桥表一致性:
    # 1) 桥表每行 (pub, source_id) 的 source_id 必须在 sources 表(无孤儿)
    # 2) prior_art_patents 每行至少 1 条 is_primary=1 桥表记录
    bridge_orphans = conn.execute(
        """SELECT COUNT(*) FROM prior_art_publication_sources ps
           LEFT JOIN sources s ON s.id=ps.source_id WHERE s.id IS NULL"""
    ).fetchone()[0]
    bridge_no_primary = conn.execute(
        """SELECT COUNT(*) FROM prior_art_patents pa
           WHERE NOT EXISTS (
               SELECT 1 FROM prior_art_publication_sources ps
               WHERE ps.publication_number=pa.publication_number AND ps.is_primary=1
           )"""
    ).fetchone()[0]
    bridge_total_failures = bridge_orphans + bridge_no_primary
    checks.append(_result(
        "prior_art_dedup_bridge_consistency", bridge_total_failures
    ))

    return checks


def require_all_pass(conn: sqlite3.Connection) -> list[CheckResult]:
    checks = run_all_checks(conn)
    failed = [check for check in checks if not check.passed]
    if failed:
        detail = "; ".join(f"{check.name}={check.detail}" for check in failed)
        raise RuntimeError(f"governance checks failed: {detail}")
    return checks
