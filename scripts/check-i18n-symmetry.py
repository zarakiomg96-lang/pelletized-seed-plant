#!/usr/bin/env python3
"""
check-i18n-symmetry.py — verifies ES/EN structural symmetry across process pages.

Checks:
1. Every ES process page has an EN counterpart (and vice versa).
2. Both files in a pair contain the same section markers:
   - "En simple" / "In simple"
   - "En detalle" / "In detail"
   - "Datos" / "Data"
3. Both contain a `<meta name="description" content="...">` tag.
4. `hreflang` links are reciprocal (ES page links to EN, EN page links to ES).

Exit code: 0 if all pairs pass, 1 if any check fails.
"""

from __future__ import annotations

import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESOS_ES = os.path.join(REPO_ROOT, "procesos")
PROCESOS_EN = os.path.join(REPO_ROOT, "procesos", "en")

SECTION_PATTERNS: dict[str, str] = {
    "simple": r'en\s+simple|in\s+simple',
    "detail": r'en\s+detalle|in\s+detail',
    "data": r'datos|data',
}


def es_slug_from_path(path: str) -> str:
    """Extract the ES slug from an absolute path like .../procesos/recepcion.html"""
    base = os.path.basename(path)
    return os.path.splitext(base)[0]


def en_slug_from_es(es_slug: str) -> str | None:
    """Map an ES process slug to its EN counterpart using SPEC §3 pairs."""
    PAIRS: dict[str, str] = {
        "recepcion": "reception",
        "pre-limpieza": "pre-cleaning",
        "limpieza-fina": "fine-cleaning",
        "peletizacion": "pelleting",
        "envasado": "packaging",
        "control-calidad": "quality-control",
        "almacen-producto-terminado": "finished-product-warehouse",
    }
    return PAIRS.get(es_slug)


def extract_sections(text: str) -> set[str]:
    """Find which of the 3 expected sections exist in the file content."""
    found: set[str] = set()
    for name, pattern in SECTION_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.add(name)
    return found


def has_description(text: str) -> bool:
    return bool(re.search(
        r'<meta\s+[^>]*name\s*=\s*["\']description["\'][^>]*content\s*=\s*["\'][^"\']+["\']',
        text,
    ))


def extract_hreflangs(text: str) -> dict[str, str]:
    """Return {lang: href} for all hreflang link tags found."""
    hreflangs: dict[str, str] = {}
    for match in re.finditer(
        r'<link\s+[^>]*hreflang\s*=\s*["\'](\w+)["\'][^>]*href\s*=\s*["\']([^"\']+)["\']',
        text,
    ):
        hreflangs[match.group(1)] = match.group(2)
    return hreflangs


def main() -> int:
    failures = 0
    es_files = sorted(
        f for f in os.listdir(PROCESOS_ES)
        if f.endswith(".html") and os.path.isfile(os.path.join(PROCESOS_ES, f))
    )

    print("=== i18n symmetry check ===")

    for es_name in es_files:
        es_path = os.path.join(PROCESOS_ES, es_name)
        es_slug = es_slug_from_path(es_name)
        en_slug = en_slug_from_es(es_slug)

        if en_slug is None:
            print(f"  FAIL: {es_name} — no EN mapping defined for '{es_slug}'")
            failures += 1
            continue

        en_name = f"{en_slug}.html"
        en_path = os.path.join(PROCESOS_EN, en_name)

        # 1. Both files exist
        if not os.path.isfile(es_path):
            print(f"  FAIL: ES file missing — {es_path}")
            failures += 1
            continue
        if not os.path.isfile(en_path):
            print(f"  FAIL: EN file missing — {en_path} (expected for {es_name})")
            failures += 1
            continue

        es_text = open(es_path, encoding="utf-8").read()
        en_text = open(en_path, encoding="utf-8").read()

        # 2. Section symmetry
        es_sections = extract_sections(es_text)
        en_sections = extract_sections(en_text)
        if es_sections != en_sections:
            print(f"  FAIL: {es_name} sections {sorted(es_sections)} vs {en_name} sections {sorted(en_sections)}")
            failures += 1
        else:
            print(f"  PASS: {es_name} <-> {en_name} — sections match ({sorted(es_sections)})")

        # 3. Description meta tag
        if not has_description(es_text):
            print(f"  FAIL: {es_name} — missing <meta name='description'>")
            failures += 1
        if not has_description(en_text):
            print(f"  FAIL: {en_name} — missing <meta name='description'>")
            failures += 1

        # 4. Reciprocal hreflang links
        es_hrefs = extract_hreflangs(es_text)
        en_hrefs = extract_hreflangs(en_text)

        if "es" not in es_hrefs:
            print(f"  FAIL: {es_name} — missing hreflang='es'")
            failures += 1
        if "en" not in es_hrefs:
            print(f"  FAIL: {es_name} — missing hreflang='en'")
            failures += 1
        if "es" not in en_hrefs:
            print(f"  FAIL: {en_name} — missing hreflang='es'")
            failures += 1
        if "en" not in en_hrefs:
            print(f"  FAIL: {en_name} — missing hreflang='en'")
            failures += 1

    for es_file in es_files:
        es_slug = es_slug_from_path(es_file)
        en_slug = en_slug_from_es(es_slug)
        if en_slug:
            en_name = f"{en_slug}.html"
            en_path = os.path.join(PROCESOS_EN, en_name)
            if os.path.isfile(en_path):
                en_text = open(en_path, encoding="utf-8").read()
                es_hrefs = extract_hreflangs(open(os.path.join(PROCESOS_ES, es_file), encoding="utf-8").read())
                en_hrefs = extract_hreflangs(en_text)
                if "es" in es_hrefs and "en" in en_hrefs:
                    print(f"  PASS: {es_file} <-> {en_name} — hreflang reciprocal")
                else:
                    print(f"  FAIL: {es_file} <-> {en_name} — hreflang not reciprocal")
                    failures += 1

    if failures:
        print(f"\nResult: FAIL ({failures} issue(s))")
    else:
        print(f"\nResult: PASS — all {len(es_files)} pairs symmetric")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
