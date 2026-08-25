from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

os.environ["AWKB_ENABLED"] = "0"

from build_db import initialize
from src.cross_match_builder import build_cross_matches
from src.governance.data_integrity import run_all_checks
from src.governance.evidence import is_fact_eligible
from src.governance.scope import classify_cpc, classify_patent_scope
from src.ontology_loader import ONTOLOGY_FILES, load_bundle


@pytest.fixture(scope="session")
def built_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("db") / "throttle.db"
    initialize(path)
    with sqlite3.connect(path) as conn:
        build_cross_matches(conn)
        conn.commit()
    return path


def test_four_ontology_files_load() -> None:
    bundle = load_bundle()
    assert [path.name for path, _ in bundle] == list(ONTOLOGY_FILES)


def test_ontology_ids_are_unique() -> None:
    ids = [entity["id"] for _, data in load_bundle() for entity in data["entities"]]
    assert len(ids) == len(set(ids))


def test_ontology_labels_are_bilingual() -> None:
    for _, data in load_bundle():
        for entity in data["entities"]:
            assert entity["label_zh"].strip()
            assert entity["label_en"].strip()


def test_ontology_references_resolve() -> None:
    bundle = load_bundle()
    ids = {entity["id"] for _, data in bundle for entity in data["entities"]}
    for _, data in bundle:
        for entity in data["entities"]:
            assert not entity.get("parent_id") or entity["parent_id"] in ids
        for relation in data.get("relations", []):
            assert relation["subject_id"] in ids
            assert relation["object_id"] in ids


def test_cpc_core_scope() -> None:
    assert classify_cpc("B64D 31/00") == "core"


def test_cpc_historical_noise_is_excluded() -> None:
    assert classify_cpc("B64D13/08") == "out_of_scope"


def test_cpc_adjacent_scope() -> None:
    assert classify_cpc("B60K26/00") == "adjacent"


def test_patent_scope_prefers_core() -> None:
    assert classify_patent_scope(["B64D13/00", "B64D31/10"]) == "core"


def test_suggested_match_is_never_fact() -> None:
    assert not is_fact_eligible("official", "STRONG", "suggested")


def test_crosschecked_strong_official_can_be_fact() -> None:
    assert is_fact_eligible("official", "STRONG", "official_crosschecked")


def test_clean_build_has_expected_ontology_counts(built_db: Path) -> None:
    with sqlite3.connect(built_db) as conn:
        rows = dict(conn.execute("SELECT ontology_type, entity_count FROM ontology_registry"))
        model_ids = {row[0] for row in conn.execute("SELECT id FROM models")}
        referenced_models = {
            model_id
            for (attributes,) in conn.execute(
                "SELECT attributes_json FROM ontology_entities WHERE ontology_type='aircraft_family'"
            )
            for model_id in json.loads(attributes).get("model_ids", [])
        }
    assert rows == {
        "aircraft_family": 9,
        "throttle_component": 40,
        "regulatory_clause": 15,
        "cpc_class": 31,
    }
    assert referenced_models == model_ids


def test_clean_build_has_sixty_three_sources(built_db: Path) -> None:
    with sqlite3.connect(built_db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0] == 63
        assert conn.execute(
            "SELECT COUNT(*) FROM sources WHERE license='' OR disclaimer_zh='' OR disclaimer_en=''"
        ).fetchone()[0] == 0


def test_clean_build_foreign_keys_pass(built_db: Path) -> None:
    with sqlite3.connect(built_db) as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_cross_match_is_review_only(built_db: Path) -> None:
    with sqlite3.connect(built_db) as conn:
        total = conn.execute("SELECT COUNT(*) FROM cross_match").fetchone()[0]
        auto_facts = conn.execute("SELECT COUNT(*) FROM cross_match WHERE eligible_for_fact=1").fetchone()[0]
        medium = conn.execute("SELECT COUNT(*) FROM cross_match WHERE match_strength='MEDIUM'").fetchone()[0]
        empty_evidence = conn.execute(
            "SELECT COUNT(*) FROM clause_mentions WHERE evidence_excerpt=''"
        ).fetchone()[0]
        statuses = {row[0] for row in conn.execute("SELECT DISTINCT verification_status FROM cross_match")}
    assert total > 0
    assert medium > 0
    assert empty_evidence == 0
    assert auto_facts == 0
    assert statuses == {"suggested"}


