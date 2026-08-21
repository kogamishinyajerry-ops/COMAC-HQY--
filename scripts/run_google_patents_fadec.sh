#!/usr/bin/env bash
# ==============================================================================
# HQY v2 重抓 wrapper · FADEC / EEC 控制系统专利
# ==============================================================================
# 这个脚本封装 v2 重抓全过程, 一键跑完 (dry-run → EXPORT → 拉回本地 → 清桶 → 灌入).
#
# 前置:
#   - 已登录 gcloud (gcloud auth login 或 service account)
#   - GCP 项目 ID 默认 throttle-atlas-prior-art (可被环境变量 BQ_PROJECT 覆盖)
#   - 已激活 BigQuery API
#
# 用法:
#   BQ_PROJECT=my-gcp-project bash scripts/run_google_patents_fadec.sh
#
# 风险:
#   - BigQuery 1 TB 扫描免费, 预估 <15 GB, $0 成本
#   - GCS 临时桶 bj-fadec-eec 会建, 跑完自动清 (兜底 GS 桶名带日期防撞名)
#   - 灌入会把 prior_art_patents 表里 source_id='google-patents-bigquery' 旧数据清空
#     历史 v1 数据请提前手动备份到 data/source_archive/archive/google-patents-bigquery-v1/
# ==============================================================================

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BQ_PROJECT="${BQ_PROJECT:-throttle-atlas-prior-art}"
GCS_BUCKET="gs://throttle-atlas-prior-art-fadec-eec-$(date +%Y%m%d-%H%M%S)"
RAW_DIR="$ROOT/data/source_archive/raw/google-patents-bigquery"

echo ">>> BQ_PROJECT = $BQ_PROJECT"
echo ">>> GCS_BUCKET = $GCS_BUCKET"
echo ">>> RAW_DIR     = $RAW_DIR"
echo

# ---------- 1. dry-run COUNT -----------------------------------------------
echo ">>> [1/4] dry-run COUNT (Top 15 国别)"
bq query --use_legacy_sql=false --project_id="$BQ_PROJECT" --format=prettyjson --max_rows=15 '
SELECT pub.country_code, COUNT(DISTINCT pub.publication_number) AS n
FROM `patents-public-data.patents.publications` AS pub,
  UNNEST(pub.cpc) AS cpc
WHERE (cpc.code LIKE "B64D31/%" OR cpc.code LIKE "F02C9/%")
  AND pub.filing_date >= 20000101
  AND (
    EXISTS (SELECT 1 FROM UNNEST(pub.title_localized) t
            WHERE t.language="en"
              AND REGEXP_CONTAINS(LOWER(t.text),
                  r"fadec|eec|full authority digital|electronic engine control|electronic engine controller"))
    OR EXISTS (SELECT 1 FROM UNNEST(pub.abstract_localized) a
               WHERE a.language="en"
                 AND REGEXP_CONTAINS(LOWER(a.text),
                     r"fadec|eec|full authority digital|electronic engine control|electronic engine controller"))
  )
GROUP BY pub.country_code ORDER BY n DESC LIMIT 15
'
echo ">>> dry-run 完成. 看上面各国件数, 估总件数."
if [ "${SKIP_CONFIRM:-0}" != "1" ] && [ -t 0 ]; then
  read -rp "继续 EXPORT? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "用户中止, 不跑 EXPORT."; exit 1; }
else
  echo ">>> SKIP_CONFIRM=1 或 stdin 非 tty, 自动继续"
fi

# ---------- 2. EXPORT DATA → GCS ------------------------------------------
echo ">>> [2/4] EXPORT DATA → GCS"
bq query --use_legacy_sql=false --project_id="$BQ_PROJECT" "
EXPORT DATA OPTIONS(
  uri='${GCS_BUCKET}/prior_art_*.json',
  format='JSON',
  overwrite=true
) AS
SELECT
  pub.publication_number,
  pub.country_code,
  pub.family_id,
  pub.filing_date,
  pub.publication_date,
  pub.grant_date,
  ARRAY(SELECT title.text FROM pub.title_localized title) AS titles_all,
  ARRAY(SELECT title.text FROM pub.title_localized title WHERE title.language = 'zh') AS title_zh,
  ARRAY(SELECT title.text FROM pub.title_localized title WHERE title.language = 'en') AS title_en,
  ARRAY(SELECT abst.text FROM pub.abstract_localized abst WHERE abst.language = 'zh') AS abstract_zh,
  ARRAY(SELECT abst.text FROM pub.abstract_localized abst WHERE abst.language = 'en') AS abstract_en,
  ARRAY(SELECT cpc.code FROM pub.cpc cpc) AS cpc_codes,
  ARRAY(SELECT inv.name FROM pub.inventor_harmonized inv) AS inventors,
  ARRAY(SELECT ass.name FROM pub.assignee_harmonized ass) AS assignees
FROM \`patents-public-data.patents.publications\` AS pub
WHERE (
    EXISTS (SELECT 1 FROM UNNEST(pub.cpc) c
            WHERE c.code LIKE 'B64D31/%'
               OR c.code LIKE 'F02C9/%')
   )
  AND pub.filing_date >= 20000101
  AND (
    EXISTS (SELECT 1 FROM UNNEST(pub.title_localized) t
            WHERE t.language = 'en'
              AND REGEXP_CONTAINS(LOWER(t.text),
                  r'fadec|eec|full authority digital|electronic engine control|electronic engine controller'))
    OR EXISTS (SELECT 1 FROM UNNEST(pub.abstract_localized) a
               WHERE a.language = 'en'
                 AND REGEXP_CONTAINS(LOWER(a.text),
                     r'fadec|eec|full authority digital|electronic engine control|electronic engine controller'))
  )
"

# ---------- 3. 拉回本地 -----------------------------------------------------
echo ">>> [3/4] gsutil cp → 本地"
mkdir -p "$RAW_DIR"
# 先备份旧 raw (如果存在且非空)
if [ -d "$RAW_DIR" ] && [ "$(ls -A "$RAW_DIR" 2>/dev/null)" ]; then
  ARCHIVE="$ROOT/data/source_archive/archive/google-patents-bigquery-v1-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$(dirname "$ARCHIVE")"
  mv "$RAW_DIR" "$ARCHIVE"
  echo "    旧 raw 归档到 $ARCHIVE"
  mkdir -p "$RAW_DIR"
fi
gsutil -m cp "${GCS_BUCKET}/prior_art_*.json" "$RAW_DIR/"
echo "    本地 raw shard 数: $(ls "$RAW_DIR" | wc -l)"

# ---------- 4. 清桶 + 灌入 -------------------------------------------------
echo ">>> [4/4] 清桶 + 灌入"
gsutil -m rm -r "$GCS_BUCKET" 2>/dev/null || true
echo "    GCS 桶已清 (或不存在)"
echo

PYTHONPATH=. python3 import_prior_art.py
echo
echo ">>> v2 重抓完成!"
echo ">>> 后续:"
echo "    python3 scripts/migrate_ontology.py   # 重算 cross_match (FADEC/EEC ↔ 25.1143)"
echo "    PYTHONPATH=. python3 -m src.export_for_pace  # 重导 pace_export.yaml"
echo "    PYTHONPATH=. python3 -m pytest -q     # 测试 (35/35 应全过)"
