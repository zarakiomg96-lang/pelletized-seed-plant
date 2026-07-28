#!/usr/bin/env python3
"""
scripts/fix-base-path.py — Rewrite HTML href/src paths to work under a
GitHub Pages subpath (e.g., /pelletized-seed-plant/).

The Astro-generated templates use <base href="/"> and absolute paths
(/assets/..., /procesos/...). On a GitHub Pages project site, the URL is
https://<org>.github.io/<repo>/ — so absolute paths point at the server
root instead of the project root.

This script:
  1. Changes <base href="/"> to <base href="/<repo>/">
  2. Strips the leading / from all href/src values (making them relative
     to the <base>).
  3. Resolves ../ and ./ paths against each file's directory.
  4. Prefixes bare sibling filenames with the file's directory.
"""

from __future__ import annotations

import os
import posixpath
import re
import sys

REPO = "pelletized-seed-plant"
BASE_HREF = f"/{REPO}/"


def fix_html(content: str, rel_path: str) -> str:
    dirname = posixpath.dirname(rel_path.replace("\\", "/"))  # '' | 'procesos' | 'procesos/en'
    sibling_prefix = dirname + "/" if dirname else ""

    # 1. Base href
    content = content.replace('<base href="/">', f'<base href="{BASE_HREF}">', 1)

    # 2. Brand link (icon home link)
    content = content.replace('href="/"', 'href="index.html"')

    # 3. Fix href/src values
    def fix_attr(m: re.Match) -> str:
        attr = m.group(1)
        val = m.group(2)
        orig = m.group(0)

        if any(val.startswith(p) for p in ("http://", "https://", "//", "mailto:", "tel:", "data:", "#", "?")):
            return orig

        new_val = val

        if new_val.startswith("/"):
            new_val = new_val[1:]
        elif new_val.startswith("../") or new_val.startswith("./"):
            new_val = posixpath.normpath(posixpath.join(dirname, new_val))
        elif "/" not in new_val and "." in new_val and not new_val.startswith("."):
            new_val = sibling_prefix + new_val

        if new_val == val:
            return orig
        return f'{attr}="{new_val}"'

    content = re.sub(r'(href|src)="([^"]+)"', fix_attr, content)

    # 4. Fix <use href="..."> (SVG sprites)
    def fix_use(m: re.Match) -> str:
        val = m.group(1)
        if val.startswith("/"):
            return f'href="{val[1:]}"'
        return m.group(0)

    content = re.sub(r'<use\s+href="([^"]+)"', fix_use, content)

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
            if new != old:
                with open(fp, "w", encoding="utf-8") as fh:
                    fh.write(new)
                print(f"  {rel}")
                changed += 1

    print(f"\n{changed} files modified")
    return 0 if changed >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