def test_eighteen_governance_checks_pass(built_db: Path) -> None:
    with sqlite3.connect(built_db) as conn:
        checks = run_all_checks(conn)
    assert len(checks) == 18
    assert all(check.passed for check in checks), [check for check in checks if not check.passed]


def test_existing_database_rebuild_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "existing.db"
    path.write_bytes(b"protected")
    with pytest.raises(RuntimeError, match="refusing to replace"):
        initialize(path)
    assert path.read_bytes() == b"protected"


def test_cascade_delete_clause_mentions(built_db: Path, tmp_path: Path) -> None:
    # 复制 session DB 到 tmp, 这样可以安全做 DELETE 不污染其他测试。
    # cross_match.object_id 没有 ON DELETE CASCADE, 所以必须先清掉引用, 才能删 ontology entity。
    # 然后验证 clause_mentions 因为 CASCADE 自动消失。
    import shutil

    copy_path = tmp_path / "cascade_test.db"
    shutil.copy2(built_db, copy_path)

    with sqlite3.connect(copy_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        row = conn.execute("SELECT clause_id FROM clause_mentions LIMIT 1").fetchone()
        assert row is not None, "session DB should have clause_mentions"
        target_id = row[0]

        before_mentions = conn.execute(
            "SELECT COUNT(*) FROM clause_mentions WHERE clause_id=?", (target_id,)
        ).fetchone()[0]
        assert before_mentions > 0

        # 必须先删 cross_match 行 (它们没有 CASCADE, FK 会挡住 ontology 删除)
        conn.execute("DELETE FROM cross_match WHERE object_id=?", (target_id,))
        # 触发 cascade
        conn.execute("DELETE FROM ontology_entities WHERE id=?", (target_id,))

        after_mentions = conn.execute(
            "SELECT COUNT(*) FROM clause_mentions WHERE clause_id=?", (target_id,)
        ).fetchone()[0]

    assert after_mentions == 0, (
        f"ON DELETE CASCADE failed: {after_mentions} clause_mentions rows still present"
    )


def test_migrate_protected_counts_preserved(tmp_path: Path) -> None:
    # migrate() 必须在 schema 变动后保持 prior_art_patents/chunks/prior_art_relevance/translated_prior_art
    # 行数零变化; 这是数据安全最后一道闸。
    db_path = tmp_path / "throttle.db"
    initialize(db_path)
    # 让 outputs 写到 tmp, 避免污染正式 outputs/governance/
    from scripts.migrate_ontology import migrate, snapshot_counts

    with sqlite3.connect(db_path) as conn:
        before = snapshot_counts(conn)

    result = migrate(db_path, backup=False)

    with sqlite3.connect(db_path) as conn:
        after = snapshot_counts(conn)

    assert before == after, f"protected counts drifted: {before} -> {after}"
    assert result["protected_counts"] == before


def test_migrate_protected_counts_asserts_on_drift(tmp_path: Path, monkeypatch) -> None:
    # 故意让 snapshot_counts 在 after 阶段虚报一个 +1, 验证 migrate 会 raise RuntimeError
    db_path = tmp_path / "throttle.db"
    initialize(db_path)
    from scripts import migrate_ontology

    real_snapshot = migrate_ontology.snapshot_counts
    call_state = {"count": 0}

    def drift_snapshot(conn):
        result = real_snapshot(conn)
        if call_state["count"] == 1:  # after 阶段
            result = dict(result)
            result["prior_art_patents"] = result.get("prior_art_patents", 0) + 1
        call_state["count"] += 1
        return result

    monkeypatch.setattr(migrate_ontology, "snapshot_counts", drift_snapshot)

    with pytest.raises(RuntimeError, match="protected data counts changed"):
        migrate_ontology.migrate(db_path, backup=False)
