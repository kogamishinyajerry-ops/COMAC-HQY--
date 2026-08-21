# 来源登记清单 · 知识库扩展接入

> 守纪律 1（来源登记）：每个新来源必须挂精确 URL + 进 sources 表。
> 守纪律 2（本地归档）：每个来源由 `sync_sources.py` 下载、SHA-256、切片。
>
> 本文件列出 9 个孤儿 JSON 对应的真实权威 URL，作为接入 sources 表的登记册。

## 枚举值约束（来自现有 sources 表）

- `kind` ∈ {official_regulation, official_certification_specification, official_manual, official_safety, official_investigation, accident_investigation, patent_document, manufacturer, manufacturer_safety, military_official, pilot_report_digest, licensed_media, **industry_standard**, **academic_reference**, **legal_statute**, **ontology_schema**}
- `quality` ∈ {government_primary, primary_document, primary, verified, high}
- `organization` 用现有可能的值或新增（如 SAE, W3C, WIPO, CNIPA, USPTO）

---

## 来源清单（按 source_id 排序）

### 1. triz/triz_40_principles.json

| 字段 | 值 |
|---|---|
| `id` | `triz-40-principles` |
| `kind` | `academic_reference` |
| `quality` | `primary` |
| `organization` | `MATRIZ` |
| `title_zh` | TRIZ 40 条发明原理（Altshuller 经典体系） |
| `title_en` | TRIZ 40 Inventive Principles (Altshuller canon) |
| `url` | https://matriz.org/training-tools/triz-40-principles/ |
| `note_zh` | Altshuller 40 原理由 MATRIZ（国际 TRIZ 协会）官方维护，是 TRIZ 方法的原始权威出处。Matrix-2010 公开版本为最新矛盾矩阵。 |
| `note_en` | The 40 principles maintained by MATRIZ as the canonical TRIZ reference. |
| `checked_at` | 2026-07-28 |

辅助参考（同主题）：
- https://www.triz-journal.com/40-principles/ （TRIZ Journal 公开镜像）

### 2. triz/cpc_throttle_classification.json

| 字段 | 值 |
|---|---|
| `id` | `wipo-cpc-scheme` |
| `kind` | `ontology_schema` |
| `quality` | `government_primary` |
| `organization` | `WIPO / EPO` |
| `title_zh` | CPC 合作专利分类表 |
| `title_en` | Cooperative Patent Classification Scheme |
| `url` | https://www.cooperativepatentclassification.org/index |
| `note_zh` | CPC 由 WIPO 与 EPO 联合维护，提供完整分类表下载。本表只取与油门台相关的 B64D 31/00、B64D 33/00、G05D 1/00、B64C 19/00、H01H 子组。 |
| `note_en` | Official CPC scheme maintained jointly by WIPO and EPO. |
| `checked_at` | 2026-07-28 |

辅助参考：
- https://patents.google.com/ （Google Patents 提供分类号检索，便于核验）

### 3. legal/patent_law_cn_us.json

**3a. CN 专利法**
| 字段 | 值 |
|---|---|
| `id` | `cnipa-patent-law-2020` |
| `kind` | `legal_statute` |
| `quality` | `government_primary` |
| `organization` | `CNIPA` |
| `title_zh` | 中华人民共和国专利法（2020 年第四次修正） |
| `title_en` | Patent Law of the People's Republic of China (4th amendment, 2020) |
| `url` | https://www.cnipa.gov.cn/col/col86/index.html |
| `note_zh` | 国家知识产权局官方发布的 2020 年第四次修正版专利法，自 2021 年 6 月 1 日起施行。 |
| `checked_at` | 2026-07-28 |

辅助参考：
- https://www.gov.cn/guoqing/2021-10/29/content_5647633.htm （国务院官网普法版）

**3b. CN 审查指南**
| 字段 | 值 |
|---|---|
| `id` | `cnipa-patent-examination-guidelines-2023` |
| `kind` | `legal_statute` |
| `quality` | `government_primary` |
| `organization` | `CNIPA` |
| `title_zh` | 专利审查指南（2023 年修订） |
| `title_en` | Patent Examination Guidelines (2023 revision) |
| `url` | https://www.cnipa.gov.cn/col/col489/index.html |
| `note_zh` | 国家知识产权局 2023 年 12 月 21 日发布、2024 年 1 月 20 日生效。 |
| `checked_at` | 2026-07-28 |

**3c. US 35 USC**
| 字段 | 值 |
|---|---|
| `id` | `uspto-35-usc-aia` |
| `kind` | `legal_statute` |
| `quality` | `government_primary` |
| `organization` | `USPTO / Cornell LII` |
| `title_zh` | 美国法典第 35 卷（专利法）AIA 版本 |
| `title_en` | 35 U.S.C. (Patents), Leahy-Smith America Invents Act version |
| `url` | https://www.law.cornell.edu/uscode/text/35 |
| `note_zh` | 35 USC 由 Cornell LII 维护公开版本，AIA 2011 后版本为现行。 |
| `checked_at` | 2026-07-28 |

