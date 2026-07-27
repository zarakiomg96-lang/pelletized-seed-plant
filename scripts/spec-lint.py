#!/usr/bin/env python3
"""
spec-lint.py — Runs SPEC.md §10 checklist in one pass.

Implements the validation contract defined in §15.3:
- Exact attribute regex (no loose substring matching for CSS classes).
- Real XML namespace parsing for sitemaps.
- Explicit PASS / FAIL per check, exit code != 0 on any FAIL.

Usage:
    python spec-lint.py
    python spec-lint.py --json          # machine-readable output

Returns:
    exit 0  → all checks PASS
    exit 1  → at least one FAIL

Reference:
    SPEC.md  — Plant Specification (default: ./SPEC.md)
"""

from __future__ import annotations

import argparse
import glob
import gzip
import io
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from contextlib import contextmanager

# Force UTF-8 on stdout/stderr (Windows cp1252 cannot encode ↔ etc).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ----------------------------------------------------------------------------
# Constants from SPEC §10
# ----------------------------------------------------------------------------

SM_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"

EXPECTED_SITEMAP_URLS = 16
EXPECTED_TOTAL_HTML = 17  # 2 homes + 7 process ES + 7 process EN + 404
HOMES = ["index.html", "en/index.html"]
N_HOME_TIMELINE = 7
N_HOME_ACCENT = 2

# Byte budget targets (§15.3.1 item 15 / group #15). Calibrated against
# site weight at v2.1: current unc ~215 KB, current gzip ~82 KB. Targets
# give 15-25% headroom so meta-tag / description / asset growth triggers
# the gate before publish-time regressions.
#
# Note: the per-section caps (HTML, assets) are **advisory** — they
# identify WHICH dimension is bloating when total trips. The total cap
# (250 KB unc / 90 KB gz) is the **binding** constraint for merges.
# Per-section caps are deliberately < total each so the per-section
# invariant fails first if one dimension is consuming disproportionate
# of the budget.
BUDGET_HTML_KB_UNC = 175.0    # current: ~154 KB
BUDGET_HTML_KB_GZ = 55.0      # current:  ~46 KB
BUDGET_ASSETS_KB_UNC = 110.0  # current:  ~61 KB
BUDGET_ASSETS_KB_GZ = 60.0    # current:  ~37 KB
BUDGET_TOTAL_KB_UNC = 250.0   # current: ~215 KB (user-stated 250 KB target)
BUDGET_TOTAL_KB_GZ = 90.0     # current:  ~82 KB (user-stated  90 KB target)

# Keys the byte budget gate treats as a precondition for running the
# per-section (assets-related) invariants. If any of these are missing,
# the gate fails with a clear message rather than emitting silent zeros.
EXPECTED_KEY_ASSETS = [
    "assets/css/styles.css",
    "assets/js/app.js",
    "assets/img/favicon.svg",
    "assets/img/og-image.png",
]

# Asset extensions considered user-facing bytes. Anything else (build
# artefacts, hidden files, sourcemaps) is excluded from the budget so
# it doesn't quietly consume target budget headroom.
ASSET_EXTENSIONS = (
    ".css", ".js", ".svg", ".png", ".jpg", ".jpeg",
    ".webp", ".ico", ".woff", ".woff2", ".ttf", ".otf",
    ".mp4", ".webm", ".txt", ".json", ".xml",
)

# ES / EN process-page slug pairing (from SPEC §3)
PROCESS_PAIRS: dict[str, str] = {
    "recepcion": "reception",
    "pre-limpieza": "pre-cleaning",
    "limpieza-fina": "fine-cleaning",
    "peletizacion": "pelleting",
    "envasado": "packaging",
    "control-calidad": "quality-control",
    "almacen-producto-terminado": "finished-product-warehouse",
}

# BUG-001 grep anchor: \b0?\d{1,2}\s*/\s*08\b
BUG_001_RE = re.compile(r"\b0?\d{1,2}\s*/\s*08\b")

