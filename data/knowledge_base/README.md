# 知识库目录索引 (knowledge_base/)

> 多 Agent 并行补全产物 · 2026-07-28
> 共 9 个 JSON 文件 + 4 个 README，312 KB，280+ 结构化数据点

## 目录结构

```
knowledge_base/
├── triz/           # 解法域 · TRIZ 方法论 + CPC 分类
│   ├── triz_40_principles.json       (40 条 Altshuller 发明原理)
│   ├── cpc_throttle_classification.json (62 条 CPC 分类号)
│   └── README.md
├── legal/          # 法律程序域 · 专利法 + 撰写规则
│   ├── patent_law_cn_us.json        (CN 专利法 + US 35 USC 15 条)
│   ├── claim_drafting_rules.json     (15 条权利要求撰写规则)
│   └── README.md
├── problem/        # 问题域深度 · FMEA + 人因 + 事故库
│   ├── fmea_aviation_throttle.json   (20 条按 ARP4761 分级失效)
│   ├── human_factors_methods.json    (12 种人因评估方法)
│   ├── accident_database_schema.json (NTSB/ASRS/AAIB schema + 检索模板)
│   └── README.md
└── ontology/       # 元知识层 · ATA + SKOS + KG
    ├── ata_100_chapters.json         (87 ATA 章节)
    ├── skos_throttle_concepts.json   (37 SKOS 概念)
    ├── knowledge_graph_schema.json   (15 节点 + 18 边 + 5 多跳示例)
    └── README.md
```

## 数据来源

| 域 | 一手来源 | 公开/开源 |
|---|---|---|
| TRIZ | Altshuller 经典 40 原理（Matrix-2010）+ 中国 TRIZ 协会中译 | 公开 |
| CPC | WIPO CPC 官方分类表 + Google Patents 检索 | 公开 |
| 法律 | 《专利法》2020 修正版 + 35 USC AIA + 审查指南 2023 + MPEP 第 9 版 | 公开 |
| FMEA | SAE ARP4761 / ARP5580 | 公开标准 |
| 人因 | NASA-TLX 原始论文 / Cooper-Harper / SHEL / EASA CS-25 AMC 25.1302 | 公开 |
| 事故库 | NTSB Aviation Database / ASRS / AAIB 公开通报 | 公开 |
| ATA | ATA-100 2023 版 | 公开 |
| SKOS | W3C SKOS Primer | 公开 |

## 维护约定

1. **追加不覆盖**：新增数据时 append，不重写既有条目
2. **数据溯源**：每条新增必须标 `source` 字段
3. **JSON 校验**：修改后必须通过 `python -m json.tool <file>` 校验
4. **领域边界**：法规域不在此目录（由 AirworthinessKB API 提供 SSOT）
5. **外部 connector**：先有技术全文库（patsnap-search）+ 全量法律法规（pkulaw）属于外部 connector，启用前不复制到本地