**3d. US MPEP**
| 字段 | 值 |
|---|---|
| `id` | `uspto-mpep-9th` |
| `kind` | `legal_statute` |
| `quality` | `government_primary` |
| `organization` | `USPTO` |
| `title_zh` | 美国专利审查程序手册（MPEP 第 9 版，2024 年修订） |
| `title_en` | Manual of Patent Examining Procedure (MPEP, 9th ed., 2024 rev.) |
| `url` | https://www.uspto.gov/web/offices/pac/mpep/index.html |
| `checked_at` | 2026-07-28 |

### 4. legal/claim_drafting_rules.json

来源同 3b + 3d（CN 审查指南 + US MPEP），无需新增独立 source。
但涉及 Alice/Mayo / KSR / Nautilus / Williamson / Ariad / Amgen 判例：

| 字段 | 值 |
|---|---|
| `id` | `us-supreme-court-patent-cases` |
| `kind` | `legal_statute` |
| `quality` | `government_primary` |
| `organization` | `U.S. Supreme Court / Cornell LII` |
| `title_zh` | 美国专利相关判例集（Alice, Mayo, KSR, Nautilus, Williamson, Ariad, Amgen v. Sanofi） |
| `title_en` | U.S. patent-related case law collection |
| `url` | https://www.law.cornell.edu/supct/html/13-298.html |
| `note_zh` | Alice Corp. v. CLS Bank（573 U.S. 208, 2014）作为客体资格两步法的代表性判例。 |
| `checked_at` | 2026-07-28 |

### 5. problem/fmea_aviation_throttle.json

**5a. SAE ARP4761**
| 字段 | 值 |
|---|---|
| `id` | `sae-arp4761` |
| `kind` | `industry_standard` |
| `quality` | `primary` |
| `organization` | `SAE International` |
| `title_zh` | SAE ARP4761 民用机载系统与设备安全性评估过程的指南 |
| `title_en` | SAE ARP4761 Guidelines for Methods of Safety Assessment Process |
| `url` | https://www.sae.org/standards/content/arp4761/ |
| `note_zh` | ARP4761 定义了 Catastrophic / Hazardous / Major / Minor / No-Safety-Effect 五级失效分类。 |
| `checked_at` | 2026-07-28 |

**5b. SAE ARP5580**
| 字段 | 值 |
|---|---|
| `id` | `sae-arp5580` |
| `kind` | `industry_standard` |
| `quality` | `primary` |
| `organization` | `SAE International` |
| `title_zh` | SAE ARP5580 故障模式影响分析（FMEA） |
| `title_en` | SAE ARP5580 Recommended Failure Modes and Effects Analysis |
| `url` | https://www.sae.org/standards/content/arp5580/ |
| `checked_at` | 2026-07-28 |

### 6. problem/human_factors_methods.json

**6a. NASA-TLX**
| 字段 | 值 |
|---|---|
| `id` | `nasa-tlx` |
| `kind` | `academic_reference` |
| `quality` | `primary` |
| `organization` | `NASA ARC` |
| `title_zh` | NASA 任务负荷指数（NASA-TLX） |
| `title_en` | NASA Task Load Index |
| `url` | https://humansystems.arc.nasa.gov/groups/TLX/ |
| `note_zh` | Hart & Staveland 1988 原始论文由 NASA ARC 官方页面提供。 |
| `checked_at` | 2026-07-28 |

**6b. Cooper-Harper**
| 字段 | 值 |
|---|---|
| `id` | `cooper-harper-1969` |
| `kind` | `academic_reference` |
| `quality` | `primary` |
| `organization` | `NASA / Cornell e-Commons` |
| `title_zh` | Cooper-Harper 飞行品质评级（1969 原始论文） |
| `title_en` | Cooper-Harper Handling Qualities Rating |
| `url` | https://commons.erau.edu/space-congress-proceedings/proceedings-1969-6th-v1/6th-V1-7/ |
| `note_zh` | Cooper & Harper 1969 原始论文。 |
| `checked_at` | 2026-07-28 |

**6c. FAA AC 25.1302**
| 字段 | 值 |
|---|---|
| `id` | `faa-ac-25-1302` |
| `kind` | `official_regulation` |
| `quality` | `government_primary` |
| `organization` | `FAA` |
| `title_zh` | FAA AC 25.1302 驾驶舱系统人为因素 |
| `title_en` | FAA AC 25.1302 Human Factors for Cockpit Systems |
| `url` | https://www.faa.gov/regulations_policies/advisory_circulars/index.cfm/go/document.information/documentID/1041470 |
| `checked_at` | 2026-07-28 |

### 7. problem/accident_database_schema.json

