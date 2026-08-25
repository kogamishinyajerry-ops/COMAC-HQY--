# Phase A Runbook · EPO OPS / USPTO / Google Patents / BQ Public 抓取故障排查

> Phase A prior_art 检索池扩展的运行手册。
> 代码:A0 (commit 16bf329) / A1 (1e8ceac) / A2 (531ec55) / **E (Phase E: bq-public-patents + google-patents-xhr, 2026-08-25)** 已就绪。
> 真数据抓取受 Keychain 凭据 + 公开 API 可达性约束。

---

## 1. 五源可达性当前评估 (2026-08-25 验证)

| 源 | 真实 endpoint | key 要求 | 可达性 |
|---|---|---|---|
| **uspto-od** (PatentsView) | `https://search.patentsview.org/api/v1/patent/` | **需要 X-Api-Key**,但 PatentsView **已暂停新 key 申请** | ❌ 不可达 |
| **uspto-od** (旧) | `https://api.patentsview.org/patents/query` | 无 | ❌ 返回 Angular SPA HTML,不再接受 POST+JSON |
| **epo-ops** (Open Patent Services) | `https://ops.epo.org/3.2/rest-services/` | OAuth2 client_credentials (免费注册) | ✅ 可达(凭据就绪后) |
| **google-patents-playwright** | `https://patents.google.com/` | 无 | ⚠️ captcha 频发,timeout 修了但仍受限 |
| **google-patents-xhr** (Phase E) | `https://patents.google.com/xhr/query` + `xhr/result` | 无 | ⚠️ IP 频次限流触发 "Sorry..." 503 |
| **bq-public-patents** (Phase E) | `patents-public-data.patents.publications` (BQ REST API) | gcloud auth 即可 | ⚠️ gen-lang-client-* sub-quota 烧光时真查询返 403, dryRun 走通 |
| **google-patents-playwright** | `https://patents.google.com/` | 无 | ⚠️ captcha 频发,Phase A 接受低命中率 |

**结论**:
- Phase A 当前**实际可跑源 = EPO OPS only**(凭据就绪后)
- **2026-08-25 全部 5 源被堵的真实状态**(实测):
  - uspto-od → ❌ PatentsView 新 API 需要 X-Api-Key (grant suspended) + 旧 endpoint 返回 HTML SPA
  - epo-ops → ❌ 无 Keychain 凭据 (`security add-generic-password -s epo-ops ...` 未跑)
  - google-patents-playwright → ❌ Playwright 30ms timeout bug 已修,但 captcha 仍频发
  - google-patents-xhr → ❌ Google "Sorry..." 503 (IP 限流,过几小时可能恢复)
  - bq-public-patents → ❌ gen-lang-client-0334150098 项目 sub-quota "Quota exceeded: free query bytes scanned" (1 TB/月免费但 per-query/daily 子 quota 已烧光)
  - **dryRun (零字节) 走通**:`bq query --dry_run` 测得 F02C9 反推 CPC LIKE 查询扫 17 GB / query,free tier 1 TB/月约能跑 60 query。`bq query` CLI 在 macOS LibreSSL+OpenSSL 3.5.5 共存环境会触发 `SSLEOFError(8, 'SSL: UNEXPECTED_EOF_WHILE_READING')`(已实测),**REST API 直接 curl + gcloud token 绕开此 bug**(详见 §4)
- **Phase E 兜底**:`scripts/import_prior_art_phase_e.py` 单值 BQ lookup (cache hit 不烧 quota) 可继续灌,前提是你手动提供 publication_number 清单
- 真爬虫恢复路径:
  1. **EPO 最现实**:去 https://developers.epo.org/ 注册 (1 工作日) + 存 Keychain (`security add-generic-password -s epo-ops -a EPO_CONSUMER_KEY -w '<key>'` ... + 同样 SECRET) → adapter 即跑通
  2. **BQ 等月重置**:gen-lang-client-* sub-quota 月底/月初 reset → BQ adapter 自动恢复
  3. **换 GCP 项目**:新建项目 (注册赠送 $300/90 天免费) → `gcloud config set project <new>` → BQ 不再受限
- USPTO 路径保留代码占位(`uspto-od` adapter 已写,无 key 跳过)
- Google 路径保留代码占位,接受 captcha

---

## 1.5 BigQuery REST API 路径 (2026-08-25 修复,Phase E 增量)

**问题**:`bq query` CLI 在 macOS LibreSSL + OpenSSL 3.5.5 共存环境触发
`SSLEOFError(8, 'SSL: UNEXPECTED_EOF_WHILE_READING')` — 真查询 + 大 body POST 必然失败。
dryRun 走通是因为它只返 schema/bytes 估算,body 小。

