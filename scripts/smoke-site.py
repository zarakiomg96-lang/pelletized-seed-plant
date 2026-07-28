#!/usr/bin/env python3
"""
scripts/smoke-site.py — Runtime proof that the static site serves what its
sitemap claims and what its pages link to.

Drift categories caught:
    * declared-not-served   : sitemap <loc> points at a path the probe cannot
                              fetch (4xx / 5xx / network error). Indicates a
                              file removed or renamed without sitemap update.
    * served-but-unlisted   : an HTML file on disk is referenced via href or
                              src from any other HTML but the sitemap does NOT
                              declare it. Crawlers will not find it.

Workflow:
    1. Pick a free TCP port (preferring 4321, falling back 4322-4330 if a
       stale http.server from a manual session still owns 4321).
    2. Bind 127.0.0.1:<port> in a daemon thread, serving the project root.
    3. Parse sitemap.xml with xml.etree — catches malformed XML and the
       wrong-namespace trap.
    4. Rewrite each <loc> from its placeholder host to localhost:<port> and
       HTTP-probe each one with urllib (built-in, no curl dep).
    5. Grep every HTML for href / src references; resolve them against each
       HTML's own directory so ../assets/... is normalised correctly.
    6. Diff (sitemap paths)  vs  (linked HTML paths) vs (files on disk).
    7. Shutdown the server and emit a human summary, or a JSON document
       when --json is passed.

Usage:
    python scripts/smoke-site.py             # default human output
    python scripts/smoke-site.py --json      # machine-readable

Exit codes:
    0 — zero drift (sitemap matches reality)
    1 — at least one drift item
    2 — runtime error (sitemap missing, bind failed, parse error)
"""

from __future__ import annotations

import argparse
import glob
import http.server
import json
import os
import re
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
PROBE_HOST = "127.0.0.1"
PORT_CANDIDATES = (4321, 4322, 4323, 4324, 4325, 4326, 4327, 4328, 4329, 4330)
SERVER_BOOT_SLEEP_S = 0.6
PROBE_TIMEOUT_S = 5

# Local URL attribute pairs we care about when grepping HTML.
LINK_TAG_ATTR = (
    ("a", "href"),
    ("link", "href"),
    ("script", "src"),
    ("img", "src"),
    ("source", "src"),
    ("iframe", "src"),
    ("video", "src"),
    ("video", "poster"),
    ("track", "src"),
    ("embed", "src"),
    ("area", "href"),
)


# Subclass that lets the smoke probe rebind its port immediately even if a
# previous helper process' socket is still in TIME_WAIT after a hard kill
# (Windows holds these for 30-60s; without this the candidate list drains).
class _ReuseAddrServer(socketserver.TCPServer):
    allow_reuse_address = True


# ---------------------------------------------------------------------------
# Path & IO helpers
# ---------------------------------------------------------------------------

def to_posix(p: str) -> str:
    return p.replace("\\", "/")


def read(path: str) -> str:
    return open(path, encoding="utf-8").read()