**7a. NTSB**
| 字段 | 值 |
|---|---|
| `id` | `ntsb-aviation-database` |
| `kind` | `accident_investigation` |
| `quality` | `government_primary` |
| `organization` | `NTSB` |
| `title_zh` | NTSB 航空事故数据库 |
| `title_en` | NTSB Aviation Accident Database & Synopses |
| `url` | https://data.ntsb.gov/avdata/ |
| `note_zh` | NTSB 公开 API，可下载全量航空事故数据。 |
| `checked_at` | 2026-07-28 |

**7b. NASA ASRS**
| 字段 | 值 |
|---|---|
| `id` | `nasa-asrs-database` |
| `kind` | `pilot_report_digest` |
| `quality` | `government_primary` |
| `organization` | `NASA ASRS` |
| `title_zh` | NASA 航空安全报告系统数据库 |
| `title_en` | NASA Aviation Safety Reporting System Database |
| `url` | https://asrs.arc.nasa.gov/search/database.html |
| `checked_at` | 2026-07-28 |

**7c. UK AAIB**
| 字段 | 值 |
|---|---|
| `id` | `uk-aaib-bulletins` |
| `kind` | `accident_investigation` |
| `quality` | `government_primary` |
| `organization` | `UK AAIB` |
| `title_zh` | UK AAIB 调查通报库 |
| `title_en` | UK Air Accidents Investigation Branch bulletins |
| `url` | https://www.gov.uk/aaib-reports |
| `checked_at` | 2026-07-28 |

### 8. ontology/ata_100_chapters.json

| 字段 | 值 |
|---|---|
| `id` | `ata-ispec-2200` |
| `kind` | `industry_standard` |
| `quality` | `primary` |
| `organization` | `ATA` |
| `title_zh` | ATA iSpec 2200 / ATA-100 章节分类 |
| `title_en` | ATA iSpec 2200 / ATA-100 Chapter Classification |
| `url` | https://www.ata.org/ |
| `note_zh` | ATA-100 章节分类是航空业事实标准，部分公开章节索引可在线获取。 |
| `checked_at` | 2026-07-28 |

辅助参考：
- https://www.s1000d.org/ （S1000D Issue 5.0+ 保留 ATA 章节映射）

### 9. ontology/skos_throttle_concepts.json

| 字段 | 值 |
|---|---|
| `id` | `w3c-skos-reference` |
| `kind` | `ontology_schema` |
| `quality` | `primary` |
| `organization` | `W3C` |
| `title_zh` | W3C SKOS 简易知识组织系统参考 |
| `title_en` | W3C SKOS Simple Knowledge Organization System Reference |
| `url` | https://www.w3.org/TR/skos-reference/ |
| `checked_at` | 2026-07-28 |

辅助参考：
- https://www.w3.org/TR/skos-primer/ （SKOS 入门指南）

### 10. ontology/knowledge_graph_schema.json

来源同 9（W3C SKOS）+ 增补：

| 字段 | 值 |
|---|---|
| `id` | `w3c-rdf-schema` |
| `kind` | `ontology_schema` |
| `quality` | `primary` |
| `organization` | `W3C` |
| `title_zh` | W3C RDF Schema 1.1 |
| `title_en` | W3C RDF Schema 1.1 |
| `url` | https://www.w3.org/TR/rdf-schema/ |
| `checked_at` | 2026-07-28 |

| 字段 | 值 |
|---|---|
| `id` | `w3c-owl2-overview` |
| `kind` | `ontology_schema` |
| `quality` | `primary` |
| `organization` | `W3C` |
| `title_zh` | W3C OWL 2 概览 |
| `title_en` | W3C OWL 2 Web Ontology Language Document Overview (Second Edition) |
| `url` | https://www.w3.org/TR/owl2-overview/ |
| `checked_at` | 2026-07-28 |

---

## 接入流程（执行顺序）

1. **本文档登记完成**（已 ✓）
2. 在 `build_db.py` 的 `SOURCES` 字面量列表追加上述 14 个新来源
3. 用 `sync_sources.py` 走完整归档流程（下载 → SHA-256 → 切片）
4. 在 `build_db.py` 新建业务表（如 `triz_principles` / `patent_law_articles` / `ata_chapters`），每张表必须 `REFERENCES sources(id)`
5. 把 9 个 JSON 的内容**逐条带 `source_id`** 重新写入业务表（不再保留 JSON 文件）
6. 守纪律 3（双语并行）：所有非结构化字段必须有 `_zh` 和 `_en`
7. 删除 `data/knowledge_base/` 目录下的 9 个 JSON

## 边界声明（守纪律 5）

每张新业务表的 README 必须写明：
- 这不是法律意见 / 不是新颖性结论
- 涉及法规原文的，必须通过 AirworthinessKB API 取（不本地复制条文）
- TRIZ / SAE / ATA 等组织标准的派生描述属于检索转述，不替代标准全文
