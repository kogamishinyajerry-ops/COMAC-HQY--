from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = ROOT / "ontology"
ONTOLOGY_FILES = (
    "aircraft_families.yaml",
    "throttle_components.yaml",
    "regulatory_clauses.yaml",
    "cpc_taxonomy.yaml",
)
_COMMON_FIELDS = {
    "id", "label_zh", "label_en", "aliases", "parent_id", "scope_level",
    "source_id", "disclaimer_zh", "disclaimer_en",
}


def _normalize_alias(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", value.casefold())


def load_document(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: root must be a mapping")
    required = {"schema_version", "ontology_type", "entities"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path.name}: missing {sorted(missing)}")
    if not isinstance(data["entities"], list) or not data["entities"]:
        raise ValueError(f"{path.name}: entities must be a non-empty list")
    return data


def load_bundle(directory: Path = ONTOLOGY_DIR) -> list[tuple[Path, dict[str, Any]]]:
    bundle = [(directory / name, load_document(directory / name)) for name in ONTOLOGY_FILES]
    ids: set[str] = set()
    for path, data in bundle:
        default_source = data.get("default_source_id", "")
        for entity in data["entities"]:
            entity_id = str(entity.get("id", "")).strip()
            if not entity_id:
                raise ValueError(f"{path.name}: entity without id")
            if entity_id in ids:
                raise ValueError(f"duplicate ontology id: {entity_id}")
            ids.add(entity_id)
            if not entity.get("label_zh") or not entity.get("label_en"):
                raise ValueError(f"{entity_id}: bilingual labels are required")
            if not entity.get("source_id", default_source):
                raise ValueError(f"{entity_id}: source_id is required")
    for path, data in bundle:
        for entity in data["entities"]:
            parent_id = entity.get("parent_id")
            if parent_id and parent_id not in ids:
                raise ValueError(f"{entity['id']}: unknown parent {parent_id}")
        for relation in data.get("relations", []):
            if relation.get("subject_id") not in ids or relation.get("object_id") not in ids:
                raise ValueError(f"{path.name}: relation references unknown entity")
    return bundle


def create_schema(conn: sqlite3.Connection) -> None:
    schema = (
        """
        CREATE TABLE IF NOT EXISTS ontology_registry (
            ontology_type TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            schema_version INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            loaded_at TEXT NOT NULL,
            entity_count INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ontology_entities (
            id TEXT PRIMARY KEY,
            ontology_type TEXT NOT NULL,
            parent_id TEXT REFERENCES ontology_entities(id),
            label_zh TEXT NOT NULL,
            label_en TEXT NOT NULL,
            scope_level TEXT NOT NULL DEFAULT '',
            source_id TEXT NOT NULL REFERENCES sources(id),
            attributes_json TEXT NOT NULL,
            disclaimer_zh TEXT NOT NULL,
            disclaimer_en TEXT NOT NULL,
            checked_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ontology_aliases (
            entity_id TEXT NOT NULL REFERENCES ontology_entities(id) ON DELETE CASCADE,
            language TEXT NOT NULL,
            alias TEXT NOT NULL,
            normalized_alias TEXT NOT NULL,
            PRIMARY KEY (entity_id, language, normalized_alias)
        );
        CREATE TABLE IF NOT EXISTS ontology_relations (
            subject_id TEXT NOT NULL REFERENCES ontology_entities(id) ON DELETE CASCADE,
            predicate TEXT NOT NULL,
            object_id TEXT NOT NULL REFERENCES ontology_entities(id) ON DELETE CASCADE,
            evidence_basis TEXT NOT NULL,
            PRIMARY KEY (subject_id, predicate, object_id)
        );
        CREATE INDEX IF NOT EXISTS idx_ontology_type ON ontology_entities(ontology_type);
        CREATE INDEX IF NOT EXISTS idx_ontology_parent ON ontology_entities(parent_id);
        CREATE INDEX IF NOT EXISTS idx_ontology_source ON ontology_entities(source_id);
        CREATE INDEX IF NOT EXISTS idx_ontology_alias ON ontology_aliases(normalized_alias);
        CREATE INDEX IF NOT EXISTS idx_ontology_relation_object ON ontology_relations(object_id, predicate);
        """
    )
    for statement in schema.split(";"):
        if statement.strip():
            conn.execute(statement)


def _install_ontology(conn: sqlite3.Connection, directory: Path = ONTOLOGY_DIR) -> dict[str, int]:
    bundle = load_bundle(directory)
    source_ids = {row[0] for row in conn.execute("SELECT id FROM sources")}
    all_entities: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for _, data in bundle:
        for entity in data["entities"]:
            source_id = entity.get("source_id", data.get("default_source_id", ""))
            if source_id not in source_ids:
                raise ValueError(f"{entity['id']}: source_id {source_id!r} is not registered")
            all_entities[entity["id"]] = (entity, data)

    conn.execute("DELETE FROM ontology_relations")
    conn.execute("DELETE FROM ontology_aliases")
    conn.execute("DELETE FROM ontology_entities")
    conn.execute("DELETE FROM ontology_registry")

    pending = dict(all_entities)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    while pending:
        progressed = False
        for entity_id, (entity, data) in list(pending.items()):
            parent_id = entity.get("parent_id") or None
            if parent_id and parent_id in pending:
                continue
            attributes = {k: v for k, v in entity.items() if k not in _COMMON_FIELDS}
            conn.execute(
                """INSERT INTO ontology_entities
                   (id, ontology_type, parent_id, label_zh, label_en, scope_level,
                    source_id, attributes_json, disclaimer_zh, disclaimer_en, checked_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entity_id, data["ontology_type"], parent_id,
                    entity["label_zh"], entity["label_en"], entity.get("scope_level", ""),
                    entity.get("source_id", data.get("default_source_id", "")),
                    json.dumps(attributes, ensure_ascii=False, sort_keys=True),
                    entity.get("disclaimer_zh", data.get("disclaimer_zh", "")),
                    entity.get("disclaimer_en", data.get("disclaimer_en", "")), now,
                ),
            )
            aliases = list(entity.get("aliases", [])) + [entity["label_zh"], entity["label_en"]]
            for alias in aliases:
                normalized = _normalize_alias(str(alias))
                if not normalized:
                    continue
                language = "zh" if re.search(r"[\u4e00-\u9fff]", str(alias)) else "en"
                conn.execute(
                    "INSERT OR IGNORE INTO ontology_aliases VALUES (?, ?, ?, ?)",
                    (entity_id, language, str(alias), normalized),
                )
            del pending[entity_id]
            progressed = True
        if not progressed:
            raise ValueError(f"cyclic ontology parents: {sorted(pending)}")

    for _, data in bundle:
        for entity in data["entities"]:
            if entity.get("parent_id"):
                conn.execute(
                    "INSERT OR IGNORE INTO ontology_relations VALUES (?, 'broader', ?, 'declared_parent')",
                    (entity["id"], entity["parent_id"]),
                )
        for relation in data.get("relations", []):
            conn.execute(
                "INSERT OR REPLACE INTO ontology_relations VALUES (?, ?, ?, ?)",
                (
                    relation["subject_id"], relation["predicate"], relation["object_id"],
                    relation.get("evidence_basis", "curated"),
                ),
            )

    counts: dict[str, int] = {}
    for path, data in bundle:
        count = len(data["entities"])
        counts[data["ontology_type"]] = count
        conn.execute(
            "INSERT INTO ontology_registry VALUES (?, ?, ?, ?, ?, ?)",
            (
                data["ontology_type"], path.name, int(data["schema_version"]),
                hashlib.sha256(path.read_bytes()).hexdigest(), now, count,
            ),
        )
    return counts


def install_ontology(conn: sqlite3.Connection, directory: Path = ONTOLOGY_DIR) -> dict[str, int]:
    create_schema(conn)
    conn.execute("SAVEPOINT install_ontology")
    try:
        counts = _install_ontology(conn, directory)
        conn.execute("RELEASE SAVEPOINT install_ontology")
        return counts
    except Exception:
        conn.execute("ROLLBACK TO SAVEPOINT install_ontology")
        conn.execute("RELEASE SAVEPOINT install_ontology")
        raise
