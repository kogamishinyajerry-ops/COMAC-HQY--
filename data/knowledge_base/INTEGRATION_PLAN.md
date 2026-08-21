# 接入方案 · schema 草案 + 执行步骤（待严冬杰确认后实施）

> 决策已拍板：
> - 失败标 metadata_only，不阻塞接入
> - 只接入 3 张高价值表（triz_principles / patent_law_articles / ata_chapters）
> - 其余 JSON（FMEA / SKOS / KG schema / claim rules / accident schema / HF methods / CPC）暂作为研究参考保留在 `outputs/research_reference/`，不进 db

---

## 一、3 张新表 schema（按现有项目风格）

### 1. `triz_principles`（解法域方法论 · 40 条）

```sql
CREATE TABLE IF NOT EXISTS triz_principles (
    id INTEGER PRIMARY KEY,                              -- 1-40
    name_zh TEXT NOT NULL,
    name_en TEXT NOT NULL,
    description_zh TEXT NOT NULL,
    description_en TEXT NOT NULL,                        -- 守纪律 3：双语并行
    aviation_examples_json TEXT NOT NULL,                -- JSON 数组
    throttle_relevance INTEGER NOT NULL,                 -- 1-5
    relevance_reason_zh TEXT NOT NULL,
    relevance_reason_en TEXT NOT NULL,
    source_id TEXT NOT NULL REFERENCES sources(id),      -- 守纪律 1：引用键
    checked_at TEXT NOT NULL
);
```

**对应 source_id**：`triz-40-principles`（MATRIZ 官方）
**字段映射自**：`triz/triz_40_principles.json`
**字段重命名**：`throttle_app_relevance` → `throttle_relevance`；`alt_labels_*` 移除（不属于原理本身）

### 2. `patent_law_articles`（法律实体法 · 15 条）

```sql
CREATE TABLE IF NOT EXISTS patent_law_articles (
    id TEXT PRIMARY KEY,                                 -- 如 "CN-22-1" / "US-35USC-101"
    jurisdiction TEXT NOT NULL,                          -- "CN" / "US"
    article TEXT NOT NULL,                               -- "22" / "35 USC 101"
    title_zh TEXT NOT NULL,
    title_en TEXT NOT NULL,
    text_zh TEXT NOT NULL,
    text_en TEXT NOT NULL,
    patentability_dimension TEXT NOT NULL,               -- novelty/inventiveness/utility/...
    application_notes_zh TEXT NOT NULL,
    application_notes_en TEXT NOT NULL,                  -- 守纪律 3
    source_id TEXT NOT NULL REFERENCES sources(id),      -- 守纪律 1
    checked_at TEXT NOT NULL,
    -- 守纪律 5：边界声明
    disclaimer_zh TEXT NOT NULL DEFAULT '本字段为检索转述，正式法律意见须由专利代理师核对官方文本'
);
```

**对应 source_id**（按 jurisdiction 分流）：
- CN 条款 → `cnipa-patent-law-2020` 或 `cnipa-patent-examination-guidelines-2023`
- US 条款 → `uspto-35-usc-aia` 或 `uspto-mpep-9th`

### 3. `ata_chapters`（元分类骨架 · 87 条）

```sql
CREATE TABLE IF NOT EXISTS ata_chapters (
    ata_code TEXT PRIMARY KEY,                           -- "76" / "76-10" / "76-20"
    title_zh TEXT NOT NULL,
    title_en TEXT NOT NULL,
    parent_code TEXT,                                    -- 可空（顶层章节）
    relevance_to_throttle TEXT NOT NULL,                 -- high/medium/low/none
    notes_zh TEXT NOT NULL,
    notes_en TEXT NOT NULL,                              -- 守纪律 3
    source_id TEXT NOT NULL REFERENCES sources(id),      -- 守纪律 1
    checked_at TEXT NOT NULL,
    FOREIGN KEY (parent_code) REFERENCES ata_chapters(ata_code)
);
```

**对应 source_id**：`ata-ispec-2200`

---

## 二、sources 表新增条目（14 个）

按 `SOURCE_REGISTRY.md` 的清单，追加到 `build_db.py` 的 `SOURCES` 字面量列表。新增 `kind` 枚举值：
- `industry_standard`（SAE / ATA）
- `academic_reference`（MATRIZ / NASA-TLX / Cooper-Harper）
- `legal_statute`（CNIPA 专利法 / USPTO 35 USC / MPEP）
- `ontology_schema`（W3C / WIPO）

**这些 kind 在 sources 表是允许的**（schema 是 TEXT NOT NULL，无 CHECK 约束），但要在 `资料与许可.md` 补充分类说明。

---

## 三、metadata_only 处理

### 现有约定
`sync_sources.py` 当前只对 `source["kind"] == "licensed_media"` 自动标 metadata_only。

### 需要扩展
为新增来源增加字段 `archive_policy`：
- `"download"`（默认）：尝试下载
- `"metadata_only"`（如 SAE ARP4761 付费标准、ATA iSpec 2200 付费标准）：只登记 URL，不下载

**实施位置**：`build_db.py` 的 SOURCES 字面量 + `sync_sources.py` 的 fetch_one_source。

### 实施代码（待严冬杰确认后写）

```python
# sync_sources.py 改动
metadata_only = source.get("archive_policy") == "metadata_only" or source["kind"] == "licensed_media"
if metadata_only:
    # 跳过下载，只写 sources 表 + source_archive_runs
    ...
```

---

## 四、chunks 切片策略（守纪律 3）