# §4 glossary equivalent-term pairs used by check_content_drift (group 13).
# Each tuple is (ES regex word-bounded, EN regex word-bounded, label). The check
# verifies that, for each ES↔EN process pair, at least one label is detected on
# both sides of the pair to guard against drift.
#
# Patterns are intentionally permissive on inflection:
#   \bsellad?[oa]s?\b covers "sello / sella / sellado / sellada / sellados / selladas"
#   \bcalibr(?:ad[oa]|ación|ar)\b covers "calibrado / calibrada / calibración / calibrar"
#   \balmac[ée]n(?:es|ado|ados|aje|amiento|amientos)?\b narrowed (v1.7)
#       then widened (v1.7.1) so it does NOT overlap the role label and
#       still covers plural participle ("almacenados") and abstract plural
#       ("almacenamientos").
#   role labels accept Spanish and English plurals (v1.7).
TERM_PAIRS: list[tuple[str, str, str]] = [
    (r"\blotes?\b", r"\blots?\b", "lot/lots"),
    (r"\bpol[íi]meros?\b", r"\bpolymers?\b", "polymer"),
    (r"\bfungicidas?\b", r"\bfungicides?\b", "fungicide"),
    (r"\btrazabilidad\b", r"\btraceability\b", "traceability"),
    (r"\bbidireccional\b", r"\bbidirectional\b", "bidirectional"),
    (r"\bcalibr(?:ad[oa]|ación|ar)\b", r"\bcalibrat(?:ion|ing|e)\b", "calibration"),
    (r"\brecubrimientos?\b", r"\bcoatings?\b", "coating"),
    (r"\bbombos?\b", r"\bdrums?\b", "drum"),
    (r"\bturbinas?\b", r"\bturbines?\b", "turbine"),
    (r"\bsecado\b", r"\bdrying\b", "drying"),
    # Narrowed in v1.7: finite suffix list so "almacenero" no longer triggers
    # this warehouse label (it triggers the role label below instead).
    (r"\balmac[ée]n(?:es|ado|ados|aje|amiento|amientos)?\b", r"\bwarehouse\b", "warehouse"),
    (r"\bcalidad\b", r"\bquality\b", "quality"),
    (r"\bcertificad[oa]s?\b", r"\bcertified\b", "certified"),
    (r"\bsellad?[oa]s?\b", r"\bseal(?:ing|ed)?\b", "seal"),
    (r"\betiquetas?\b", r"\blabel(?:ing|led|s)?\b", "label"),
    (r"\bproveedores?\b", r"\bsuppliers?\b", "supplier"),
    (r"\bsemillas?\b", r"\bseeds?\b", "seed"),
    (r"\blimpiezas?\b", r"\bcleaning\b", "cleaning"),
    (r"\bgermin(?:aci[óo]n|ar)\b", r"\bgermin(?:ation|ating|ate)\b", "germination"),
    (r"\bimpurezas?\b", r"\bimpurit(?:y|ies)\b", "impurity"),
    (r"\bgraf(?:o|os)\b", r"\bgraph(?:s)?\b", "graph"),
    (r"\brotatori[ao]s?\b", r"\brotating\b", "rotating"),
    # Round 2 of §4 coverage (v1.6): roles, process concepts, materials.
    # Plurals accepted in v1.7.
    (r"\bpeletizaci[óo]n\b", r"\bpelleting\b", "peletización/pelleting"),
    (r"\barcillas?\s+inertes?\b", r"\binert\s+clays?\b", "arcilla inerte/inert clay"),
    (r"\balmaceneros?\b", r"\bwarehouse\s+operators?\b", "almacenero/warehouse operator"),
    (r"\boperarios?\s+de\s+planta\b", r"\bfloor\s+operators?\b", "operario/floor operator"),
    (r"\bespecialistas?\s+de\s+laboratorio\b",
     r"\blab(?:oratory)?\s+specialists?\b", "especialista/lab specialist"),
    (r"\bnodo\s+de\s+decisi[óo]n\b", r"\bdecision\s+node\b", "nodo de decisión/decision node"),
    (r"\bproceso\s+hero\b", r"\bhero\s+process\b", "proceso hero/hero process"),
]

# CJK Unicode ranges
CJK_RE = re.compile(r"[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7AF]")

# Common placeholder strings — anchored with word boundaries so Spanish "todo"
# doesn't false-positive on real content.
PLACEHOLDER_PATTERNS = (
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bXXX\b"),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
)

# ---------------------------------------------------------------------------
# Result helpers
# ---------------------------------------------------------------------------

results: list[tuple[str, str, str]] = []


