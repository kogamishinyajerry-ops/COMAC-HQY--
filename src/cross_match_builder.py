from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .governance.evidence import evidence_strength, is_fact_eligible, source_credibility_tier
from .governance.normalize import normalize_text
from .governance.scope import classify_patent_scope


@dataclass(frozen=True)
class BuildStats:
    patents_scanned: int
    excluded_scope: int
    mentions: int
    matches: int
    strong: int
    medium: int
    weak: int


def create_schema(conn: sqlite3.Connection) -> None:
    schema = (
        """
        CREATE TABLE IF NOT EXISTS clause_mentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_type TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            publication_number TEXT NOT NULL,
            clause_id TEXT NOT NULL REFERENCES ontology_entities(id) ON DELETE CASCADE,
            matched_terms_json TEXT NOT NULL,
            matched_components_json TEXT NOT NULL,
            cpc_scope TEXT NOT NULL,
            score REAL NOT NULL,
            strength TEXT NOT NULL CHECK(strength IN ('STRONG', 'MEDIUM', 'WEAK')),
            evidence_excerpt TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(subject_type, subject_id, clause_id)
        );
        CREATE TABLE IF NOT EXISTS cross_match (
            id TEXT PRIMARY KEY,
            subject_type TEXT NOT NULL,
            subject_id TEXT NOT NULL,
            object_type TEXT NOT NULL,
            object_id TEXT NOT NULL REFERENCES ontology_entities(id),
            match_strength TEXT NOT NULL CHECK(match_strength IN ('STRONG', 'MEDIUM', 'WEAK')),
            score REAL NOT NULL,
            basis_json TEXT NOT NULL,
            source_credibility_tier TEXT NOT NULL,
            evidence_strength TEXT NOT NULL,
            verification_status TEXT NOT NULL,
            eligible_for_fact INTEGER NOT NULL CHECK(eligible_for_fact IN (0, 1)),
            created_at TEXT NOT NULL,
            UNIQUE(subject_type, subject_id, object_type, object_id)
        );
        CREATE INDEX IF NOT EXISTS idx_clause_mentions_clause ON clause_mentions(clause_id, strength);
        CREATE INDEX IF NOT EXISTS idx_clause_mentions_subject ON clause_mentions(subject_type, subject_id);
        CREATE INDEX IF NOT EXISTS idx_cross_match_subject ON cross_match(subject_type, subject_id);
        CREATE INDEX IF NOT EXISTS idx_cross_match_object ON cross_match(object_type, object_id);
        CREATE INDEX IF NOT EXISTS idx_cross_match_review ON cross_match(verification_status, match_strength, score DESC);
        """
    )
    for statement in schema.split(";"):
        if statement.strip():
            conn.execute(statement)


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _groups(attributes: dict[str, Any]) -> list[list[str]]:
    raw = attributes.get("keyword_groups", [])
    return [[normalize_text(term) for term in group if normalize_text(term)] for group in raw]


def _matched_groups(text: str, groups: list[list[str]]) -> tuple[int, list[str]]:
    matched: list[str] = []
    count = 0
    for group in groups:
        hits = [term for term in group if term in text]
        if hits:
            count += 1
            matched.extend(hits)
    return count, list(dict.fromkeys(matched))


def _excerpt(text: str, terms: list[str], length: int = 360) -> str:
    positions = [text.find(term) for term in terms if text.find(term) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - 100)
    return text[start : start + length].strip()