每张新表的"描述性字段"（description / application_notes / notes）切片进 `chunks` 表：

- **triz_principles**：每条原理 1 个 chunk（40 chunks），title = "TRIZ 原理 N：中文名"
- **patent_law_articles**：每条法条 1 个 chunk（15 chunks），title = "CN/US §xxx 条款名"
- **ata_chapters**：每个章节 1 个 chunk（87 chunks），title = "ATA 章节号 中文名"

总计 142 个新 chunks，全部双语并行（body_zh / body_en），带 source_id。

---

## 五、执行步骤（顺序固定，每步可独立验证）

### Step 1 · 在 build_db.py 追加 SOURCES 字面量（14 个）
- 编辑 `build_db.py` 的 `SOURCES` 列表
- 追加 SOURCE_REGISTRY.md 中的 14 个来源
- 每个来源带 `archive_policy` 字段（download 或 metadata_only）

**验证**：跑 `python -c "from build_db import SOURCES; print(len(SOURCES))"`，应该比原来多 14

### Step 2 · 在 build_db.py 追加 3 张新表 schema
- 在 `initialize()` 函数里追加 `CREATE TABLE IF NOT EXISTS triz_principles / patent_law_articles / ata_chapters`
- 都带 `REFERENCES sources(id)` 外键

**验证**：删 db → 跑 `python build_db.py` → `sqlite3 data/throttle_knowledge.db ".schema triz_principles"` 应该有结果

### Step 3 · 在 build_db.py 追加 3 张表的数据字面量
- 把 9 个 JSON 中对应字段（按本文件 schema 草案的映射）转成 Python 字面量
- **每条带 source_id**（按 jurisdiction 等条件映射）
- 派生描述字段标 `derived: true`（如果有的话）

**验证**：跑 build_db 后查 `SELECT COUNT(*) FROM triz_principles` 应 = 40

### Step 4 · 修改 sync_sources.py 支持 archive_policy
- 加 metadata_only 跳过下载分支
- 跑 `python sync_sources.py` 走完整归档流程

**验证**：跑后查 `source_archive_runs` 表，新增 1 个 run，succeeded >= 可下载的，failed = 0（metadata_only 不算 failed）

### Step 5 · 把新表内容切片进 chunks 表
- 在 build_db.py 的 chunks 字面量里追加 142 条新切片
- 每条带 source_id（指向新登记的 source）
- 双语并行

**验证**：`SELECT COUNT(*) FROM chunks WHERE source_id LIKE 'triz-%' OR source_id LIKE 'cnipa-%' OR source_id LIKE 'ata-%'` 应 ≈ 142

### Step 6 · 资料与许可.md 补充新来源
- 在 § 核心技术来源、§ 适航法规、§ 专利对照文献 等章节追加
- 在文件末尾加 § 共同发明方法论与跨学科参考，说明 TRIZ / SAE / ATA / 法律 的来源与边界声明

### Step 7 · 清理孤儿 JSON
- 删除 `data/knowledge_base/triz/`、`legal/`、`ontology/`、`problem/` 目录下的 9 个 JSON
- 但保留 `SOURCE_REGISTRY.md` 和本文件作为接入记录
- 把"研究参考"类 JSON（FMEA / SKOS / KG / HF / CPC / claim_rules / accident_schema）移到 `outputs/research_reference/`，加 README 说明"暂未接入引用键体系，研究用途"

---

## 六、待严冬杰确认的问题

### Q1：archive_policy 怎么定？
按以下初步分配：

| source_id | archive_policy | 理由 |
|---|---|---|
| triz-40-principles | download | MATRIZ 页面公开 |
| wipo-cpc-scheme | download | WIPO 公开 |
| cnipa-patent-law-2020 | download | CNIPA 公开 |
| cnipa-patent-examination-guidelines-2023 | download | CNIPA 公开 |
| uspto-35-usc-aia | download | Cornell LII 公开 |
| uspto-mpep-9th | download | USPTO 公开 |
| us-supreme-court-patent-cases | download | Cornell LII 公开 |
| **sae-arp4761** | **metadata_only** | SAE 付费 |
| **sae-arp5580** | **metadata_only** | SAE 付费 |
| nasa-tlx | download | NASA ARC 公开 |
| cooper-harper-1969 | download | ERAU 公开 |
| faa-ac-25-1302 | download | FAA 公开 |
| ntsb-aviation-database | download | NTSB 公开 |
| nasa-asrs-database | download | NASA ASRS 公开 |
| uk-aaib-bulletins | download | GOV.UK 公开 |
| **ata-ispec-2200** | **metadata_only** | ATA 付费 |
| w3c-skos-reference | download | W3C 公开 |
| w3c-rdf-schema | download | W3C 公开 |
| w3c-owl2-overview | download | W3C 公开 |

**3 个 metadata_only**（SAE ×2 + ATA ×1）。

### Q2：第 7 步清理，研究参考类 JSON 放哪里？
建议路径：`outputs/research_reference/`，加 README.md 写"未接入引用键体系，仅作概念参考"。

---

## 七、不改的部分（守边界）

- `app.py` 不改（运行时只读）
- 现有 sources / chunks / regulatory_constraints 等表不动
- AirworthinessKB API 接入逻辑不动（守 SSOT）
- README / 交付安装说明 / 资料与许可 的现有条款不改，只追加

---

## 八、确认后的下一步

严冬杰看完本文件，确认 Q1 的 archive_policy 分配 + Q2 的研究参考路径后，我开始按 Step 1-7 顺序执行。
**每步独立验证，不一次性写完所有代码**。
