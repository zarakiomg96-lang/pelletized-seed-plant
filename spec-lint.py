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
import io
import json
import os
import re
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

ROOT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()


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
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON instead of table")
    args = parser.parse_args()

    os.chdir(ROOT)

    # Run all checks. In --json mode, route their chatty per-check output
    # to a discardable buffer so ONLY the JSON document reaches the real
    # stdout — wire consumers (CI, hooks, dashboards) can then pipe or
    # parse without dealing with tables, OK/FAIL rows, or group banners.
    if args.json:
        with _silenced_stdout():
            for fn in ALL_CHECKS:
                fn()
    else:
        for fn in ALL_CHECKS:
            fn()

    n_pass = sum(1 for _, status, _ in results if status == "PASS")
    n_fail = sum(1 for _, status, _ in results if status == "FAIL")

    if args.json:
        print(json.dumps(
            {
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
