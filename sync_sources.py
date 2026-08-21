from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from build_db import DB_PATH


ROOT = Path(__file__).resolve().parent
ARCHIVE_DIR = ROOT / "data" / "source_archive"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0 Safari/537.36 ThrottleAtlasResearch/1.0"
)
SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "template"}
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl", "dt",
    "figcaption", "figure", "footer", "h1", "h2", "h3", "h4", "h5", "h6",
    "header", "hr", "li", "main", "nav", "ol", "p", "pre", "section", "table",
    "td", "th", "tr", "ul",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.skip_depth = 0
        self.in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        value = data.strip()
        if not value:
            return
        self.parts.append(value)
        self.parts.append(" ")
        if self.in_title:
            self.title_parts.append(value)


def clean_text(value: str) -> str:
    value = html.unescape(value).replace("\x00", " ")
    value = re.sub(r"[ \t\f\v]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    lines = [line.strip() for line in value.splitlines()]
    deduped: list[str] = []
    for line in lines:
        if not line:
            if deduped and deduped[-1] != "":
                deduped.append("")
            continue
        if deduped and line == deduped[-1]:
            continue
        deduped.append(line)
    return "\n".join(deduped).strip()


def decode_bytes(data: bytes, charset: str) -> tuple[str, str]:
    candidates = [charset, "utf-8", "gb18030", "latin-1"]
    for candidate in dict.fromkeys(item for item in candidates if item):
        try:
            return data.decode(candidate), candidate
        except (LookupError, UnicodeDecodeError):
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def extract_html(data: bytes, charset: str) -> tuple[str, str, str, int]:
    decoded, used_charset = decode_bytes(data, charset)
    parser = ReadableHTMLParser()
    parser.feed(decoded)
    parser.close()
    title = clean_text(" ".join(parser.title_parts))
    return clean_text("".join(parser.parts)), title, used_charset, 0


def extract_pdf(data: bytes) -> tuple[str, str, str, int, str]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data), strict=False)
        pages: list[str] = []
        for index, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception as exc:
                text = f"[page {index + 1} extraction error: {exc}]"
            pages.append(f"\n\n[PAGE {index + 1}]\n{text}")
        title = ""
        if reader.metadata:
            title = str(reader.metadata.get("/Title") or "").strip()
        return clean_text("".join(pages)), title, "binary", len(reader.pages), "pypdf"
    except Exception as pypdf_error:
        import pdfplumber

        pages = []
        with pdfplumber.open(io.BytesIO(data)) as document:
            for index, page in enumerate(document.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as exc:
                    text = f"[page {index + 1} extraction error: {exc}]"
                pages.append(f"\n\n[PAGE {index + 1}]\n{text}")
            page_count = len(document.pages)
            metadata = document.metadata or {}
        title = str(metadata.get("Title") or "").strip()
        extracted = clean_text("".join(pages))
        if not extracted:
            raise RuntimeError(f"PDF text extraction failed: {pypdf_error}")
        return extracted, title, "binary", page_count, "pdfplumber"


def detect_language(text: str) -> str:
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text[:100_000]))
    latin = len(re.findall(r"[A-Za-z]", text[:100_000]))
    if chinese > latin * 0.25:
        return "zh" if latin < chinese * 0.3 else "mixed"
    return "en" if latin else "unknown"


def extension_for(content_type: str, final_url: str, data: bytes) -> str:
    lower_type = content_type.lower()
    suffix = Path(urlparse(final_url).path).suffix.lower()
    if data.startswith(b"%PDF") or "application/pdf" in lower_type:
        return ".pdf"
    if "html" in lower_type:
        return ".html"
    if "json" in lower_type:
        return ".json"
    if "xml" in lower_type:
        return ".xml"
    if lower_type.startswith("text/"):
        return ".txt"
    if suffix and len(suffix) <= 8:
        return suffix
    return ".bin"


def chunk_text(text: str, target: int = 1800, overlap: int = 220) -> list[tuple[int, int, str]]:
    if not text:
        return []
    chunks: list[tuple[int, int, str]] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(length, start + target)
        if end < length:
            search_from = min(length, start + int(target * 0.62))
            candidates = [
                text.rfind("\n\n", search_from, end),
                text.rfind("\n", search_from, end),
                text.rfind("。", search_from, end),
                text.rfind(". ", search_from, end),
            ]
            boundary = max(candidates)
            if boundary > start:
                end = boundary + 1
        value = text[start:end].strip()
        if value:
            chunks.append((start, end, value))
        if end >= length:
            break
        start = max(start + 1, end - overlap)
    return chunks