def _build_cross_matches(conn: sqlite3.Connection) -> BuildStats:
    conn.execute("DELETE FROM cross_match")
    conn.execute("DELETE FROM clause_mentions")

    clauses = []
    for row in conn.execute(
        "SELECT id, attributes_json FROM ontology_entities WHERE ontology_type='regulatory_clause' ORDER BY id"
    ):
        attributes = json.loads(row[1])
        clauses.append(
            {
                "id": row[0],
                "groups": _groups(attributes),
                "component_ids": set(attributes.get("component_ids", [])),
            }
        )

    components = []
    for row in conn.execute(
        "SELECT id, attributes_json FROM ontology_entities WHERE ontology_type='throttle_component' ORDER BY id"
    ):
        attributes = json.loads(row[1])
        component_id = attributes.get("component_id")
        if component_id:
            components.append((component_id, _groups(attributes)))

    source_quality = {
        row[0]: row[1] for row in conn.execute("SELECT id, quality FROM sources")
    }
    candidates: list[dict[str, Any]] = []
    for row in conn.execute(
        """SELECT publication_number, title_zh, title_en, abstract_zh, abstract_en,
                  cpc_codes, source_id
           FROM prior_art_patents ORDER BY publication_number"""
    ):
        candidates.append(
            {
                "subject_type": "prior_art_patent",
                "subject_id": row[0],
                "publication_number": row[0],
                "text": " ".join(row[1:5]),
                "cpc_codes": _json_list(row[5]),
                "applicable_aircraft": [],
                "source_id": row[6],
                "curated": False,
            }
        )
    for row in conn.execute(
        """SELECT id, publication_no, title_zh, title_en, claim_zh, claim_en,
                  change_zh_json, change_en_json, tags_json, applicable_aircraft_json, source_id
           FROM patents ORDER BY id"""
    ):
        candidates.append(
            {
                "subject_type": "patent",
                "subject_id": row[0],
                "publication_number": row[1],
                "text": " ".join(str(value or "") for value in row[2:9]),
                "cpc_codes": [],
                "applicable_aircraft": _json_list(row[9]),
                "source_id": row[10],
                "curated": True,
            }
        )

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    excluded_scope = mentions = matches = strong = medium = weak = 0

    for patent in candidates:
        cpc_scope = classify_patent_scope(patent["cpc_codes"])
        if not patent["curated"] and cpc_scope == "out_of_scope":
            excluded_scope += 1
            continue
        text = normalize_text(patent["text"])
        if not text or text in {"[en-only]", "[zh pending]"}:
            continue

        patent_components: set[str] = set()
        component_terms: list[str] = []
        for component_id, groups in components:
            component_group_count, terms = _matched_groups(text, groups)
            if component_group_count:
                patent_components.add(component_id)
                component_terms.extend(terms)

        for clause in clauses:
            shared_components = sorted(patent_components & clause["component_ids"])
            if not shared_components:
                continue
            group_count, clause_terms = _matched_groups(text, clause["groups"])
            if group_count == 0 and not patent["curated"]:
                continue
            strength = evidence_strength(group_count, len(shared_components), cpc_scope)
            if patent["curated"] and group_count >= 1 and strength == "WEAK":
                strength = "MEDIUM"
            if strength == "WEAK" and not (patent["curated"] or cpc_scope == "adjacent"):
                continue
            score = group_count * 35 + len(shared_components) * 20
            score += 20 if cpc_scope == "core" else 5 if cpc_scope == "adjacent" else 0
            score += 10 if patent["curated"] else 0
            matched_terms = list(dict.fromkeys(clause_terms + component_terms))[:20]
            excerpt = _excerpt(text, matched_terms)
            conn.execute(
                """INSERT INTO clause_mentions
                   (subject_type, subject_id, publication_number, clause_id,
                    matched_terms_json, matched_components_json, cpc_scope,
                    score, strength, evidence_excerpt, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    patent["subject_type"], patent["subject_id"], patent["publication_number"],
                    clause["id"], json.dumps(matched_terms, ensure_ascii=False),
                    json.dumps(shared_components, ensure_ascii=False), cpc_scope, score,
                    strength, excerpt, now,
                ),
            )
            mentions += 1
            credibility = source_credibility_tier(source_quality.get(patent["source_id"], ""))
            verification_status = "suggested"
            eligible = int(is_fact_eligible(credibility, strength, verification_status))
            basis = {
                "matched_terms": matched_terms,
                "matched_components": shared_components,
                "cpc_codes": patent["cpc_codes"],
                "cpc_scope": cpc_scope,
                "applicable_aircraft": patent.get("applicable_aircraft", []),
                "rule": "text_groups+component_anchor+cpc_scope",
            }
            match_id = "xmatch-" + hashlib.sha256(
                f"{patent['subject_type']}|{patent['subject_id']}|{clause['id']}".encode("utf-8")
            ).hexdigest()[:16]
            conn.execute(
                """INSERT INTO cross_match
                   (id, subject_type, subject_id, object_type, object_id, match_strength,
                    score, basis_json, source_credibility_tier, evidence_strength,
                    verification_status, eligible_for_fact, created_at)
                   VALUES (?, ?, ?, 'regulatory_clause', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    match_id, patent["subject_type"], patent["subject_id"], clause["id"],
                    strength, score, json.dumps(basis, ensure_ascii=False, sort_keys=True),
                    credibility, strength, verification_status, eligible, now,
                ),
            )
            matches += 1
            if strength == "STRONG":
                strong += 1
            elif strength == "MEDIUM":
                medium += 1
            else:
                weak += 1

    return BuildStats(len(candidates), excluded_scope, mentions, matches, strong, medium, weak)


def build_cross_matches(conn: sqlite3.Connection) -> BuildStats:
    create_schema(conn)
    conn.execute("SAVEPOINT build_cross_matches")
    try:
        stats = _build_cross_matches(conn)
        conn.execute("RELEASE SAVEPOINT build_cross_matches")
        return stats
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT build_cross_matches")
        conn.execute("RELEASE SAVEPOINT build_cross_matches")
        raise


def export_review_csv(conn: sqlite3.Connection, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = conn.execute(
        """SELECT x.id, m.publication_number, x.subject_type, x.subject_id,
                  x.object_id AS clause_id, x.match_strength, x.score,
                  x.verification_status, m.cpc_scope, m.matched_components_json,
                  m.matched_terms_json, m.evidence_excerpt
           FROM cross_match x
           JOIN clause_mentions m
             ON m.subject_type=x.subject_type AND m.subject_id=x.subject_id
            AND m.clause_id=x.object_id
           ORDER BY CASE x.match_strength WHEN 'STRONG' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
                    x.score DESC, x.subject_type, x.subject_id, x.object_id"""
    ).fetchall()
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8-sig", newline="", dir=output_path.parent, delete=False
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["match_id", "publication_number", "subject_type", "subject_id", "clause_id",
             "match_strength", "score", "verification_status", "cpc_scope",
             "matched_components", "matched_terms", "evidence_excerpt"]
        )
        writer.writerows(rows)
        temp_path = Path(handle.name)
    temp_path.replace(output_path)
    return len(rows)
