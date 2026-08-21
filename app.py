from __future__ import annotations

import argparse
import json
import mimetypes
import re
import sqlite3
import threading
import time
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from build_db import DB_PATH, initialize


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


def db_connect() -> sqlite3.Connection:
    # The knowledge base is intentionally opened read-only at runtime. This
    # keeps the app portable on restricted drives and prevents accidental edits
    # to the curated source register. Rebuild it with build_db.py when updating.
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE name = ? LIMIT 1",
        (table_name,),
    ).fetchone() is not None


def get_models() -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute("SELECT * FROM models ORDER BY category, family, id").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["geometry"] = json.loads(item.pop("geometry_json"))
        item["features"] = json.loads(item.pop("features_json"))
        result.append(item)
    return result


def get_sources() -> list[dict]:
    with db_connect() as conn:
        if table_exists(conn, "source_snapshots"):
            rows = conn.execute(
                """
                SELECT s.*, sp.status AS archive_status,
                       sp.fetched_at AS archive_fetched_at,
                       sp.byte_size AS archive_byte_size,
                       sp.local_path AS archive_local_path,
                       sp.sha256 AS archive_sha256,
                       sp.content_type AS archive_content_type
                FROM sources s
                LEFT JOIN source_snapshots sp
                  ON sp.source_id = s.id AND sp.is_current = 1
                ORDER BY s.kind, s.organization
                """
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM sources ORDER BY kind, organization").fetchall()
    return [dict(row) for row in rows]


def get_components() -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute("SELECT * FROM components ORDER BY order_index, id").fetchall()
    return [dict(row) for row in rows]


def get_constraints(component_id: str) -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT r.*, s.title_zh AS source_title_zh, s.title_en AS source_title_en,
                   s.organization, s.url, s.quality
            FROM regulatory_constraints r
            JOIN sources s ON s.id = r.source_id
            WHERE r.component_id = ?
            ORDER BY r.order_index, r.authority
            """,
            (component_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_design_components() -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT d.*, s.title_zh AS source_title_zh, s.title_en AS source_title_en,
                   s.organization, s.url
            FROM design_component_options d
            JOIN sources s ON s.id = d.source_id
            ORDER BY d.slot_id, d.order_index
            """
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        result.append(item)
    return result


def get_patents() -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT p.*, s.url, s.organization
            FROM patents p JOIN sources s ON s.id = p.source_id
            ORDER BY p.priority_date DESC, p.publication_no
            """
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["change_zh"] = json.loads(item.pop("change_zh_json"))
        item["change_en"] = json.loads(item.pop("change_en_json"))
        item["tags"] = json.loads(item.pop("tags_json"))
        result.append(item)
    return result


def get_pilot_needs() -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT n.*, s.title_zh AS source_title_zh, s.title_en AS source_title_en,
                   s.organization, s.url
            FROM pilot_needs n JOIN sources s ON s.id = n.source_id
            ORDER BY n.severity DESC, n.evidence_count DESC, n.id
            """
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        item["goals"] = json.loads(item.pop("goals_json"))
        result.append(item)
    return result


def get_invention_patterns() -> list[dict]:
    with db_connect() as conn:
        rows = conn.execute(
            "SELECT * FROM invention_patterns ORDER BY difficulty, id"
        ).fetchall()
    result = []
    json_fields = [
        "suitable_tags", "avoid_tags", "risk_tags",
        "claim_zh", "claim_en", "validation_zh", "validation_en",
    ]
    for row in rows:
        item = dict(row)
        for field in json_fields:
            item[field] = json.loads(item.pop(f"{field}_json"))
        result.append(item)
    return result


def get_stats() -> dict:
    with db_connect() as conn:
        models = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
        sources = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
        seed_chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        organizations = conn.execute("SELECT COUNT(DISTINCT organization) FROM sources").fetchone()[0]
        components = conn.execute("SELECT COUNT(*) FROM components").fetchone()[0]
        constraints = conn.execute("SELECT COUNT(*) FROM regulatory_constraints").fetchone()[0]
        design_options = conn.execute("SELECT COUNT(*) FROM design_component_options").fetchone()[0]
        patents = conn.execute("SELECT COUNT(*) FROM patents").fetchone()[0]
        pilot_needs = conn.execute("SELECT COUNT(*) FROM pilot_needs").fetchone()[0]
        invention_patterns = conn.execute("SELECT COUNT(*) FROM invention_patterns").fetchone()[0]
        archive = {
            "archived_sources": 0,
            "archive_documents": 0,
            "archive_chunks": 0,
            "archive_bytes": 0,
            "archive_last_sync": "",
            "archive_run_status": "not_started",
            "archive_failed": 0,
        }
        if table_exists(conn, "source_archive_runs"):
            archive_row = conn.execute(
                """
                SELECT
                  (SELECT COUNT(DISTINCT source_id)
                     FROM source_snapshots
                    WHERE is_current = 1 AND status = 'ok') AS archived_sources,
                  (SELECT COUNT(d.id)
                     FROM source_documents d
                     JOIN source_snapshots sp ON sp.id = d.snapshot_id
                    WHERE sp.is_current = 1 AND sp.status = 'ok') AS archive_documents,
                  (SELECT COUNT(ac.id)
                     FROM source_archive_chunks ac
                     JOIN source_documents d ON d.id = ac.document_id
                     JOIN source_snapshots sp ON sp.id = d.snapshot_id
                    WHERE sp.is_current = 1 AND sp.status = 'ok') AS archive_chunks,
                  (SELECT COALESCE(SUM(byte_size), 0)
                     FROM source_snapshots
                    WHERE is_current = 1 AND status = 'ok') AS archive_bytes,
                  (SELECT COALESCE(MAX(fetched_at), '')
                     FROM source_snapshots
                    WHERE is_current = 1 AND status = 'ok') AS archive_last_sync
                """
            ).fetchone()
            latest_run = conn.execute(
                """
                SELECT status, failed
                FROM source_archive_runs
                ORDER BY started_at DESC
                LIMIT 1
                """
            ).fetchone()
            if archive_row:
                archive.update(dict(archive_row))
            if latest_run:
                archive["archive_run_status"] = latest_run["status"]
                archive["archive_failed"] = latest_run["failed"]
    return {
        "models": models,
        "sources": sources,
        "chunks": seed_chunks + archive["archive_chunks"],
        "seed_chunks": seed_chunks,
        "organizations": organizations,
        "components": components,
        "constraints": constraints,
        "design_options": design_options,
        "patents": patents,
        "pilot_needs": pilot_needs,
        "invention_patterns": invention_patterns,
        **archive,
    }


def tokenize(query: str) -> list[str]:
    query = query.strip().lower()
    english = re.findall(r"[a-z0-9][a-z0-9+/-]*", query)
    chinese_runs = re.findall(r"[\u4e00-\u9fff]+", query)
    chinese = []
    for run in chinese_runs:
        chinese.append(run)
        if len(run) > 2:
            chinese.extend(run[i : i + 2] for i in range(len(run) - 1))
    tokens = [query] + english + chinese
    # 同义词扩展:让"反推"/"autothrottle"等术语命中 BigQuery 英文 patent 的同义表述
    tokens.extend(_expand_synonyms(tokens))
    return list(dict.fromkeys(token for token in tokens if token))


# 油门台术语同义词表(中→英,英→英,英缩写→全称)
# 只扩展术语,不去碰普通词,避免噪音
_SYNONYMS = {
    # 中文 → 英文
    "反推": ["reverse thrust", "reverse", "retard", "ground idle"],
    "油门": ["throttle lever", "throttle", "power lever"],
    "卡位": ["detent", "gate", "stop"],
    "锁止": ["lock", "gate", "stop", "interlock"],
    "告警": ["alert", "warning", "caution", "indication"],
    "推力": ["thrust"],
    "振动": ["vibration", "shake"],
    "复飞": ["go-around", "go around", "to/ga"],
    "触觉": ["haptic", "tactile"],
    "手柄": ["lever", "handle", "stick"],
    "断开": ["disconnect", "disengage"],
    "切断": ["cutoff", "shutoff", "shut off"],
    "起飞": ["takeoff", "take-off"],
    "着陆": ["landing", "touchdown"],
    "慢车": ["idle"],
    "调速": ["governor", "speed control"],
    # 英文缩写 → 全称
    "autothrottle": ["automatic throttle"],
    "throttle": ["throttle lever", "power lever"],
    "reverse": ["reverse thrust", "retard", "ground idle"],
    "detent": ["gate", "stop"],
    "to/ga": ["takeoff", "go-around", "go around"],
}


def _expand_synonyms(tokens: list[str]) -> list[str]:
    expanded: list[str] = []
    for tok in tokens:
        syns = _SYNONYMS.get(tok)
        if syns:
            expanded.extend(syns)
    return expanded


def make_excerpt(text: str, terms: list[str], length: int = 900) -> str:
    if len(text) <= length:
        return text
    lower = text.lower()
    positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
    center = min(positions) if positions else 0
    start = max(0, center - 180)
    end = min(len(text), start + length)
    if end - start < length:
        start = max(0, end - length)
    excerpt = text[start:end].strip()
    return f"{'…' if start else ''}{excerpt}{'…' if end < len(text) else ''}"


def search_chunks(query: str, limit: int = 8) -> list[dict]:
    terms = tokenize(query)
    if not terms:
        return []
    with db_connect() as conn:
        rows = conn.execute(
            """
            SELECT c.*, s.title_zh AS source_title_zh, s.title_en AS source_title_en,
                   s.organization, s.url, s.kind, s.quality
            FROM chunks c JOIN sources s ON s.id = c.source_id
            """
        ).fetchall()
        archive_rows = []
        if table_exists(conn, "source_archive_chunks"):
            archive_rows = conn.execute(
                """
                SELECT ac.id, ac.title, ac.text, ac.source_id,
                       s.title_zh AS source_title_zh,
                       s.title_en AS source_title_en,
                       s.organization, s.url, s.kind, s.quality
                FROM source_archive_chunks ac
                JOIN source_documents d ON d.id = ac.document_id
                JOIN source_snapshots sp
                  ON sp.id = d.snapshot_id
                 AND sp.is_current = 1
                 AND sp.status = 'ok'
                JOIN sources s ON s.id = ac.source_id
                """
            ).fetchall()
    ranked = []
    for row in rows:
        item = dict(row)
        title = f"{item['title_zh']} {item['title_en']}".lower()
        body = f"{item['body_zh']} {item['body_en']}".lower()
        score = 0
        matched = []
        for term in terms:
            title_hits = title.count(term)
            body_hits = body.count(term)
            if title_hits or body_hits:
                matched.append(term)
                score += title_hits * 5 + body_hits * 2
        if score:
            item["score"] = score
            item["matched_terms"] = matched[:5]
            item["archive"] = False
            ranked.append(item)
    for row in archive_rows:
        raw = dict(row)
        title = (
            f"{raw['title']} {raw['source_title_zh']} "
            f"{raw['source_title_en']}"
        ).lower()
        body = raw["text"].lower()
        score = 0
        matched = []
        for term in terms:
            title_hits = title.count(term)
            body_hits = body.count(term)
            if title_hits or body_hits:
                matched.append(term)
                score += title_hits * 5 + body_hits * 2
        if score:
            ranked.append(
                {
                    "id": f"archive-{raw['id']}",
                    "title_zh": raw["source_title_zh"],
                    "title_en": raw["source_title_en"],
                    "body_zh": make_excerpt(raw["text"], matched),
                    "body_en": make_excerpt(raw["text"], matched),
                    "source_id": raw["source_id"],
                    "source_title_zh": raw["source_title_zh"],
                    "source_title_en": raw["source_title_en"],
                    "organization": raw["organization"],
                    "url": raw["url"],
                    "kind": raw["kind"],
                    "quality": raw["quality"],
                    "score": score + 1,
                    "matched_terms": matched[:5],
                    "archive": True,
                }
            )
    ranked.sort(key=lambda x: (-x["score"], str(x["id"])))
    requested = max(1, min(limit, 20))
    selected: list[dict] = []
    per_source: dict[str, int] = {}
    for item in ranked:
        source_id = item["source_id"]
        if per_source.get(source_id, 0) >= 2:
            continue
        selected.append(item)
        per_source[source_id] = per_source.get(source_id, 0) + 1
        if len(selected) >= requested:
            break
    return selected


class Handler(BaseHTTPRequestHandler):
    server_version = "ThrottleAtlas/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, payload, status=HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/models":
            return self.send_json(get_models())
        if parsed.path == "/api/sources":
            return self.send_json(get_sources())
        if parsed.path == "/api/components":
            return self.send_json(get_components())
        if parsed.path == "/api/constraints":
            params = parse_qs(parsed.query)
            component_id = params.get("component", [""])[0]
            return self.send_json({"component": component_id, "constraints": get_constraints(component_id)})
        if parsed.path == "/api/design-components":
            return self.send_json(get_design_components())
        if parsed.path == "/api/patents":
            return self.send_json(get_patents())
        if parsed.path == "/api/pilot-needs":
            return self.send_json(get_pilot_needs())
        if parsed.path == "/api/invention-patterns":
            return self.send_json(get_invention_patterns())
        if parsed.path == "/api/stats":
            return self.send_json(get_stats())
        if parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            query = params.get("q", [""])[0]
            return self.send_json({"query": query, "results": search_chunks(query)})
        if parsed.path == "/api/health":
            return self.send_json({"ok": True, "database": DB_PATH.exists(), "time": time.time()})
        self.serve_static(parsed.path)

    def serve_static(self, path: str) -> None:
        relative = unquote(path).lstrip("/") or "index.html"
        target = (STATIC / relative).resolve()
        if STATIC.resolve() not in target.parents and target != STATIC.resolve():
            return self.send_error(HTTPStatus.FORBIDDEN)
        if target.is_dir():
            target = target / "index.html"
        if not target.exists():
            return self.send_error(HTTPStatus.NOT_FOUND)
        mime, _ = mimetypes.guess_type(target.name)
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime or 'application/octet-stream'}" + ("; charset=utf-8" if (mime or "").startswith("text/") else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache" if target.suffix in {".html", ".js", ".css"} else "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)


def run(port: int, open_browser: bool) -> None:
    if not DB_PATH.exists():
        initialize()
    server = None
    active_port = port
    for candidate in range(port, port + 20):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", candidate), Handler)
            active_port = candidate
            break
        except OSError:
            continue
    if server is None:
        raise RuntimeError("No free local port found.")
    url = f"http://127.0.0.1:{active_port}"
    print("")
    print("  THROTTLE ATLAS / 油门台图谱")
    print(f"  {url}")
    print("  关闭此窗口即可停止应用。 / Close this window to stop.")
    print("")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    run(args.port, args.open)
