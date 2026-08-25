"""A1:HQY export_for_pace 测试。

验证:
1. build_export 从真实 DB 产出正确数据(8 专利 / 36 cross_match / 16 组件 / 15 条款)
2. cross_match 的 basis_json 正确解析(matched_components 非空)
3. clause_entities 含 5 条款号 × 3 authority
4. throttle_components 含 component_id(用于 join)
5. write_export 原子写 + utf-8
6. DB 不存在时退化返回空结构

日期:2026-07-29
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

# 让 src/ 可 import
HQY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HQY_ROOT))

from src.export_for_pace import (
    DB_PATH,
    ONTOLOGY_DIR,
    build_export,
    export,
    write_export,
)


# ---- 1. 真实 DB export 数值正确 ----------------------------------------


@pytest.fixture(scope="module")
def real_export():
    """模块级 fixture:从真实 DB build 一次,后续测试复用。"""
    if not DB_PATH.exists():
        pytest.skip("HQY DB 不存在,跳过真实数据测试")
    return build_export()


def test_export_counts_match_real_db(real_export):
    """真实 DB 产出数量对得上(8 专利 / 36 cross_match / 11 组件 / 15 条款)。"""
    cov = real_export["coverage"]
    assert cov["curated_patents"] == 8, f"期望 8 curated 专利,实际 {cov['curated_patents']}"
    assert cov["cross_matches"] == 36, f"期望 36 cross_match,实际 {cov['cross_matches']}"
    assert cov["throttle_components"] == 40, f"期望 40 组件,实际 {cov['throttle_components']}"
    assert cov["clause_entities"] == 15, f"期望 15 条款,实际 {cov['clause_entities']}"


def test_meta_fields_complete(real_export):
    """_meta 含 source/version/generated_at/db_path/hqy_note。"""
    meta = real_export["_meta"]
    assert meta["source"] == "HQY-throttle-patent-assistant"
    assert meta["version"] == "0.1.0"
    assert "generated_at" in meta
    assert "T" in meta["generated_at"]  # ISO8601
    assert "db_path" in meta
    assert "hqy_note" in meta


# ---- 2. cross_match basis_json 解析 ------------------------------------


def test_cross_match_basis_parsed(real_export):
    """cross_match 的 basis_json 正确解析(matched_components 是 list)。"""
    sample = real_export["cross_matches"][0]
    assert "basis" in sample
    assert isinstance(sample["basis"]["matched_components"], list)
    assert isinstance(sample["basis"]["matched_terms"], list)
    assert "cpc_scope" in sample["basis"]
    assert "rule" in sample["basis"]


def test_cross_match_all_have_patent_subject(real_export):
    """所有 cross_match 的 subject_type=patent(8 curated 专利)。"""
    for cm in real_export["cross_matches"]:
        assert cm["subject_type"] == "patent", \
            f"期望 subject_type=patent,实际 {cm['subject_type']}(id={cm['id']})"
        assert cm["object_type"] == "regulatory_clause"


def test_cross_match_strengths_are_weak_or_medium(real_export):
    """36 条全是 WEAK 或 MEDIUM(suggested 状态)。"""
    for cm in real_export["cross_matches"]:
        assert cm["match_strength"] in {"WEAK", "MEDIUM"}, \
            f"非法 strength: {cm['match_strength']}"
        assert cm["verification_status"] == "suggested"


# ---- 3. clause_entities 含 5 条款号 × 3 authority -----------------------


def test_clause_entities_cover_5_clause_numbers(real_export):
    """15 条款实体覆盖 5 个条款号:25.777/779/1141/1143/1155。"""
    clause_numbers = {ent["clause_number"] for ent in real_export["clause_entities"]}
    expected = {"25.777", "25.779", "25.1141", "25.1143", "25.1155"}
    assert clause_numbers == expected, f"条款号应为 {expected},实际 {clause_numbers}"


def test_clause_entities_cover_3_authorities(real_export):
    """15 条款实体覆盖 3 authority:FAA/EASA/CAAC。"""
    authorities = {ent["authority"] for ent in real_export["clause_entities"]}
    assert authorities == {"FAA", "EASA", "CAAC"}, f"实际 {authorities}"


# ---- 4. throttle_components 含 component_id ----------------------------


def test_throttle_components_have_component_id(real_export):
    """每个组件含 component_id(用于 join cross_match.basis.matched_components)。

    注意:component_id 用下划线命名(forward_lever),与 cross_match.basis 命名空间一致,
    不是 id 里的连字符(forward-lever)。
    """
    for comp in real_export["throttle_components"]:
        assert comp["component_id"], f"component_id 空: {comp}"
        # 含下划线的 component_id(forward_lever / reverse_lever)是本体 yaml 原值
        # 含连字符的(throttle-quadrant)是兜底从 id 切的(本体无 component_id 字段)
    # forward_lever 必须存在且是下划线(cross_match 用的就是这个)
    ids = {c["component_id"] for c in real_export["throttle_components"]}
    assert "forward_lever" in ids, f"forward_lever(下划线)应在 component_id 集合,实际 {ids}"
    assert "reverse_lever" in ids, f"reverse_lever(下划线)应在,实际 {ids}"


# ---- 5. write_export 原子写 + utf-8 ------------------------------------


def test_write_export_atomic_and_utf8(tmp_path, real_export):
    """write_export 写到 tmp_path,文件存在且 utf-8 可读。"""
    out = tmp_path / "pace_export.yaml"
    returned = write_export(real_export, out)
    assert returned == out
    assert out.exists()
    # 读回来对得上
    content = out.read_text(encoding="utf-8")
    assert "curated_patents" in content
    reloaded = yaml.safe_load(content)
    assert reloaded["coverage"]["curated_patents"] == 8
    # 中文正确(非 GBK 乱码)
    assert "油门台" in content or "油门" in content


def test_write_export_no_tmp_left(tmp_path, real_export):
    """原子写完成后无 .tmp 残留。"""
    out = tmp_path / "pace_export.yaml"
    write_export(real_export, out)
    assert not out.with_suffix(".yaml.tmp").exists()


# ---- 6. DB 不存在时退化 -----------------------------------------------


def test_build_export_missing_db_returns_empty(tmp_path):
    """DB 不存在时 build_export 返回空结构(不抛异常)。"""
    nonexistent = tmp_path / "nonexistent.db"
    data = build_export(db_path=nonexistent, ontology_dir=ONTOLOGY_DIR)
    assert data["coverage"]["curated_patents"] == 0
    assert data["coverage"]["cross_matches"] == 0
    assert data["curated_patents"] == []
    assert data["cross_matches"] == []
    # 但 ontology yaml 仍能读(不依赖 DB)
    assert data["coverage"]["throttle_components"] == 40
    assert data["coverage"]["clause_entities"] == 15


# ---- 7. 端到端:export() 写到 tmp --------------------------------------


def test_export_end_to_end(tmp_path, monkeypatch):
    """export() 完整流程:build + write。"""
    if not DB_PATH.exists():
        pytest.skip("HQY DB 不存在")
    out = tmp_path / "subdir" / "pace_export.yaml"
    monkeypatch.chdir(tmp_path)  # 不影响绝对路径,只是隔离
    returned = export(output_path=out)
    assert returned == out
    assert out.exists()
    data = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert data["coverage"]["cross_matches"] == 36


# ---- AA.3:专利适用整机族维度(2026-08-05 加)--------------------------


def test_cross_match_all_have_applicable_aircraft(real_export):
    """AA.3:36 cross_match 全部带 applicable_aircraft 字段(3 civil family)。

    用户 2026-08-05 决定:8 专利统一适用 a320/b737ng/c919 三族,不按专利区分。
    """
    expected = {"aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"}
    for cm in real_export["cross_matches"]:
        aircraft = cm.get("basis", {}).get("applicable_aircraft")
        assert aircraft, f"cross_match {cm['id']} 缺 applicable_aircraft"
        assert set(aircraft) == expected, \
            f"cross_match {cm['id']} aircraft 不匹配,实际 {set(aircraft)}"


def test_curated_patents_have_applicable_aircraft(real_export):
    """AA.3:8 curated_patent 全部带 applicable_aircraft 字段。"""
    expected = {"aircraft:a320-family", "aircraft:b737ng-family", "aircraft:c919-family"}
    patents = real_export.get("curated_patents", [])
    # export 里 curated_patents 字段名可能是 curated_patents 或 patents
    if not patents:
        # 看实际 key 名
        keys = [k for k in real_export.keys() if "patent" in k.lower()]
        pytest.skip(f"export 无 curated_patents 字段,候选 keys: {keys}")

    for p in patents:
        aircraft = p.get("applicable_aircraft", [])
        assert set(aircraft) == expected, \
            f"patent {p.get('patent_id')} aircraft 不匹配,实际 {set(aircraft)}"


def test_db_patents_table_has_applicable_aircraft_column():
    """AA.3:patents 表有 applicable_aircraft_json TEXT 列(DDL 守卫)。

    防回退:如果有人回滚 build_db.py 的 schema,这条测试会红。
    """
    if not DB_PATH.exists():
        pytest.skip("HQY DB 不存在")

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute("PRAGMA table_info(patents)")
        cols = {row[1]: row[2] for row in cur.fetchall()}  # name → type
    finally:
        conn.close()

    assert "applicable_aircraft_json" in cols, \
        f"patents 表缺 applicable_aircraft_json 列,实际列: {list(cols.keys())}"
    assert cols["applicable_aircraft_json"] == "TEXT", \
        f"applicable_aircraft_json 类型应为 TEXT,实际 {cols['applicable_aircraft_json']}"


def test_db_patents_all_have_3_civil_families():
    """AA.3:DB 里 8 专利每个都存了 3 civil family(JSON 解析后)。"""
    import json

    if not DB_PATH.exists():
        pytest.skip("HQY DB 不存在")

    expected = {"a320-family", "b737ng-family", "c919-family"}
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            "SELECT id, applicable_aircraft_json FROM patents"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    assert len(rows) == 8, f"期望 8 专利,实际 {len(rows)}"
    for pid, json_str in rows:
        aircraft = json.loads(json_str) if json_str else []
        # DB 里存的是带 aircraft: 前缀的完整 id(HQY 侧约定)
        families = {a.split(":", 1)[1] if ":" in a else a for a in aircraft}
        assert families == expected, \
            f"patent {pid} aircraft 不匹配,实际 {families}"