def url_to_local_path(url: str) -> str:
    """Strip host/scheme from a sitemap <loc> and return its filesystem path.
    A trailing slash means "directory, serve index.html". Handles both
    root-hosted (example.com/foo.html) and subpath-hosted
    (user.github.io/repo/foo.html) URLs by stripping segment by segment
    until the remainder matches a project path."""
    path = urllib.parse.urlparse(url).path or "/"
    path = urllib.parse.unquote(path)
    if path in ("/", ""):
        return "index.html"
    if path.endswith("/"):
        path += "index.html"
    # Strip leading segments until the remainder is a valid project path.
    # Handles GitHub Pages subpath: user.github.io/repo/procesos/foo.html
    segments = path.strip("/").split("/")
    for i in range(len(segments)):
        candidate = "/".join(segments[i:])
        if candidate.startswith(("procesos/", "en/", "assets/", "docs/", "scripts/", ".github/")):
            return candidate
        if candidate in ("index.html", "404.html", "robots.txt", "sitemap.xml"):
            return candidate
        # Check if file or directory exists at this path
        if os.path.isfile(candidate) or os.path.isdir(candidate):
            return candidate
    # Fallback: strip everything up to first known project marker, or
    # just return the full relative path.
    for i, seg in enumerate(segments):
        if seg in ("procesos", "en", "assets", "docs", "scripts"):
            return "/".join(segments[i:])
    return path.lstrip("/")


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def serve_in_background(directory: str, port_candidates: tuple[int, ...]) -> tuple[threading.Thread, socketserver.TCPServer, int]:
    """Bind 127.0.0.1:<port> serving `directory`. Bind BEFORE the thread so
    smoke probes see a stable listener. Tries each candidate until one binds
    successfully; raises OSError if every candidate is in use."""
    last_exc: OSError | None = None
    for port in port_candidates:
        try:
            handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(
                *a, directory=directory, **kw
            )
            httpd = _ReuseAddrServer(
                (PROBE_HOST, port), handler, bind_and_activate=True
            )
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            time.sleep(SERVER_BOOT_SLEEP_S)
            return thread, httpd, port
        except OSError as exc:
            last_exc = exc
            continue
    raise last_exc or OSError("no candidate port could bind")


# ---------------------------------------------------------------------------
# Probe primitives
# ---------------------------------------------------------------------------

def fetch_status(url: str) -> int:
    try:
        with urllib.request.urlopen(url, timeout=PROBE_TIMEOUT_S) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def parse_sitemap_urls(path: str) -> list[str]:
    tree = ET.parse(path)
    return [u.text for u in tree.findall(f".//{SM_NS}loc") if u.text]


def _base_href_path(text: str) -> str | None:
    """Return the path part of <base href> if present, or None."""
    m = re.search(r'<base\s+href="([^"]+)"', text, re.IGNORECASE)
    if not m:
        return None
    href = m.group(1).strip()
    # Strip scheme+host if present
    parsed = urllib.parse.urlparse(href)
    path = parsed.path or "/"
    return path


