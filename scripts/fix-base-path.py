#!/usr/bin/env python3
"""
scripts/fix-base-path.py — Rewrite HTML paths to work under a GitHub Pages
project site subpath.

GitHub Pages project sites serve at https://<org>.github.io/<repo>/.
Astro-generated templates use <base href="/"> and absolute paths (/assets/...)
that resolve to the server root instead of the project root.

This script is idempotent: safe to run on already-fixed HTML.

Steps:
  1. <base href="/"> or <base href="<repo>/"> → <base href="/<repo>/">
  2. href="/" (brand link) → href="index.html"
  3. Strip leading / from all href/src (→ relative to <base>)
  4. Resolve ../ and ./ relative to each file's directory
  5. Prefix bare sibling filenames with file's directory
  6. Fix <use href="/assets/..."> (SVG sprites)
  7. Repair breadcrumb links that got incorrect sibling prefix:
       procesos/index.html → index.html
       procesos/en/index.html → en/index.html
"""

from __future__ import annotations

import os
import posixpath
import re
import sys

REPO = "pelletized-seed-plant"
BASE_HREF = f"/{REPO}/"


def fix_html(content: str, rel_path: str) -> str:
    dirname = posixpath.dirname(rel_path.replace("\\", "/"))
    sibling_prefix = dirname + "/" if dirname else ""

    # 1. Brand link → placeholder (exclude <base> tags)
    MARKER = "@@HOME@@"
    def fix_brand(m: re.Match) -> str:
        orig = m.group(0)
        return orig.replace('href="/"', f'href="{MARKER}"', 1)
    content = re.sub(r'<(?!base\b)[^>]*?\bhref="/"', fix_brand, content)

    # 2. Fix all href/src values in non-base tags.
    #    Preserve the FULL tag — replace only the attribute value, not the match text.
    def fix_attr(m: re.Match) -> str:
        attr = m.group(1)
        val = m.group(2)
        orig = m.group(0)

        if any(val.startswith(p) for p in ("http://", "https://", "//",
                                            "mailto:", "tel:", "data:", "#", "?")):
            return orig

        new_val = val

        if new_val.startswith("/"):
            new_val = new_val[1:]
        elif new_val.startswith("../") or new_val.startswith("./"):
            new_val = posixpath.normpath(posixpath.join(dirname, new_val))
        elif "/" not in new_val and "." in new_val and not new_val.startswith("."):
            # Sibling link: prefix with directory (but not index.html — base-relative)
            if new_val != "index.html":
                new_val = sibling_prefix + new_val

        if new_val == val:
            return orig
        return orig.replace(f'{attr}="{val}"', f'{attr}="{new_val}"', 1)

    content = re.sub(r'<(?!base\b)[^>]*?\b(href|src)="([^"]+)"', fix_attr, content)

    # 3. Fix <use href="..."> (SVG sprites)
    def fix_use(m: re.Match) -> str:
        orig = m.group(0)
        val = m.group(1)
        if val.startswith("/"):
            return orig.replace(f'href="{val}"', f'href="{val[1:]}"', 1)
        return orig

    content = re.sub(r'<use\s+href="([^"]+)"', fix_use, content)

    # 4. Restore brand link
    content = content.replace(f'href="{MARKER}"', 'href="index.html"')

    # 5. Set base href LAST (after all other href processing)
    content = content.replace('<base href="/">', f'<base href="{BASE_HREF}">', 1)
    content = content.replace(f'<base href="{REPO}/">', f'<base href="{BASE_HREF}">', 1)

    return content


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    changed = 0

    for root_dir, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("_archive",)]
        for f in files:
            if not f.endswith(".html"):
                continue
            fp = os.path.join(root_dir, f)
            rel = os.path.relpath(fp, root)
            with open(fp, encoding="utf-8") as fh:
                old = fh.read()
            new = fix_html(old, rel)
            if new == old:
                import re as _re
                _m = _re.search('<base[^>]+>', old)
                _mb = _m.group() if _m else 'NONE'
                _mn = _re.search('<base[^>]+>', new)
                _mnb = _mn.group() if _mn else 'NONE'
                if '/pelletized' not in _mnb:
                    print(f'  SKIP {rel}: base old={_mb} base new={_mnb}', file=__import__('sys').stderr)
            if new != old:
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(new)
                print(f"  {rel}")
                changed += 1

    print(f"\n{changed} files modified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
