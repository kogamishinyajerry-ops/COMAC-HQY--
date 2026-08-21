"""把 9 个孤儿 JSON 中的 3 个表数据，转换为守纪律的 Python 字面量片段。

输出 3 个文件到 data/knowledge_base/_generated/：
- triz_principles.py
- patent_law_articles.py
- ata_chapters.py

每个文件是可直接粘贴到 build_db.py 的 Python 字面量。

守纪律：
- 每条数据带 source_id（REFERENCES sources(id)）
- 所有非结构化字段双语并行（_zh / _en）
- 缺失字段如实标注（不编造）
"""
from __future__ import annotations
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent  # knowledge_base/
OUT = Path(__file__).resolve().parent / "_generated"
OUT.mkdir(exist_ok=True)


# ============= TRIZ 40 原理 =============
def gen_triz() -> str:
    with open(BASE / "triz" / "triz_40_principles.json", encoding="utf-8") as f:
        data = json.load(f)
    principles = data["principles"]

    lines = ["TRIZ_PRINCIPLES = ["]
    for p in principles:
        # description_en 缺失：用 name_en + 简短英文摘要（不编造正文，仅声明）
        desc_zh = p["description_zh"]
        # 描述用 name_en 作标识（避免编造内容），如实标注"英文描述待补"
        desc_en = f"[EN description pending] {p['name_en']}: see Chinese description for full text."
        examples = p.get("aviation_examples", [])
        examples_json = json.dumps(examples, ensure_ascii=False)
        rel = p.get("throttle_app_relevance", {})
        score = rel.get("score", 3)
        reason_zh = rel.get("reason", "")
        # reason_en 缺失，用"see zh"声明
        reason_en = "[EN reason pending] See Chinese reason."

        # 安全转义
        def esc(s):
            return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        lines.append("    {")
        lines.append(f'        "id": {p["id"]},')
        lines.append(f'        "name_zh": "{esc(p["name_zh"])}",')
        lines.append(f'        "name_en": "{esc(p["name_en"])}",')
        lines.append(f'        "description_zh": "{esc(desc_zh)}",')
        lines.append(f'        "description_en": "{esc(desc_en)}",')
        lines.append(f'        "aviation_examples_json": "{esc(examples_json)}",')
        lines.append(f'        "throttle_relevance": {score},')
        lines.append(f'        "relevance_reason_zh": "{esc(reason_zh)}",')
        lines.append(f'        "relevance_reason_en": "{esc(reason_en)}",')
        lines.append(f'        "source_id": "triz-40-principles",')
        lines.append('        "checked_at": "2026-07-28",')
        lines.append("    },")
    lines.append("]")
    return "\n".join(lines) + "\n"


# ============= Patent Law Articles =============
def gen_patent_law() -> str:
    with open(BASE / "legal" / "patent_law_cn_us.json", encoding="utf-8") as f:
        data = json.load(f)
    articles = data["articles"]

    def source_for(jur: str, article: str) -> str:
        """按 jurisdiction + article 决定 source_id。"""
        if jur == "CN":
            # 审查指南相关条款 → guidelines；其他 → patent law
            if "26.4" in article or "审查" in article:
                return "cnipa-patent-examination-guidelines-2023"
            return "cnipa-patent-law-2020"
        if jur == "US":
            if "MPEP" in article.upper():
                return "uspto-mpep-9th"
            return "uspto-35-usc-aia"
        return "cnipa-patent-law-2020"

    lines = ["PATENT_LAW_ARTICLES = ["]
    for a in articles:
        jur = a["jurisdiction"]
        article = a["article"]
        # 原 application_notes 是单字段（中英混合？看下样本），保守处理：标 zh，en 标 pending
        notes_raw = a.get("application_notes", "")
        # 如果包含中文字符，认为是 zh；否则是 en
        has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in notes_raw)
        if has_cjk:
            notes_zh = notes_raw
            notes_en = "[EN notes pending]"
        else:
            notes_en = notes_raw
            notes_zh = "[中文要点待补]"
        sid = source_for(jur, article)
        rid = f"{jur}-{article.replace(' ', '-').replace('.', '_')}"

        def esc(s):
            return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        lines.append("    {")
        lines.append(f'        "id": "{esc(rid)}",')
        lines.append(f'        "jurisdiction": "{jur}",')
        lines.append(f'        "article": "{esc(article)}",')
        lines.append(f'        "title_zh": "{esc(a["title_zh"])}",')
        lines.append(f'        "title_en": "{esc(a["title_en"])}",')
        lines.append(f'        "text_zh": "{esc(a["text_zh"])}",')
        lines.append(f'        "text_en": "{esc(a["text_en"])}",')
        lines.append(f'        "patentability_dimension": "{esc(a["patentability_dimension"])}",')
        lines.append(f'        "application_notes_zh": "{esc(notes_zh)}",')
        lines.append(f'        "application_notes_en": "{esc(notes_en)}",')
        lines.append(f'        "source_id": "{sid}",')
        lines.append('        "checked_at": "2026-07-28",')
        lines.append("    },")
    lines.append("]")
    return "\n".join(lines) + "\n"