def record(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    results.append((name, status, detail))


# ---------------------------------------------------------------------------
# Locator
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else os.getcwd()


def to_posix(p: str) -> str:
    """Normalize a path to forward-slash separators so Windows glob output is
    comparable to the forward-slash constants in this script."""
    return p.replace("\\", "/")


def read(path: str) -> str:
    return open(path, encoding="utf-8").read()


def all_html() -> list[str]:
    return sorted(glob.glob("**/*.html", recursive=True))


# ---------------------------------------------------------------------------
# 1. Sitemap
# ---------------------------------------------------------------------------

def check_sitemap() -> None:
    print("\n=== 1. sitemap.xml ===")
    try:
        tree = ET.parse("sitemap.xml")
    except Exception as exc:
        record("Sitemap parses as XML", False, f"exception: {exc}")
        return
    urls = [u.text for u in tree.findall(f".//{SM_NS}loc") if u.text]
    record("Sitemap parses as XML", True, f"{len(urls)} <loc> entries")
    record(
        f"Sitemap has exactly {EXPECTED_SITEMAP_URLS} URLs",
        len(urls) == EXPECTED_SITEMAP_URLS,
        f"got {len(urls)}",
    )
    has_es_home = any(u.endswith("/") or u.endswith("/index.html") for u in urls)
    has_en_home = any(u.endswith("/en/") or u.endswith("/en/index.html") for u in urls)
    record("Sitemap contains ES home", has_es_home)
    record("Sitemap contains EN home (/en/)", has_en_home)
    # Every URL ends in .html or in / (legacy)
    bad_urls = [u for u in urls if not (u.endswith(".html") or u.endswith("/"))]
    record("All sitemap URLs end with .html or /", not bad_urls, f"offenders: {bad_urls}")


# ---------------------------------------------------------------------------
# 2. HTML inventory
# ---------------------------------------------------------------------------

def check_inventory() -> None:
    print("\n=== 2. HTML inventory ===")
    EXPECTED_FILES = sorted(
        set(HOMES)
        | {"404.html"}
        | {f"procesos/{s}.html" for s in PROCESS_PAIRS}
        | {f"procesos/en/{s}.html" for s in PROCESS_PAIRS.values()}
    )
    htmls = sorted(to_posix(p) for p in all_html())
    record(
        f"{EXPECTED_TOTAL_HTML} HTML files present",
        len(htmls) == EXPECTED_TOTAL_HTML,
        f"got {len(htmls)} ({htmls})",
    )
    missing = sorted(set(EXPECTED_FILES) - set(htmls))
    extra = sorted(set(htmls) - set(EXPECTED_FILES))
    record("All expected HTML files are present", not missing, f"missing: {missing}")
    record("No unexpected HTML files", not extra, f"extra: {extra}")


# ---------------------------------------------------------------------------
# 3. BUG-001 stale /08 grep
# ---------------------------------------------------------------------------

def check_bug_001() -> None:
    print("\n=== 3. BUG-001 stale /08 grep ===")
    hits: list[str] = []
    files = all_html() + ["SPEC.md", "README.md", "sitemap.xml", "robots.txt"]
    for f in files:
        if not os.path.isfile(f):
            continue
        try:
            text = read(f)
        except Exception:
            continue
        for m in BUG_001_RE.finditer(text):
            start = max(0, m.start() - 25)
            end = min(len(text), m.end() + 25)
            hits.append(f"{f}: ...{text[start:end].replace(chr(10), ' ')}...")
    record(
        "No stale NN/08 references anywhere",
        not hits,
        f"{len(hits)} hits" if hits else "0",
    )


# ---------------------------------------------------------------------------
# 4. CJK + placeholders
# ---------------------------------------------------------------------------

def check_text_purity() -> None:
    print("\n=== 4. CJK + placeholder strings ===")
    cjk: list[str] = []
    placeholders: list[str] = []
    for f in all_html():
        try:
            text = read(f)
        except Exception:
            continue
        if CJK_RE.search(text):
            cjk.append(f)
        for pat in PLACEHOLDER_PATTERNS:
            m = pat.search(text)
            if m is not None:
                start = max(0, m.start() - 25)
                end = min(len(text), m.end() + 25)
                placeholders.append(
                    f"{f}: ...{text[start:end].replace(chr(10), ' ')}..."
                )
    record("No CJK characters in HTML", not cjk, str(cjk))
    record(
        "No Lorem/TODO/XXX placeholders (word-anchored)",
        not placeholders,
        str(placeholders) if placeholders else "0",
    )


# ---------------------------------------------------------------------------
# 5. Per-page meta
# ---------------------------------------------------------------------------

def check_per_page_meta() -> None:
    print("\n=== 5. Per-page meta ===")
    for f in all_html():
        try:
            text = read(f)
        except Exception:
            continue
        # <title>
        m_title = re.search(r"<title>([^<]+)</title>", text)
        record(f"{f}: <title> present", m_title is not None)
        # <meta name="description">
        m_desc = re.search(
            r'<meta\s+name="description"\s+content="([^"]+)"', text
        )
        if m_desc is not None:
            desc = m_desc.group(1)
            record(
                f"{f}: description >= 120 chars",
                len(desc) >= 120,
                f"len={len(desc)}",
            )
        else:
            record(f"{f}: <meta name=description> present", False)
        # canonical
        record(f"{f}: <link rel=canonical>", 'rel="canonical"' in text)
        # hreflang (404.html may differ per SPEC §9.3 exemption)
        if f != "404.html":
            record(f"{f}: hreflang=es", 'hreflang="es"' in text)
            record(f"{f}: hreflang=en", 'hreflang="en"' in text)
        # Single h1
        h1 = re.findall(r"<h1\b", text)
        record(f"{f}: exactly 1 <h1>", len(h1) == 1, f"got {len(h1)}")
        # <html lang>
        m_lang = re.search(r'<html\s+lang="([^"]+)"', text)
        f_posix = to_posix(f)
        # Match either "en/foo" or ".../en/foo" or ".../en/" as a path
        # segment; "en/index.html" must also match (no leading slash).
        path_parts = [p for p in f_posix.split("/") if p]
        expected_lang = "en" if (path_parts and path_parts[0] == "en") or "en" in path_parts else "es"
        if f == "404.html":
            # 404 is bilingual; lang tag may be either, but it must exist.
            record(f"{f}: <html lang>", m_lang is not None)
        else:
            record(
                f"{f}: <html lang> matches content",
                m_lang is not None and m_lang.group(1) == expected_lang,
                f"expected={expected_lang} got={m_lang.group(1) if m_lang else None}",
            )


# ---------------------------------------------------------------------------
# 6. Homes: 7 timeline cards, 2 --accent
# ---------------------------------------------------------------------------

def check_homes_timeline() -> None:
    print("\n=== 6. Homes timeline (7 cards, 2 --accent each) ===")
    for f in HOMES:
        try:
            text = read(f)
        except Exception as exc:
            record(f"{f}: readable", False, str(exc))
            continue
        # Exact attribute matches per §15.3
        main = len(re.findall(r'class="timeline__item\b"', text))
        accent = len(re.findall(
            r'class="timeline__item timeline__item--accent"', text))
        total = main + accent
        record(
            f"{f}: {N_HOME_TIMELINE} timeline cards total",
            total == N_HOME_TIMELINE,
            f"main={main} accent={accent} total={total}",
        )
        record(
            f"{f}: {N_HOME_ACCENT} accent cards (procesos 04, 06)",
            accent == N_HOME_ACCENT,
            f"accent={accent}",
        )


# ---------------------------------------------------------------------------
# 7. Homes: structural DOM identity (counter-based)
# ---------------------------------------------------------------------------

def count_in_section(text: str, css_class: str) -> int:
    """Count how many class= attributes contain the given CSS class as a
    whole token (word-bounded)."""
    cls = re.escape(css_class)
    return len(re.findall(rf'class="[^"]*\b{cls}\b[^"]*"', text))


def check_homes_structural_identity() -> None:
    print("\n=== 7. Homes structural DOM identity ES↔EN ===")
    targets = [".section", ".section--soft", ".stats", ".stat", ".badges", ".badge",
               ".mission-block", ".split", ".hero", ".video-frame"]
    es_text = read("index.html")
    en_text = read("en/index.html")
    for cls in targets:
        es = count_in_section(es_text, cls)
        en = count_in_section(en_text, cls)
        record(
            f"Homes have equal '{cls}' count",
            es == en,
            f"ES={es} EN={en}",
        )


# ---------------------------------------------------------------------------
# 8. Process pages: eyebrows, next-step, structural identity
# ---------------------------------------------------------------------------

def check_process_pages() -> None:
    print("\n=== 8. Process pages ===")
    for es_slug, en_slug in PROCESS_PAIRS.items():
        es_path = f"procesos/{es_slug}.html"
        en_path = f"procesos/en/{en_slug}.html"
        if not (os.path.isfile(es_path) and os.path.isfile(en_path)):
            record(f"{es_slug}: pair present", False, "missing")
            continue
        es = read(es_path)
        en = read(en_path)
        # eyebrow
        m_es = re.search(r'class="eyebrow"[^>]*>Proceso\s+(\d{2})\s*/\s*07', es)
        m_en = re.search(r'class="eyebrow"[^>]*>Process\s+(\d{2})\s*/\s*07', en)
        record(f"{es_path}: eyebrow 'Proceso NN / 07'", m_es is not None)
        record(f"{en_path}: eyebrow 'Process NN / 07'", m_en is not None)
        if m_es and m_en:
            record(
                f"{es_path}/{en_path}: eyebrows agree on process number",
                m_es.group(1) == m_en.group(1),
                f"ES={m_es.group(1)} EN={m_en.group(1)}",
            )
        # next-step (last process has no next-step)
        if es_slug != "almacen-producto-terminado":
            m_next_es = re.search(
                r'<a\s+class="next-step"[^>]*href="([^"]+)"', es, re.DOTALL)
            m_next_en = re.search(
                r'<a\s+class="next-step"[^>]*href="([^"]+)"', en, re.DOTALL)
            record(f"{es_path}: next-step present", m_next_es is not None)
            record(f"{en_path}: next-step present", m_next_en is not None)
        # structural identity (.depth-block count, .io-grid count, telemetry rows)
        es_depth = count_in_section(es, ".depth-block")
        en_depth = count_in_section(en, ".depth-block")
        es_io = count_in_section(es, ".io-grid")
        en_io = count_in_section(en, ".io-grid")
        es_telemetry_rows = len(re.findall(r"<tr\b", es))
        en_telemetry_rows = len(re.findall(r"<tr\b", en))
        record(
            f"{es_slug} pair: .depth-block count equal",
            es_depth == en_depth,
            f"ES={es_depth} EN={en_depth}",
        )
        record(
            f"{es_slug} pair: .io-grid count equal",
            es_io == en_io,
            f"ES={es_io} EN={en_io}",
        )
        record(
            f"{es_slug} pair: <tr> count equal",
            es_telemetry_rows == en_telemetry_rows,
            f"ES={es_telemetry_rows} EN={en_telemetry_rows}",
        )


# ---------------------------------------------------------------------------
# 9. JSON-LD in homes
# ---------------------------------------------------------------------------

def check_jsonld() -> None:
    print("\n=== 9. JSON-LD in homes ===")
    jsonld_pat = re.compile(
        r'<script\s+type="application/ld\+json">([\s\S]+?)</script>'
    )
    for f in HOMES:
        text = read(f)
        blocks = jsonld_pat.findall(text)
        record(f"{f}: JSON-LD <script> present", len(blocks) >= 1,
               f"found {len(blocks)}")
        for i, raw in enumerate(blocks):
            try:
                data = json.loads(raw)
                record(f"{f} JSON-LD[{i}]: parses as JSON", True)
                record(
                    f"{f} JSON-LD[{i}]: @context=schema.org",
                    isinstance(data, dict)
                    and data.get("@context") == "https://schema.org",
                )
            except Exception as exc:
                record(f"{f} JSON-LD[{i}]: parses as JSON", False, str(exc))


# ---------------------------------------------------------------------------
# 10. CSS design tokens
# ---------------------------------------------------------------------------

def check_design_tokens() -> None:
    print("\n=== 10. CSS design tokens ===")
    css = read("assets/css/styles.css")
    for token in ("--cream", "--ink", "--ink-soft", "--tobacco-700", "--seed"):
        has_def = re.search(rf"{re.escape(token)}\s*:", css) is not None
        record(f"Token {token} defined", has_def)
    # specific: prefers-reduced-motion handling in CSS or JS
    # Accept both @media (prefers-reduced-motion: reduce) and
    # @media (prefers-reduced-motion: no-preference); both gate reveal behavior.
    has_reduced = re.search(
        r"@media\s*\([^)]*prefers-reduced-motion[^)]*\)", css
    ) is not None
    record("prefers-reduced-motion media query present", has_reduced)
    # focus-visible
    record(":focus-visible style present", ":focus-visible" in css)


# ---------------------------------------------------------------------------
# 11. JS: aria-current + lang toggle
# ---------------------------------------------------------------------------

def check_app_js() -> None:
    print("\n=== 11. app.js ===")
    js = read("assets/js/app.js")
    record("aria-current assignment present", "aria-current" in js)
    record("lang path detection (data-lang)", "data-lang" in js)
    record("IntersectionObserver for reveal", "IntersectionObserver" in js)
    record(
        "prefers-reduced-motion short-circuit",
        "prefers-reduced-motion" in js,
    )
    record("file:// href rewriter present", "file:" in js)


# ---------------------------------------------------------------------------
# 12. 404 + robots + sitemap wiring
# ---------------------------------------------------------------------------

def _extract_description(path: str) -> str | None:
    text = read(path)
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', text)
    return m.group(1) if m else None


def check_assets() -> None:
    print("\n=== 12. 404.html / robots.txt wiring ===")
    record("404.html exists", os.path.isfile("404.html"))
    record("robots.txt exists", os.path.isfile("robots.txt"))
    if os.path.isfile("robots.txt"):
        rt = read("robots.txt")
        record("robots.txt references sitemap.xml",
               "sitemap.xml" in rt.lower(),
               str(rt))
    record("og-image.png exists", os.path.isfile("assets/img/og-image.png"))
    record("favicon.svg exists", os.path.isfile("assets/img/favicon.svg"))


# ---------------------------------------------------------------------------
# 13. Content drift detector (per §10.6 SDD intent)
# ---------------------------------------------------------------------------

def check_content_drift() -> None:
    print("\n=== 13. Content drift ES↔EN (per §10.6 SDD intent) ===")
    for es_slug, en_slug in PROCESS_PAIRS.items():
        es_path = f"procesos/{es_slug}.html"
        en_path = f"procesos/en/{en_slug}.html"
        if not (os.path.isfile(es_path) and os.path.isfile(en_path)):
            continue
        es_desc = _extract_description(es_path)
        en_desc = _extract_description(en_path)
        if es_desc is None or en_desc is None:
            record(f"{es_slug}/{en_slug} pair: descriptions present", False,
                   "missing")
            continue
        es_lower = es_desc.lower()
        en_lower = en_desc.lower()
        es_present = sorted({
            label
            for es_re, en_re, label in TERM_PAIRS
            if re.search(es_re, es_lower)
        })
        en_present = sorted({
            label
            for es_re, en_re, label in TERM_PAIRS
            if re.search(en_re, en_lower)
        })
        shared = sorted(set(es_present) & set(en_present))
        en_only = sorted(set(en_present) - set(es_present))
        es_only = sorted(set(es_present) - set(en_present))
        record(
        f"{es_slug} pair: ≥1 §4 glossary term shared ES↔EN",
        len(shared) >= 1,
        f"shared={shared} EN-only={en_only} ES-only={es_only}",
    )


# ---------------------------------------------------------------------------
# 14. Runtime proofs — sitemap ↔ server ↔ filesystem
# ---------------------------------------------------------------------------

def check_runtime_proofs() -> None:
    """Delegates the runtime probe to scripts/smoke-site.py and reports the
    result as a single gate invariant. This is what catches drift between
    sitemap.xml and the actual filesystem when files are renamed, deleted,
    or referenced only from HTML without the sitemap being updated."""
    print("\n=== 14. Runtime proofs (sitemap ↔ served ↔ filesystem) ===")
    script = os.path.join(ROOT, "scripts", "smoke-site.py")
    try:
        proc = subprocess.run(
            [sys.executable, script, "--json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        record(
            "Runtime proofs: smoke probe completed within 60s",
            False,
            "scripts/smoke-site.py timed out",
        )
        return
    except Exception as exc:
        record("Runtime proofs: smoke probe runnable", False, str(exc))
        return

    if proc.returncode not in (0, 1):
        record(
            "Runtime proofs: sitemap ↔ server ↔ filesystem",
            False,
            f"smoke-site.py exit={proc.returncode} stderr={proc.stderr.strip()[:200]}",
        )
        return

    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        record("Runtime proofs: probe output was valid JSON", False, str(exc))
        return

    record("Runtime proofs: probe output was valid JSON", True)

    drift = bool(report.get("declared_not_served") or report.get("served_but_unlisted"))
    record(
        "Runtime proofs: no drift between sitemap, server and HTML links",
        not drift,
        (
            f"{len(report.get('declared_not_served', []))} broken, "
            f"{len(report.get('served_but_unlisted', []))} unlinked"
            if drift else "sitemap ≥ server ≥ filesystem"
        ),
    )


# ---------------------------------------------------------------------------
# 15. Byte budget — *> HTML weight + assets weight, unc + gzip
# ---------------------------------------------------------------------------

def check_byte_budget() -> None:
    """Group #15: assert aggregate site weight (HTML + assets) stays below
    pre-declared budgets in both uncompressed and gzip-compressed bytes.
    Catches silent bloat regressions (extra meta tags, verbose
    descriptions, image growth) before publish. Each section (HTML,
    assets) and aggregate emits a separate invariant so the diagnostic
    points at which dimension is overweight.

    Excludes files under docs/ — that folder is operator-facing
    documentation, not user-facing bytes. Also filters hidden files
    (`.DS_Store`, `.gitkeep`, build artefacts) and unknown extensions so
    they don't quietly consume target budget headroom.
    """
    print("\n=== 15. Byte budget (HTML + assets, unc + gzip) ===")
    html_files = [
        f for f in all_html()
        if not to_posix(f).startswith("docs/")
    ]
    asset_files = sorted(
        os.path.join(root, name)
        for root, _dirs, names in os.walk("assets")
        for name in names
        if not name.startswith(".")
        and os.path.isfile(os.path.join(root, name))
        and any(name.lower().endswith(ext) for ext in ASSET_EXTENSIONS)
    )

    # Precondition: key user-facing assets must exist before the per-section
    # asset invariants are meaningful. Without this guard, a botched
    # `git checkout assets/` or an accidental `rm -rf assets/img/` would
    # produce zero-weight asset output and the gate would silence-pass on
    # bloat that wasn't really absent.
    missing_key_assets = [k for k in EXPECTED_KEY_ASSETS if not os.path.isfile(k)]
    if missing_key_assets:
        record(
            "Byte budget precondition: key assets present",
            False,
            f"missing: {missing_key_assets}",
        )
        for inv_name in (
            "Byte budget: assets uncompressed",
            "Byte budget: assets gzip",
            "Byte budget: total uncompressed",
            "Byte budget: total gzip",
        ):
            record(inv_name + " (skipped: keys missing)", False,
                   "precondition failed")
    else:
        record("Byte budget precondition: key assets present", True,
               f"{len(EXPECTED_KEY_ASSETS)} checked, all present")

    def _unc_bytes(files: list[str]) -> int:
        return sum(os.path.getsize(f) for f in files)

    def _gz_bytes(files: list[str]) -> int:
        total = 0
        for f in files:
            try:
                total += len(gzip.compress(open(f, "rb").read()))
            except OSError:
                continue
        return total

    h_unc = _unc_bytes(html_files) / 1024
    h_gz = _gz_bytes(html_files) / 1024
    a_unc = _unc_bytes(asset_files) / 1024
    a_gz = _gz_bytes(asset_files) / 1024

    def _delta(actual: float, limit: float) -> str:
        diff = actual - limit
        if diff <= 0:
            return f"{actual:.1f} KB (limit {limit:.0f}; headroom {abs(diff):.1f} KB)"
        return f"{actual:.1f} KB EXCEEDS limit {limit:.0f} by {diff:.1f} KB"

    record(
        f"Byte budget: HTML uncompressed ≤ {BUDGET_HTML_KB_UNC:.0f} KB",
        h_unc <= BUDGET_HTML_KB_UNC,
        _delta(h_unc, BUDGET_HTML_KB_UNC),
    )
    record(
        f"Byte budget: HTML gzip ≤ {BUDGET_HTML_KB_GZ:.0f} KB",
        h_gz <= BUDGET_HTML_KB_GZ,
        _delta(h_gz, BUDGET_HTML_KB_GZ),
    )
    record(
        f"Byte budget: assets uncompressed ≤ {BUDGET_ASSETS_KB_UNC:.0f} KB",
        a_unc <= BUDGET_ASSETS_KB_UNC,
        _delta(a_unc, BUDGET_ASSETS_KB_UNC),
    )
    record(
        f"Byte budget: assets gzip ≤ {BUDGET_ASSETS_KB_GZ:.0f} KB",
        a_gz <= BUDGET_ASSETS_KB_GZ,
        _delta(a_gz, BUDGET_ASSETS_KB_GZ),
    )
    record(
        f"Byte budget: total uncompressed ≤ {BUDGET_TOTAL_KB_UNC:.0f} KB",
        h_unc + a_unc <= BUDGET_TOTAL_KB_UNC,
        _delta(h_unc + a_unc, BUDGET_TOTAL_KB_UNC),
    )
    record(
        f"Byte budget: total gzip ≤ {BUDGET_TOTAL_KB_GZ:.0f} KB",
        h_gz + a_gz <= BUDGET_TOTAL_KB_GZ,
        _delta(h_gz + a_gz, BUDGET_TOTAL_KB_GZ),
    )


# ---------------------------------------------------------------------------
# 16. HTML markup validate — *.html correctness per page (pure-Python ladder)
# ---------------------------------------------------------------------------

def check_html_validate() -> None:
    """Group #16: HTML markup correctness per page.

    Runs `scripts/html-validate.py` as a subprocess (30 s timeout) and parses
    its JSON output. Each of the 14 catalog entries (13 rules = 9 markup §10
    + 4 a11y §6, plus 1 `file_missing` sentinel excluded from the per-rule
    PASS-emission loop because check_page() emits it directly) emits one
    invariant so a regression points at which constraint is failing.
    Companion to group #15 (byte budget, which targets SIZE); this one
    targets STRUCTURE.

    Why not htmlhint / lighthouse-ci:
    - htmlhint requires Node — conflicts with Python-3.8-only CI runtime
      established in v2.3. Pure-Python keeps the dependency surface flat.
    - lighthouse-ci requires headless Chrome (~250 MB) and 2–5 min per page
      scan vs ~10 ms here. Wall-clock budget would explode past the 5-min
      `timeout-minutes` of `gate.yml`.
    """
    print("\n=== 16. HTML markup validate (17 pages × 14 catalog entries) ===")

    # v2.9: single-source-of-truth rule catalog loaded from
    # scripts/data/html-rules.json. No more hardcoded rules list in spec-lint.py.
    # Precondition invariants: the JSON must exist + be parseable + carry
    # the $schema_version we expect. These are emitted as gate invariants
    # so missing/malformed catalog blocks the gate visibly (not silently).
    rules_json_path = os.path.join(ROOT, "scripts", "data", "html-rules.json")
    if not os.path.isfile(rules_json_path):
        record(
            "HTML validate: rule catalog exists",
            False,
            f"missing: {rules_json_path}",
        )
        return
    try:
        rules_catalog_doc = json.load(open(rules_json_path))
    except json.JSONDecodeError as exc:
        record(
            "HTML validate: rule catalog is valid JSON",
            False,
            f"json error: {exc}",
        )
        return
    record(
        "HTML validate: rule catalog is valid JSON",
        True,
        f"schema_version={rules_catalog_doc.get('$schema_version', '?')}",
    )

    schema_version = rules_catalog_doc.get("$schema_version", 0)
    if not isinstance(schema_version, int) or schema_version < 1:
        record(
            "HTML validate: rule catalog $schema_version >= 1",
            False,
            f"got: {schema_version}",
        )
        return
    record("HTML validate: rule catalog $schema_version >= 1", True)

    rules_catalog = rules_catalog_doc.get("rules", [])
    if not rules_catalog:
        record(
            "HTML validate: rule catalog has at least 1 rule",
            False,
            "rules array empty",
        )
        return
    record(
        f"HTML validate: rule catalog has {len(rules_catalog)} rules",
        True,
        f"expected 14 entries (13 rules + 1 file_missing sentinel) per v2.10 generic engine",
    )

    try:
        proc = subprocess.run(
            [sys.executable, "scripts/html-validate.py"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        record(
            "HTML validate: probe completed in under 30 s",
            False,
            f"exception={type(exc).__name__}: {exc}",
        )
        return

    # Probe emitted parseable JSON.
    try:
        data = json.loads(proc.stdout)
        record(
            "HTML validate: probe output was valid JSON",
            True,
            f"scanned={data.get('files_scanned', 0)}/17 files, "
            f"violations={data.get('files_with_violations', 0)} pages",
        )
    except json.JSONDecodeError:
        record(
            "HTML validate: probe output was valid JSON",
            False,
            f"stdout[:120]={proc.stdout[:120]!r}",
        )
        return

    files_scanned = data.get("files_scanned", 0)
    files_missing = data.get("files_missing", 0)
    record(
        "HTML validate: all 17 pages present on disk",
        files_scanned == 17 and files_missing == 0,
        f"scanned={files_scanned}, missing={files_missing}",
    )

    rule_totals = data.get("rule_totals", {})
    for rule in rules_catalog:
        key = rule["key"]
        label = rule["label"]
        n = rule_totals.get(key, 0)
        record(
            f"HTML validate: {label}",
            n == 0,
            f"pages_with_issue={n}",
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

@contextmanager
def _silenced_stdout():
    """Context manager that redirects sys.stdout to a discardable buffer
    while the wrapped code runs. Used in --json mode to keep the JSON
    document pristine on the real stdout. The captured text is NOT
    exposed: this context only silences, never returns the buffer."""
    saved = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = saved


# Ordered tuple of every gate group. Single source of truth: adding a 14th
# check is one line here, used verbatim in both human and JSON modes.
ALL_CHECKS = (
    check_sitemap,
    check_inventory,
    check_bug_001,
    check_text_purity,
    check_per_page_meta,
    check_homes_timeline,
    check_homes_structural_identity,
    check_process_pages,
    check_jsonld,
    check_design_tokens,
    check_app_js,
    check_assets,
    check_content_drift,
    check_runtime_proofs,
    check_byte_budget,
    check_html_validate,
)

# Group index in ALL_CHECKS (0-based; "g1"=index 0 ... "g15"=index 14).
# Used by --scope to skip costly groups when the caller knows they don't apply.
# Group#14 (runtime proofs) is the slow one — boots an HTTP server + makes 16
# urllib round-trips just to assert sitemap≤>server≤>filesystem drift. Perfect
# candidate to omit from pre-commit fast lanes that only touch docs/scripts.
SCOPE_GROUPS: dict[str, set[int]] = {
    # Default — every check runs (call from CI, manual, --json from a pipe).
    "full": set(),
    # Hook fast lane — skip the runtime probe. Document changes cannot drift
    # the runtime topology; if the site is healthy when the commit starts, it
    # is still healthy when commit ends. Group#15 (byte budget) IS kept because
    # it is sub-second and catches egregiously oversized assets fast.
    "fast": {13},  # skip check_runtime_proofs (group #14)
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON instead of table")
    parser.add_argument(
        "--scope", default="full", choices=("fast", "full"),
        help=("gate scope: 'full' (default — run all 15 groups) | "
              "'fast' (skip group #14 runtime proofs; sub-30s pre-commit lane)"),
    )
    args = parser.parse_args()

    os.chdir(ROOT)

    skipped_indices = SCOPE_GROUPS.get(args.scope, set())
    effective_checks = tuple(
        fn for idx, fn in enumerate(ALL_CHECKS) if idx not in skipped_indices
    )
    # Always tell the caller which groups were skipped, even in --quiet mode
    # via the JSON shape — hooks and dashboards need it for their own logs.
    skipped_names = [fn.__name__ for fn in
                     (ALL_CHECKS[i] for i in sorted(skipped_indices))]

    # Run effective checks. In --json mode, route their chatty per-check output
    # to a discardable buffer so ONLY the JSON document reaches the real
    # stdout — wire consumers (CI, hooks, dashboards) can then pipe or
    # parse without dealing with tables, OK/FAIL rows, or group banners.
    if args.json:
        with _silenced_stdout():
            for fn in effective_checks:
                fn()
    else:
        for fn in effective_checks:
            fn()

    n_pass = sum(1 for _, status, _ in results if status == "PASS")
    n_fail = sum(1 for _, status, _ in results if status == "FAIL")

    if args.json:
        print(json.dumps(
            {
                "scope": args.scope,
                "skipped": skipped_names,
                "pass": n_pass,
                "fail": n_fail,
                "results": [
                    {"name": name, "status": status, "detail": detail}
                    for name, status, detail in results
                ],
            },
            indent=2,
            ensure_ascii=False,
        ))
        return 0 if n_fail == 0 else 1

    print("\n" + "=" * 64)
    print("SPEC-LINT SUMMARY")
    print("=" * 64)
    for name, status, detail in results:
        marker = "OK  " if status == "PASS" else "FAIL"
        row = f"[{marker}] {name}"
        if detail and status == "FAIL":
            row += f"  -> {detail}"
        print(row)
    print()
    print(f"PASS: {n_pass}   FAIL: {n_fail}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