**修复**:`src/prior_art_adapters/bq_public.py` 改用 `requests.post` 直连
`https://bigquery.googleapis.com/bigquery/v2/projects/<project>/queries`,
用 `gcloud auth print-access-token` 取 token,带 `Accept-Encoding: gzip`。

**已验证**(2026-08-25 手动 curl 跑通):
- dryRun F02C9 反推 → 17 GB / query
- dryRun F02D11 汽车油门 → 17 GB / query
- 真查询受 sub-quota 卡死 → 返 `Quota exceeded: free query bytes scanned`

**新增测试**(`tests/test_prior_art_adapters.py`):
- `test_bq_adapter_rest_parses_schema_and_rows` — REST 响应 schema+rows 解析
- `test_bq_adapter_rest_returns_none_on_quota_error` — 配额超限优雅返 None
- `test_bq_adapter_rest_returns_none_on_no_token` — 无 token 不发请求
- `test_bq_adapter_rest_returns_empty_list_on_no_rows` — 空结果集返 []
- `test_bq_adapter_search_yields_records_from_rest` — 端到端 search() yield record

**实际可跑场景**(恢复路径任选其一):
1. 月初 / 月底 quota 重置 → BQ adapter 自动恢复(无需改代码)
2. 换 GCP project:`gcloud config set project <new>`(新注册项目前 90 天有 $300 credit)
3. 已知 publication_number 手动清单 → 走 `scripts/import_prior_art_phase_e.py`(单值 lookup,cache hit 不烧 quota)

---

## 2. EPO OPS 凭据准备 (Phase A 跑通的唯一前置条件)

### 2.1 申请 developer account

去 https://developers.epo.org/ 注册免费账号:
- Consumer Key (32 字符)
- Consumer Secret (32 字符)
- 注册后等 24h 内邮件确认(工作日)

### 2.2 macOS Keychain 存储

```bash
# 在终端执行(替换 <value> 为真实凭据)
security add-generic-password -s epo-ops -a EPO_CONSUMER_KEY -w '<consumer_key>'
security add-generic-password -s epo-ops -a EPO_CONSUMER_SECRET -w '<consumer_secret>'

# 验证存储成功
security find-generic-password -s epo-ops -a EPO_CONSUMER_KEY -w
security find-generic-password -s epo-ops -a EPO_CONSUMER_SECRET -w
```

**注意**:密码按 macOS keychain service `epo-ops` + account `EPO_CONSUMER_KEY`/`SECRET` 索引。
adapter 代码见 `src/prior_art_adapters/epo_ops.py:_keychain_get()`。

---

## 3. 三步跑 Phase A

### 3.1 健康检查

```bash
cd ~/projects/HQY-Agent
unset GH_TOKEN GITHUB_TOKEN
python scripts/import_prior_art_phase_a.py --dry-run --source epo-ops \
  --keyword "FADEC" --cpc F02C9/00
```

**期望输出**:
```
INFO phase_a health_check epo-ops: OK
INFO phase_a === phase A summary ===
INFO phase_a source=epo-ops keywords=('FADEC',) cpcs=('F02C9/00',) dry_run=True
INFO phase_a inserted=0 skipped_existing=0 bridge_rows=0 orphans=0
```

`inserted=0` 是 dry-run 时不会真插,但 health_check OK 表明 OAuth 通 + API 可达。
**如果 health_check FAIL**:见 §4 故障排查。

### 3.2 实际入库(写库 + 桥表)

```bash
python scripts/import_prior_art_phase_a.py \
  --source epo-ops \
  --keyword "reverse thrust" \
  --keyword "FADEC" \
  --keyword "EEC" \
  --cpc B64D31/00 \
  --cpc F02C9/00 \
  --cpc F02C9/28 \
  --cpc F02C9/46 \
  --limit-per-query 500 \
  --filing-from 2000-01-01
```

**预期**:12 query × 500 上限 = 最多 6000 候选,去重后入库 3000-5000 件 + 同号桥表行。

跑完会**自动**调 `require_all_pass()`,确认 18 守卫全过:
```
INFO phase_a governance: 18/18 PASS
```

### 3.3 老库桥表反向迁移(已有 google-patents-bigquery 数据)

```bash
python scripts/migrate_dedup_bridge.py
```

会自动备份 `throttle_knowledge.db.bak.bridge-<timestamp>` + 回填桥表 + 跑 18 守卫。

---

## 4. 故障排查

### 4.1 EPO health_check FAIL:Keychain not found