def linked_local_paths(html_files: list[str]) -> set[str]:
    """Grep every HTML for href / src attributes on tag names of interest.
    Resolve each target against the HTML's own dir so ../assets/... ends up
    in the right place. Skip fragments, mailto, external schemes."""
    tag_names = "|".join(re.escape(t) for t, _ in LINK_TAG_ATTR)
    rx = re.compile(
        rf"<({tag_names})\b[^>]*?(?:href|src|poster)\s*=\s*(['\"])([^'\"]+)\2",
        re.IGNORECASE,
    )
    linked: set[str] = set()
    for f in html_files:
        try:
            text = read(f)
        except Exception:
            continue
        base_dir = os.path.dirname(f)
        base_href_path = _base_href_path(text)
        for m in rx.finditer(text):
            target = m.group(3).strip()
            if not target:
                continue
            if target.startswith((
                "http://", "https://", "//", "#",
                "mailto:", "javascript:", "tel:", "data:",
            )):
                continue
            target = target.split("?", 1)[0].split("#", 1)[0]
            if not target:
                continue
            # Resolve against <base href> (if present) or the file's dir.
            # Strip the base path prefix so linked paths match sitemap paths.
            if base_href_path is not None:
                # Resolve relative target against the base href path.
                resolved = urllib.parse.urljoin(base_href_path, target)
                resolved_path = urllib.parse.urlparse(resolved).path
                resolved_path = urllib.parse.unquote(resolved_path)
                # Strip the base href prefix itself
                if resolved_path.startswith(base_href_path):
                    joined = resolved_path[len(base_href_path):]
                else:
                    joined = resolved_path.lstrip("/")
            else:
                joined = (
                    os.path.normpath(os.path.join(base_dir, target))
                    if base_dir else os.path.normpath(target)
                )
                joined = re.sub(r"^[a-zA-Z]:[\\/]", "", joined)
                joined = to_posix(joined).lstrip("/")
            joined = joined.lstrip("/")
            linked.add(joined)
    return linked


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    os.chdir(ROOT)

    declared_not_served: list[tuple[str, int]] = []
    served_but_unlisted: list[str] = []
    chosen_port: int | None = None
    httpd: socketserver.TCPServer | None = None

    try:
        # 1. Bring up an HTTP server in the project root.
        try:
            _, httpd, chosen_port = serve_in_background(
                ROOT, PORT_CANDIDATES
            )
        except OSError as exc:
            return _emit(args, OK=2, payload={
                "error": f"could not bind any of {PORT_CANDIDATES}: {exc}",
                "declared_not_served": [],
                "served_but_unlisted": [],
            })

        probe_base = f"http://{PROBE_HOST}:{chosen_port}"

        # 2. Parse sitemap.
        if not os.path.isfile("sitemap.xml"):
            return _emit(args, OK=2, payload={
                "error": "sitemap.xml not found in project root",
                "declared_not_served": [],
                "served_but_unlisted": [],
            })
        try:
            sitemap_urls = parse_sitemap_urls("sitemap.xml")
        except ET.ParseError as exc:
            return _emit(args, OK=2, payload={
                "error": f"sitemap.xml is malformed XML: {exc}",
                "declared_not_served": [],
                "served_but_unlisted": [],
            })

        # 3. Probe each sitemap URL.
        sitemap_paths = sorted({
            p for p in (url_to_local_path(u) for u in sitemap_urls) if p
        })
        for url in sitemap_urls:
            local = url_to_local_path(url)
            probe_url = f"{probe_base}/{local}"
            status = fetch_status(probe_url)
            if status != 200:
                declared_not_served.append((probe_url, status))

        # 4. Find HTML files referenced from any other HTML.
        html_files = sorted(glob.glob("**/*.html", recursive=True))
        linked = linked_local_paths(html_files)
        linked_html = {
            p for p in linked
            if p.endswith(".html") and p != "404.html"
        }
        sitemap_html = {
            p for p in sitemap_paths
            if p.endswith(".html") or p == "index.html"
        }
        served_but_unlisted = sorted(linked_html - sitemap_html)

    finally:
        if httpd is not None:
            try:
                httpd.shutdown()
                httpd.server_close()
            except Exception:
                pass

    return _emit(args,
        OK=1 if (declared_not_served or served_but_unlisted) else 0,
        port=chosen_port,
        payload={
            "sitemap_urls_count": len(sitemap_paths),
            "declared_not_served": [
                {"url": u, "status": s} for u, s in declared_not_served
            ],
            "served_but_unlisted": served_but_unlisted,
        },
    )


def _emit(args: argparse.Namespace, *, OK: int, payload: dict, port: int | None = None) -> int:
    drift = bool(payload.get("declared_not_served") or payload.get("served_but_unlisted"))
    payload = {
        **({"port": port} if port is not None else {}),
        **({"error": payload.pop("error")} if "error" in payload else {}),
        "pass": 0 if drift else 1,
        "fail": 1 if drift else 0,
        **payload,
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if "error" in payload:
            print(f"[smoke-site] RUNTIME ERROR — {payload['error']}", file=sys.stderr)
            return OK
        if not drift:
            print(
                f"[smoke-site] PASS — sitemap matches reality on port {port} "
                f"({payload['sitemap_urls_count']} URLs served, "
                f"0 broken, 0 unlinked HTML pages)"
            )
            return OK
        print(
            f"[smoke-site] FAIL — drift detected on port {port} "
            f"({len(payload['declared_not_served'])} broken, "
            f"{len(payload['served_but_unlisted'])} unlinked)",
            file=sys.stderr,
        )
        if payload["declared_not_served"]:
            print("  declared-not-served:", file=sys.stderr)
            for item in payload["declared_not_served"]:
                print(f"    [{item['status']}] {item['url']}", file=sys.stderr)
        if payload["served_but_unlisted"]:
            print("  served-but-unlisted:", file=sys.stderr)
            for p in payload["served_but_unlisted"]:
                print(f"    {p}", file=sys.stderr)
    return OK


if __name__ == "__main__":
    sys.exit(main())
