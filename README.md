# COMAC-HQY-专利助手

> 商飞 COMAC HQY 油门台专利设计与证据工作台 — Agent 化交付版

一个可离线运行的中英双语航空油门台专利检索 + 跨源对齐 + 共同发明器 Web/CLI 双形态工具。
本仓是 `~/projects/COMAC_FDE_Team/Projects/HQY_油门台专利助手_throttle_app` 的 Agent 化轻量打包版,
仅含代码 + 本体 yaml + 小产物,数据库与原始抓取归档按需重建。

---

## 一键启动 (Web)

需要 Python 3.10+,装好依赖,然后:

```bash
pip install -r requirements.txt
python agent_cli.py serve           # 启 Web UI,默认 http://127.0.0.1:8765
```

首次运行会提示"知识库不存在",按下一节重建即可。

---

## 数据重建 (重要)

本仓**不**带 SQLite 数据库与原始抓取归档(共约 71M,见 `.gitignore`)。
clone 之后必须重建,选下面任一方式:

### 方式 A:从零建库 (慢,首次约 10-15 分钟,需要联网)

```bash
python agent_cli.py rebuild
# 跑完会得到 data/throttle_knowledge.db (≈17M)
```

`rebuild` 默认离线模式,使用内置 FALLBACK 条款(18 条 FAA/EASA/CAAC)。
如要拉取 AirworthinessKB 最新条款正文(可选,需先启动 AWKB 服务):

```bash
AWKB_ENABLED=1 python agent_cli.py rebuild
```

### 方式 B:从原 HQY 仓复制现成 db (快,推荐)

```bash
cp ~/projects/COMAC_FDE_Team/Projects/HQY_油门台专利助手_throttle_app/data/throttle_knowledge.db \
   data/throttle_knowledge.db
```

如果还要带原始抓取归档(54M+):

```bash
cp -R ~/projects/COMAC_FDE_Team/Projects/HQY_油门台专利助手_throttle_app/data/source_archive \
      data/source_archive
```

### 验证重建结果

```bash
python agent_cli.py stats     # 看表 + 计数
python agent_cli.py check     # 跑 17 项治理守卫
python agent_cli.py patrol    # 跑 4 路巡检,产物在 outputs/governance/
```

---

## CLI 速查

```bash
python agent_cli.py serve              # 启 Web UI
python agent_cli.py rebuild            # 重建 SQLite 知识库
python agent_cli.py query "thrust"     # 关键词查 patents / clauses
python agent_cli.py query "FAA" --target constraints
python agent_cli.py export             # 生成 outputs/pace_export.yaml (供 P-ACE 消费)
python agent_cli.py patrol             # 跑 4 路巡检
python agent_cli.py check              # 跑 17 项治理守卫
python agent_cli.py stats              # db 表 + 计数
python agent_cli.py curate             # 列 8 条 curated 专利 (供共同发明器)
python agent_cli.py ontology -v        # 加载本体 yaml + 打印前 3 条样本
```

所有子命令均支持 `--help`。

---

## 跟 P-ACE / AirworthinessKB / engine-kb-bridge 联动

本仓是 EngineKB / AWKB / bridge / HQY 四仓布局中的**油门台专利**主线,
与发动机公开情报 (P-ACE) / 适航条款 (AWKB) 通过 `engine-kb-bridge` 镜像耦合。

### 输出产物 `outputs/pace_export.yaml`

`agent_cli.py export` 会从 SQLite + ontology yaml 精选出:

- 8 条自建 curated 专利(patents 表)
- 36 条 cross_match(专利 ↔ 条款,半自动三轨证据制)
- 16 条 throttle_component 本体实体
- 15 条 regulatory_clause 本体实体(5 条款号 × 3 authority)

写到 `outputs/pace_export.yaml`,由 P-ACE 通过 env var `HQY_EXPORT_YAML` 读(镜像 `PACE_BRIDGE_YAML` 模式)。

### 不耦合 P-ACE / AWKB 数据

- 本仓不 import P-ACE / AWKB 代码
- 不连 P-ACE / AWKB SQLite
- 不自动重算 cross_match(需要时跑 `agent_cli.py patrol` 即可)

改数据后重算本体:

```bash
python agent_cli.py patrol
# 刷新 cross_match + 4 路巡检产物
```

---

## 项目结构

```
HQY-Agent/
├── agent_cli.py            # ⭐ Agent CLI 入口 (thin facade, 9 子命令)
├── app.py                  # Web UI HTTP 服务 (标准库 http.server)
├── build_db.py             # SQLite 知识库初始化
├── sync_sources.py         # 公开来源抓取脚本
├── ontology/               # 本体 yaml (4 文件: aircraft / throttle / clause / cpc)
├── src/
│   ├── cross_match_builder.py
│   ├── export_for_pace.py
│   ├── governance/         # 17 守卫 (evidence/scope/normalize/data_integrity)
│   └── ontology_loader.py
├── scripts/
│   ├── migrate_ontology.py
│   └── patrol_48h.py       # 4 路巡检
├── data/                   # ⛔ 不入仓,clone 后重建
│   ├── throttle_knowledge.db
│   └── source_archive/
├── outputs/                # 产物 (pace_export.yaml 入仓, csv/json 不入)
├── static/                 # Web UI 资源 (index.html / app.js / style.css)
├── tests/                  # pytest (35 测: 20 pass + 15 skip 需 db)
├── .gitignore
├── requirements.txt
└── README.md (本文件)
```

---

## 资料边界

法规模块当前仅覆盖运输类 / 大型飞机基线(FAA 14 CFR Part 25、EASA CS-25、CAAC CCAR-25-R4)。
具体型号的审定基础、修订版、专用条件和符合性方法可能不同。
三维模型是基于公开资料制作的参数化示意,不是原厂 CAD。
公开资料不足的功能被标记为"有限证据"或"未充分披露"。
本应用仅用于教育与研究,不用于实际飞行、维修、适航、认证或制造。

共同发明器生成的是可讨论、可试验的"发明假设"。
概念评估中的"差异机会"不是新颖性或创造性结论;
权利要求骨架也不是可直接提交的正式权利要求。
专利重合度来自所选组件技术标签与公开权利要求摘要的启发式匹配,
不是侵权、新颖性、创造性、自由实施或可专利性法律意见。
正式申请前须由专利代理师核对完整权利要求、同族、引证、官方法律状态和目标司法辖区。

本地归档仅用于个人研究、检索和证据回溯。
原网页、PDF 与影像页面仍受各来源网站的版权、许可条款和使用政策约束;
本地保存不改变其权利状态,也不代表可对外重新分发。

---

## 测试

```bash
python -m pytest tests/ -v
# 20 passed, 15 skipped (skipped 测需要 db,见方式 A/B 重建后全绿)
```

---

## 许可证与版权

见 `资料与许可.md`。本地归档仅供个人研究使用,不改变原始资料的版权状态。

## 上游

- 原项目:`~/projects/COMAC_FDE_Team/Projects/HQY_油门台专利助手_throttle_app/`
- 兄弟项目:
  - P-ACE (`~/Documents/AeroPlaneEngineSearch/public_engine_intel/`)
  - AirworthinessKB (`~/Documents/AirworthinessKB/`)
  - engine-kb-bridge (`~/Documents/engine-kb-bridge/`)
- 部署形态:轻量镜像,可单机离线运行,适合作为四仓耦合方案的"专利域"独立交付包