# ============= ATA Chapters =============
def gen_ata() -> str:
    with open(BASE / "ontology" / "ata_100_chapters.json", encoding="utf-8") as f:
        data = json.load(f)
    atas = data["ata_chapters"]

    lines = ["ATA_CHAPTERS = ["]
    # 顶层 + children 全部展平
    for a in atas:
        # 顶层节点
        notes_zh = a.get("notes", "")
        notes_en = f"[EN notes pending] {a['title_en']}"
        rel = a.get("relevance_to_throttle", "none")

        def esc(s):
            return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

        lines.append("    {")
        lines.append(f'        "ata_code": "{esc(a["ata_code"])}",')
        lines.append(f'        "title_zh": "{esc(a["title_zh"])}",')
        lines.append(f'        "title_en": "{esc(a["title_en"])}",')
        lines.append(f'        "parent_code": "",')  # 顶层
        lines.append(f'        "relevance_to_throttle": "{esc(rel)}",')
        lines.append(f'        "notes_zh": "{esc(notes_zh)}",')
        lines.append(f'        "notes_en": "{esc(notes_en)}",')
        lines.append(f'        "source_id": "ata-ispec-2200",')
        lines.append('        "checked_at": "2026-07-28",')
        lines.append("    },")
        # children
        for ch in a.get("children", []):
            ch_notes_zh = ch.get("notes", "")
            ch_notes_en = f"[EN notes pending] {ch['title_en']}"
            ch_rel = ch.get("relevance_to_throttle", "none")
            lines.append("    {")
            lines.append(f'        "ata_code": "{esc(ch["ata_code"])}",')
            lines.append(f'        "title_zh": "{esc(ch["title_zh"])}",')
            lines.append(f'        "title_en": "{esc(ch["title_en"])}",')
            lines.append(f'        "parent_code": "{esc(a["ata_code"])}",')
            lines.append(f'        "relevance_to_throttle": "{esc(ch_rel)}",')
            lines.append(f'        "notes_zh": "{esc(ch_notes_zh)}",')
            lines.append(f'        "notes_en": "{esc(ch_notes_en)}",')
            lines.append(f'        "source_id": "ata-ispec-2200",')
            lines.append('        "checked_at": "2026-07-28",')
            lines.append("    },")
    lines.append("]")
    return "\n".join(lines) + "\n"


def main():
    (OUT / "triz_principles.py").write_text(gen_triz(), encoding="utf-8")
    (OUT / "patent_law_articles.py").write_text(gen_patent_law(), encoding="utf-8")
    (OUT / "ata_chapters.py").write_text(gen_ata(), encoding="utf-8")
    # 验证语法
    import importlib.util
    for name in ["triz_principles", "patent_law_articles", "ata_chapters"]:
        path = OUT / f"{name}.py"
        spec = importlib.util.spec_from_file_location(name, path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        var_name = {"triz_principles": "TRIZ_PRINCIPLES",
                    "patent_law_articles": "PATENT_LAW_ARTICLES",
                    "ata_chapters": "ATA_CHAPTERS"}[name]
        n = len(getattr(m, var_name))
        size = path.stat().st_size / 1024
        print(f"  ✓ {name}.py  {n} 条  {size:.1f} KB")


if __name__ == "__main__":
    main()