```
WARNING src.prior_art_adapters.epo_ops EPO health check failed:
  Keychain epo-ops/EPO_CONSUMER_KEY not found.
  Add with: security add-generic-password -s epo-ops -a EPO_CONSUMER_KEY -w '<value>'
```

**修复**:见 §2.2,确认 keychain 存了两个 entry 且 service/account 名完全匹配。

### 4.2 EPO health_check FAIL:401 Unauthorized

OAuth token 过期,adapter 会自动 refresh(`_ensure_token` 重置 `_access_token`)。
持续 401 表明 Keychain 凭据错误或被 EPO revoke,重新申请。

### 4.3 EPO 429 Too Many Requests

adapter 内部已 sleep 30s 后 retry。
EPO OPS 限速 50 req/min,Phase A rate_limit_sec=1.5s(40/min)。
若频繁 429:把 `--limit-per-query` 降到 100,减少并发请求。

### 4.4 Google Patents captcha

```
WARNING src.prior_art_adapters.google_patents_playwright Google captcha triggered,
  skip rest of this query
```

Phase A 接受(plan R1)。captcha 后 adapter 跳完当前 query,继续下一 keyword × CPC。
若持续被 captcha:暂停 5-10 分钟后重跑,或换 cookie / proxy(需要时另开 Phase)。

### 4.5 USPTO SSL EOF 或 HTML 响应

```
urllib3.exceptions.SSLError: [SSL: UNEXPECTED_EOF_WHILE_READING]
```

PatentsView API 现在要求 X-Api-Key,无 key 被阻断。
**Phase A 当前不跑 USPTO**(见 §1)。如未来 PatentsView 重启 API key 申请,把 `X-Api-Key: <key>` 加进
`src/prior_art_adapters/uspto_opendata.py:health_check()` 和 `_search_one()` 的 headers。

### 4.6 governance 18/18 FAIL

`require_all_pass()` 抛 RuntimeError 详情 `;`-separated:

- `prior_art_dedup_bridge_consistency=N`:桥表有孤儿 source_id 不在 sources 表。
  跑 `python scripts/migrate_dedup_bridge.py` 重新对齐。
- `prior_art_traceability=N`:prior_art_patents 有 source_id 不在 sources 表。
  老 google-patents-bq 行不会触发,但新 import 的源 source_id 必须先登记。
- `prior_art_cpc_json=N`:prior_art_patents.cpc_codes 不是 JSON valid。
  adapter 输出会保证,如果是手工 INSERT 触发,需手动 fix。

---

## 5. 集成测试

`pytest tests/test_import_phase_a.py` 9 测覆盖 dry-run / dedup / orphan / tmp_path 隔离。
无真网络依赖,任何环境都能跑:

```bash
python -m pytest tests/test_import_phase_a.py -v
```

---

## 6. 不破坏既有边界 (Phase A 边界声明)

- **不动** `patents` (8 条 curated) / `invention_patterns` (8 个发明模式)
- **不动** `app.py` Web UI / `export_for_pace.py` 老路径
- **不动** `migrate_ontology.py` (protected_counts 校核,Phase A 走新桥表不进 protected 范围)
- **不动** `import_prior_art.py` 老 google-patents-bigquery 单源流程(保留,Phase A 是新链路)
- **同本体层只动** `scope.py` CORE_PREFIXES + `cpc_taxonomy.yaml` 4 实体;governance 加 1 个新守卫 + 1 个 floor 数值

---

## 7. Phase B/C 路径

- **Phase B** (汽车油门):CPC=B60K26/00 + B60K31/00 + G05G1/00,关键词 throttle / accelerator / drive-by-wire / ETC
- **Phase C** (船舶油门):CPC=B63H21/00 + B63H21/21 + G05G1/00,关键词 marine throttle / engine telegraph / bridge control
- 三阶段节奏同 Phase A:A0 本体扩 → A1 adapter 接 → A2 桥表 → A3 dry-run → A4 写库

---

## 8. 风险清单 (plan §10 节选)

| # | 风险 | 缓解 |
|---|---|---|
| R1 | Google captcha | adapter 跳过,接受低命中率 |
| R2 | EPO token 过期 | adapter 自动 refresh + 测试 mock |
| R3 | USPTO API 不可达 | 当前跳过,保留代码占位 |
| R7 | per_query_limit 累计超额 | hard cap 20000 抛错防 OOM |
| R11 | macOS Write GBK 坑 | `open(..., encoding='utf-8')` |
| R12 | EPO 429 | rate_limit_sec=1.5s,自动退避 |