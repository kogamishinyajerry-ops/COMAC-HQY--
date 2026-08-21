"""COMAC-HQY-专利助手 — Agent CLI 入口。

薄 facade,把现有模块 (build_db / export_for_pace / patrol_48h / governance / app)
封装成一组可单独运行的子命令。LLM 集成留到下一阶段,当前子命令全部离线可跑。

子命令:
  serve         启本地 Web UI (http://localhost:8765, 默认端口)
  rebuild       重建 SQLite 知识库 (跑 build_db.initialize)
  query         关键词查 patents / regulatory_constraints
  export        重新生成 outputs/pace_export.yaml (供 P-ACE / bridge 消费)
  patrol        跑 4 路巡检 → outputs/governance/
  check         跑 17 项治理守卫
  stats         列出 db 表 + 计数
  curate        列 8 条 curated 专利 (供共同发明器使用)
  ontology      加载并打印本体 yaml
  help          子命令帮助
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# 轻量镜像:默认离线,避免 import build_db 时触发 AWKB 网络同步
# 显式开: `AWKB_ENABLED=1 python agent_cli.py rebuild` 拉最新条款正文
os.environ.setdefault("AWKB_ENABLED", "0")

# 现有模块导入
import build_db                                # noqa: E402
from src.export_for_pace import export as run_export  # noqa: E402
from src.governance.data_integrity import run_all_checks, require_all_pass  # noqa: E402
from src.ontology_loader import ONTOLOGY_FILES, load_bundle  # noqa: E402

DB_PATH = ROOT / "data" / "throttle_knowledge.db"


# ============================================================
# 通用
# ============================================================

def _ensure_db() -> bool:
    """确保 db 存在,不存在时打印重建指引并返回 False。"""
    if not DB_PATH.exists():
        print(f"[!] 知识库不存在: {DB_PATH}", file=sys.stderr)
        print("    跑 `python agent_cli.py rebuild` 或 `python build_db.py` 重建。", file=sys.stderr)
        return False
    return True


def _connect_ro() -> sqlite3.Connection:
    """只读连接 (跟 app.py 一致,防止误写)。"""
    uri = f"{DB_PATH.as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# 子命令实现
# ============================================================

def cmd_serve(args: argparse.Namespace) -> int:
    """启 Web UI,默认 8765 端口。"""
    from app import get_models, get_patents, get_components, get_constraints
    import mimetypes
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, unquote, urlparse
    import webbrowser
    import threading

    port = args.port
    static_dir = ROOT / "static"

    class Handler(BaseHTTPRequestHandler):
        # 复用 app.py 的查询函数
        do_GET = BaseHTTPRequestHandler.do_GET  # 占位,下方覆盖

        def log_message(self, fmt: str, *args2) -> None:  # noqa: A003
            pass  # 静默

        def _json(self, payload, status: int = 200) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _file(self, path: Path) -> None:
            if not path.is_file():
                self.send_error(404)
                return
            ctype, _ = mimetypes.guess_type(str(path))
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", ctype or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            try:
                if parsed.path == "/api/models":
                    return self._json(get_models())
                if parsed.path == "/api/patents":
                    return self._json(get_patents())
                if parsed.path == "/api/components":
                    return self._json(get_components())
                if parsed.path == "/api/constraints":
                    cid = (qs.get("component_id") or [""])[0]
                    return self._json(get_constraints(cid))
                if parsed.path == "/" or parsed.path == "/index.html":
                    return self._file(static_dir / "index.html")
                if parsed.path.startswith("/static/"):
                    rel = unquote(parsed.path[len("/static/"):])
                    return self._file(static_dir / rel)
                self.send_error(404)
            except Exception as exc:  # noqa: BLE001
                self._json({"error": str(exc)}, status=500)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[✓] COMAC-HQY-专利助手 启动: http://127.0.0.1:{port}")
    print(f"    静态资源: {static_dir}")
    print(f"    知识库:   {DB_PATH}  ({'已加载' if DB_PATH.exists() else '缺失,跑 rebuild 重建'})")
    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[✓] 收到 Ctrl+C,关闭服务。")
        server.shutdown()
    return 0


def cmd_rebuild(args: argparse.Namespace) -> int:
    """重建 SQLite 知识库。"""
    print(f"[•] 重建知识库: {DB_PATH}")
    build_db.initialize(DB_PATH)
    print(f"[✓] 重建完成: {DB_PATH}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    """关键词查 patents / regulatory_constraints。"""
    if not _ensure_db():
        return 1
    keyword = args.keyword.strip()
    if not keyword:
        print("[!] 关键词为空,见 `agent_cli.py query --help`", file=sys.stderr)
        return 2
    target = args.target
    limit = args.limit

    with _connect_ro() as conn:
        if target == "patents":
            rows = conn.execute(
                """
                SELECT p.publication_no, p.jurisdiction, p.assignee, p.priority_date,
                       p.title_zh, p.title_en, p.status_zh, p.status_en
                FROM patents p
                WHERE p.title_zh LIKE ? OR p.title_en LIKE ?
                ORDER BY p.priority_date DESC
                LIMIT ?
                """,
                (f"%{keyword}%", f"%{keyword}%", limit),
            ).fetchall()
            results = [dict(r) for r in rows]
        elif target == "constraints":
            rows = conn.execute(
                """
                SELECT r.authority, r.clause_number, r.title_zh, r.title_en,
                       c.id AS component_id, c.name_zh AS component_name
                FROM regulatory_constraints r
                JOIN components c ON c.id = r.component_id
                WHERE r.title_zh LIKE ? OR r.title_en LIKE ? OR r.clause_number LIKE ?
                ORDER BY r.authority, r.clause_number
                LIMIT ?
                """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
            ).fetchall()
            results = [dict(r) for r in rows]
        else:  # all
            results = []
            for r in conn.execute(
                "SELECT p.publication_no AS no, p.title_zh AS title FROM patents "
                "WHERE p.title_zh LIKE ? LIMIT ?",
                (f"%{keyword}%", limit),
            ).fetchall():
                results.append({"type": "patent", **dict(r)})
            for r in conn.execute(
                "SELECT r.authority || ' ' || r.clause_number AS no, r.title_zh AS title "
                "FROM regulatory_constraints r "
                "WHERE r.title_zh LIKE ? OR r.clause_number LIKE ? LIMIT ?",
                (f"%{keyword}%", f"%{keyword}%", limit),
            ).fetchall():
                results.append({"type": "clause", **dict(r)})
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n[•] {len(results)} 条结果 (target={target}, limit={limit})", file=sys.stderr)
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """重新生成 pace_export.yaml。"""
    if not _ensure_db():
        return 1
    out = run_export()
    size = out.stat().st_size
    print(f"[✓] pace_export.yaml 已生成: {out} ({size:,} bytes)")
    return 0


def cmd_patrol(args: argparse.Namespace) -> int:
    """跑 4 路巡检 (count / scope / integrity / cross_match 刷新)。"""
    if not _ensure_db():
        return 1
    # 直接 import + 调 main(),把 patrol_48h 原本打 stdout 的部分接管
    import scripts.patrol_48h as p
    return p.main()


def cmd_check(args: argparse.Namespace) -> int:
    """跑 17 项治理守卫。"""
    if not _ensure_db():
        return 1
    with _connect_ro() as conn:
        results = run_all_checks(conn)
    failed = [r for r in results if not r.passed]
    for r in results:
        marker = "✓" if r.passed else "✗"
        print(f"  {marker} {r.name:50s}  count={r.count:6d}  expect={r.expectation}")
    print(f"\n[•] {len(results) - len(failed)}/{len(results)} 守卫通过")
    return 0 if not failed else 1


def cmd_stats(args: argparse.Namespace) -> int:
    """列出 db 表 + 计数。"""
    if not _ensure_db():
        return 1
    with _connect_ro() as conn:
        tables = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' "
                "AND name NOT LIKE '%_data' AND name NOT LIKE '%_idx' "
                "AND name NOT LIKE '%_content' AND name NOT LIKE '%_docsize' "
                "AND name NOT LIKE '%_config' "
                "ORDER BY name"
            )
        ]
        out = {}
        for t in tables:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_curate(args: argparse.Namespace) -> int:
    """列 8 条 curated 专利 (供共同发明器使用)。"""
    if not _ensure_db():
        return 1
    with _connect_ro() as conn:
        rows = conn.execute(
            """
            SELECT p.publication_no, p.jurisdiction, p.assignee, p.priority_date,
                   p.title_zh, p.title_en, p.applicable_aircraft_json
            FROM patents p
            ORDER BY p.priority_date DESC
            """
        ).fetchall()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["applicable_aircraft"] = json.loads(item.pop("applicable_aircraft_json") or "[]")
        except json.JSONDecodeError:
            item["applicable_aircraft"] = []
        items.append(item)
    print(json.dumps({"curated_patents": items, "count": len(items)},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_ontology(args: argparse.Namespace) -> int:
    """加载并打印本体 yaml。"""
    bundle = load_bundle()  # list[(Path, dict)]
    summary = {
        "ontology_files": [name for name in ONTOLOGY_FILES],
        "counts": {path.name: len(data["entities"]) for path, data in bundle},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.verbose:
        for path, data in bundle:
            ents = data["entities"]
            print(f"\n--- {path.name} ({len(ents)} 条) ---")
            print(json.dumps(ents[:3], ensure_ascii=False, indent=2))
            if len(ents) > 3:
                print(f"  ... 还有 {len(ents) - 3} 条")
    return 0


# ============================================================
# argparse
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent_cli",
        description="COMAC-HQY-专利助手 Agent CLI (轻量镜像版)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("serve", help="启 Web UI")
    sp.add_argument("--port", type=int, default=8765, help="监听端口 (默认 8765)")
    sp.add_argument("--no-browser", action="store_true", help="不自动开浏览器")
    sp.set_defaults(func=cmd_serve)

    sub.add_parser("rebuild", help="重建 SQLite 知识库").set_defaults(func=cmd_rebuild)

    sp = sub.add_parser("query", help="关键词查 patents / clauses")
    sp.add_argument("keyword", help="关键词 (中英文均可)")
    sp.add_argument("--target", choices=["patents", "constraints", "all"], default="all")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(func=cmd_query)

    sub.add_parser("export", help="生成 pace_export.yaml (P-ACE 联动)").set_defaults(func=cmd_export)
    sub.add_parser("patrol", help="跑 4 路巡检").set_defaults(func=cmd_patrol)
    sub.add_parser("check", help="跑 17 项治理守卫").set_defaults(func=cmd_check)
    sub.add_parser("stats", help="db 表 + 计数").set_defaults(func=cmd_stats)
    sub.add_parser("curate", help="列 8 条 curated 专利").set_defaults(func=cmd_curate)

    sp = sub.add_parser("ontology", help="加载本体 yaml")
    sp.add_argument("-v", "--verbose", action="store_true", help="打印前 3 条样本")
    sp.set_defaults(func=cmd_ontology)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