def fetch_url_with_curl(url: str, timeout: int, max_bytes: int) -> dict:
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if not curl:
        raise RuntimeError("curl fallback is not available")
    body_handle = tempfile.NamedTemporaryFile(prefix="throttle-source-", delete=False)
    body_path = Path(body_handle.name)
    body_handle.close()
    marker = "__THROTTLE_ARCHIVE_META__"
    try:
        result = subprocess.run(
            [
                curl, "--location", "--fail", "--silent", "--show-error",
                "--compressed", "--retry", "1", "--retry-all-errors",
                "--connect-timeout", str(max(5, min(timeout, 20))),
                "--max-time", str(timeout),
                "--user-agent", USER_AGENT,
                "--header",
                "Accept: text/html,application/xhtml+xml,application/pdf,text/plain,application/json;q=0.9,*/*;q=0.6",
                "--header", "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
                "--output", str(body_path),
                "--write-out",
                f"{marker}%{{url_effective}}\\t%{{http_code}}\\t%{{content_type}}",
                url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout * 2 + 20,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or f"curl exited {result.returncode}")
        meta = result.stdout.rsplit(marker, 1)[-1].strip().split("\t", 2)
        if len(meta) != 3:
            raise RuntimeError("curl returned incomplete response metadata")
        data = body_path.read_bytes()
        if len(data) > max_bytes:
            raise ValueError(f"download exceeds {max_bytes} bytes")
        final_url, status_text, content_type_header = meta
        charset_match = re.search(r"charset=([^;\s]+)", content_type_header, re.I)
        return {
            "data": data,
            "final_url": final_url,
            "http_status": int(status_text or 0),
            "content_type": content_type_header.split(";", 1)[0].strip().lower()
            or "application/octet-stream",
            "charset": charset_match.group(1).strip("\"'") if charset_match else "",
            "etag": "",
            "last_modified": "",
        }
    finally:
        body_path.unlink(missing_ok=True)


def fetch_url(url: str, timeout: int, max_bytes: int, retries: int = 2) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf,text/plain,application/json;q=0.9,*/*;q=0.6",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        },
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > max_bytes:
                    raise ValueError(f"content length {content_length} exceeds {max_bytes}")
                data = response.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ValueError(f"download exceeds {max_bytes} bytes")
                content_type_header = response.headers.get("Content-Type", "")
                content_type = content_type_header.split(";", 1)[0].strip().lower()
                charset_match = re.search(r"charset=([^;\s]+)", content_type_header, re.I)
                return {
                    "data": data,
                    "final_url": response.geturl(),
                    "http_status": getattr(response, "status", 200),
                    "content_type": content_type or "application/octet-stream",
                    "charset": charset_match.group(1).strip("\"'") if charset_match else "",
                    "etag": response.headers.get("ETag", ""),
                    "last_modified": response.headers.get("Last-Modified", ""),
                }
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.2 * (attempt + 1))
    try:
        return fetch_url_with_curl(url, timeout=timeout, max_bytes=max_bytes)
    except Exception as curl_error:
        urllib_message = str(last_error) if last_error else "unknown urllib error"
        raise RuntimeError(f"urllib: {urllib_message}; curl: {curl_error}") from curl_error


def ensure_archive_schema(conn: sqlite3.Connection) -> None:
    required = {
        "source_archive_runs", "source_snapshots", "source_documents",
        "source_archive_chunks", "source_archive_fts",
    }
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
        ).fetchall()
    }
    missing = required - existing
    if missing:
        raise RuntimeError(
            f"archive schema missing: {', '.join(sorted(missing))}; run build_db.py first"
        )


def recover_incomplete_runs(conn: sqlite3.Connection) -> None:
    running = conn.execute(
        "SELECT id FROM source_archive_runs WHERE status = 'running'"
    ).fetchall()
    for row in running:
        run_id = row["id"]
        counts = conn.execute(
            """
            SELECT COUNT(*) AS processed,
                   SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS succeeded,
                   SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS failed,
                   SUM(CASE WHEN status = 'ok' THEN byte_size ELSE 0 END) AS bytes
            FROM source_snapshots
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()
        conn.execute(
            """
            UPDATE source_archive_runs
            SET finished_at = ?, status = 'interrupted',
                succeeded = ?, failed = ?, bytes_downloaded = ?
            WHERE id = ?
            """,
            (
                utc_now(), counts["succeeded"] or 0, counts["failed"] or 0,
                counts["bytes"] or 0, run_id,
            ),
        )
    if running:
        conn.commit()


_ARCHIVE_POLICY_RE = re.compile(r"\[archive_policy\s*=\s*(metadata_only|download)\s*\]")


def detect_archive_policy(source: sqlite3.Row) -> str:
    """从 note_zh 末尾标记解析 archive_policy。返回 'metadata_only' 或 'download'。

    规则（守纪律 2）：
    - 标记 `[archive_policy=metadata_only]` -> 只登记 URL，不下载内容
    - 标记 `[archive_policy=download]`        -> 走正常下载流程
    - 无标记 + kind == 'licensed_media'      -> 兼容老数据，视为 metadata_only
    - 无标记 + 其他 kind                      -> 默认 download
    """
    note_zh = source["note_zh"] if "note_zh" in source.keys() else ""
    match = _ARCHIVE_POLICY_RE.search(note_zh)
    if match:
        return match.group(1).strip().lower()
    if source["kind"] == "licensed_media":
        return "metadata_only"
    return "download"


def archive_metadata_only(
    conn: sqlite3.Connection,
    run_id: str,
    source: sqlite3.Row,
) -> dict:
    """metadata_only 归档：不下载内容，只写一行 snapshot 记录登记 URL。

    用于 SAE ARP4761 / ARP5580 / ATA iSpec 2200 等付费标准。
    snapshot 的 status='metadata_only'，sha256/local_path 为空。
    """
    source_id = source["id"]
    fetched_at = utc_now()
    conn.execute(
        "UPDATE source_snapshots SET is_current = 0 WHERE source_id = ?",
        (source_id,),
    )
    conn.execute(
        """
        INSERT INTO source_snapshots (
            run_id, source_id, fetched_at, final_url, http_status,
            content_type, charset, etag, last_modified, sha256, byte_size,
            local_path, status, error, is_current
        ) VALUES (?, ?, ?, ?, NULL, '', '', '', '', '', 0, '', 'metadata_only', '', 1)
        """,
        (run_id, source_id, fetched_at, source["url"]),
    )
    conn.commit()
    return {
        "status": "ok",
        "metadata_only": True,
        "bytes": 0,
        "text_length": 0,
        "chunks": 0,
        "pages": 0,
        "method": "metadata_only",
        "local_path": "",
    }


def archive_source(
    conn: sqlite3.Connection,
    run_id: str,
    source: sqlite3.Row,
    archive_dir: Path,
    timeout: int,
    max_bytes: int,
) -> dict:
    source_id = source["id"]
    # 守纪律 2：metadata_only 来源不下载内容，只登记 URL
    if detect_archive_policy(source) == "metadata_only":
        return archive_metadata_only(conn, run_id, source)
    fetched_at = utc_now()
    try:
        response = fetch_url(source["url"], timeout=timeout, max_bytes=max_bytes)
        data = response["data"]
        sha256 = hashlib.sha256(data).hexdigest()
        suffix = extension_for(response["content_type"], response["final_url"], data)
        relative_path = Path("raw") / source_id / f"{sha256[:20]}{suffix}"
        absolute_path = archive_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        if not absolute_path.exists():
            absolute_path.write_bytes(data)

        if suffix == ".pdf":
            text, extracted_title, used_charset, page_count, method = extract_pdf(data)
        elif suffix in {".html", ".htm"}:
            text, extracted_title, used_charset, page_count = extract_html(
                data, response["charset"]
            )
            method = "html_parser"
        elif suffix == ".json":
            decoded, used_charset = decode_bytes(data, response["charset"])
            try:
                text = json.dumps(json.loads(decoded), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                text = decoded
            extracted_title, page_count, method = "", 0, "json"
            text = clean_text(text)
        elif response["content_type"].startswith("text/") or suffix in {".txt", ".xml"}:
            decoded, used_charset = decode_bytes(data, response["charset"])
            text, extracted_title, page_count, method = clean_text(decoded), "", 0, "plain_text"
        else:
            text, extracted_title, used_charset, page_count, method = "", "", "binary", 0, "binary_metadata"

        conn.execute(
            "UPDATE source_snapshots SET is_current = 0 WHERE source_id = ?",
            (source_id,),
        )
        cursor = conn.execute(
            """
            INSERT INTO source_snapshots (
                run_id, source_id, fetched_at, final_url, http_status,
                content_type, charset, etag, last_modified, sha256, byte_size,
                local_path, status, error, is_current
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', 1)
            """,
            (
                run_id, source_id, fetched_at, response["final_url"],
                response["http_status"], response["content_type"], used_charset,
                response["etag"], response["last_modified"], sha256, len(data),
                relative_path.as_posix(), "ok",
            ),
        )
        snapshot_id = cursor.lastrowid
        document_id = None
        chunk_count = 0
        if text:
            document_cursor = conn.execute(
                """
                INSERT INTO source_documents (
                    snapshot_id, source_id, title, language, extraction_method,
                    page_count, text_content, text_length, word_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot_id, source_id,
                    extracted_title or source["title_en"] or source["title_zh"],
                    detect_language(text), method, page_count, text, len(text),
                    len(re.findall(r"\S+", text)),
                ),
            )
            document_id = document_cursor.lastrowid
            for index, (start, end, value) in enumerate(chunk_text(text)):
                chunk_cursor = conn.execute(
                    """
                    INSERT INTO source_archive_chunks (
                        document_id, source_id, chunk_index, title, text,
                        char_start, char_end, token_estimate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id, source_id, index,
                        extracted_title or source["title_en"] or source["title_zh"],
                        value, start, end, max(1, len(value) // 4),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO source_archive_fts (
                        rowid, text, title, source_id, document_id
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_cursor.lastrowid, value,
                        extracted_title or source["title_en"] or source["title_zh"],
                        source_id, document_id,
                    ),
                )
                chunk_count += 1
        conn.commit()
        return {
            "status": "ok",
            "bytes": len(data),
            "text_length": len(text),
            "chunks": chunk_count,
            "pages": page_count,
            "method": method,
            "metadata_only": False,
            "local_path": relative_path.as_posix(),
        }
    except Exception as exc:
        conn.execute(
            """
            INSERT INTO source_snapshots (
                run_id, source_id, fetched_at, final_url, http_status,
                content_type, charset, etag, last_modified, sha256, byte_size,
                local_path, status, error, is_current
            ) VALUES (?, ?, ?, ?, NULL, '', '', '', '', '', 0, '', 'error', ?, 0)
            """,
            (run_id, source_id, fetched_at, source["url"], str(exc)[:2000]),
        )
        conn.commit()
        return {"status": "error", "error": str(exc)}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Download registered Throttle Atlas sources into the local SQLite archive."
    )
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--archive-dir", type=Path, default=ARCHIVE_DIR)
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--kind", action="append", default=[])
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry only sources that failed in the most recent completed run.",
    )
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=int, default=35)
    parser.add_argument("--max-bytes", type=int, default=80 * 1024 * 1024)
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 2
    args.archive_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    ensure_archive_schema(conn)
    recover_incomplete_runs(conn)

    clauses: list[str] = []
    params: list[str] = []
    if args.source_id:
        placeholders = ",".join("?" for _ in args.source_id)
        clauses.append(f"id IN ({placeholders})")
        params.extend(args.source_id)
    if args.kind:
        placeholders = ",".join("?" for _ in args.kind)
        clauses.append(f"kind IN ({placeholders})")
        params.extend(args.kind)
    if args.retry_failed:
        clauses.append(
            "id NOT IN (SELECT source_id FROM source_snapshots "
            "WHERE is_current = 1 AND status = 'ok')"
        )
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM sources {where} ORDER BY kind, organization, id"
    if args.limit > 0:
        sql += f" LIMIT {int(args.limit)}"
    sources = conn.execute(sql, params).fetchall()

    run_id = f"{datetime.now().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"
    started_at = utc_now()
    conn.execute(
        """
        INSERT INTO source_archive_runs (
            id, started_at, status, total_sources
        ) VALUES (?, ?, 'running', ?)
        """,
        (run_id, started_at, len(sources)),
    )
    conn.commit()

    succeeded = failed = metadata_only = bytes_downloaded = 0
    print(f"Archive run {run_id}: {len(sources)} sources", flush=True)
    for index, source in enumerate(sources, start=1):
        prefix = f"[{index:02d}/{len(sources):02d}] {source['id']}"
        print(f"{prefix} ...", flush=True)
        result = archive_source(
            conn, run_id, source, args.archive_dir, args.timeout, args.max_bytes
        )
        if result["status"] == "ok":
            succeeded += 1
            bytes_downloaded += result["bytes"]
            metadata_only += int(result.get("metadata_only", False))
            if result.get("metadata_only"):
                print(
                    f"{prefix} METADATA_ONLY (URL registered, content not downloaded)",
                    flush=True,
                )
            else:
                print(
                    f"{prefix} OK {result['bytes']} bytes | "
                    f"{result['text_length']} chars | {result['chunks']} chunks | "
                    f"{result['method']}",
                    flush=True,
                )
        else:
            failed += 1
            print(f"{prefix} ERROR {result['error']}", flush=True)

    status = "complete" if failed == 0 else "partial"
    conn.execute(
        """
        UPDATE source_archive_runs
        SET finished_at = ?, status = ?, succeeded = ?, failed = ?,
            metadata_only = ?, bytes_downloaded = ?
        WHERE id = ?
        """,
        (
            utc_now(), status, succeeded, failed, metadata_only,
            bytes_downloaded, run_id,
        ),
    )
    conn.commit()
    summary = {
        "run_id": run_id,
        "status": status,
        "total": len(sources),
        "succeeded": succeeded,
        "failed": failed,
        "metadata_only": metadata_only,
        "bytes_downloaded": bytes_downloaded,
    }
    (args.archive_dir / "latest_run.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    conn.close()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
