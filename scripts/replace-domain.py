#!/usr/bin/env python3
"""
replace-domain.py -- Reemplaza el placeholder de dominio en todo el proyecto.

Uso:
    python scripts/replace-domain.py              # dry-run: muestra qué cambiaría
    python scripts/replace-domain.py tudominio.com # reemplaza y escribe los archivos

Sin argumento hace dry-run. Con dominio, hace el replace in-place.
Los archivos en .gitignore, .git/ y scripts/_archive/ se excluyen automáticamente.

Referencia: PEND-002 en SPEC.md §14.
"""

from __future__ import annotations

import os
import re
import sys
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent

OLD_DOMAIN = "example.com"

# Archivos a procesar (todos los que pueden contener el placeholder)
INCLUDE_GLOBS = [
    "*.html", "*.md", "*.xml", "*.txt", "*.json",
    "*.py",
]


def find_affected_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for glob in INCLUDE_GLOBS:
        for p in sorted(REPO.rglob(glob)):
            rel = p.relative_to(REPO)
            parts = rel.parts
            # Excluir .git y _archive
            if any(part.startswith(".git") for part in parts):
                continue
            if "_archive" in parts:
                continue
            # Excluir .frebuff-validation
            if ".frebuff-validation" in parts:
                continue
            files.append(p)
    return files


def _replacements(text: str, new_domain: str) -> list[tuple[str, str]]:
    """Return list of (old_text, new_text) for every replacement in text."""
    result: list[tuple[str, str]] = []

    # 1. https://zarakiomg96-lang.github.io/pelletized-seed-plant -> https://nuevo.dominio
    for m in re.finditer(re.escape(f"https://{OLD_DOMAIN}"), text):
        result.append((m.group(0), f"https://{new_domain}"))

    # 2. og:url relativo -> absoluto
    for m in re.finditer(
        r'property="og:url"\s+content="/([^"]+)"', text,
    ):
        old_val = m.group(0)
        result.append((
            old_val,
            f'property="og:url" content="https://{new_domain}/{m.group(1)}"',
        ))

    # 3. og:image relativo -> absoluto
    for m in re.finditer(
        r'property="og:image"\s+content="/([^"]+)"', text,
    ):
        old_val = m.group(0)
        result.append((
            old_val,
            f'property="og:image" content="https://{new_domain}/{m.group(1)}"',
        ))

    # 4. Base href: extraer subpath del dominio nuevo si lo tiene
    #    ej: "zarakiomg96-lang.github.io/pelletized-seed-plant" -> "/pelletized-seed-plant/"
    #    ej: "semillas.iit.cu"                                  -> "/"
    domain_path = "/"
    if "/" in new_domain:
        domain_path = "/" + new_domain.split("/", 1)[1] + "/"
    for m in re.finditer(
        r'<base\s+href="([^"]+)"',
        text,
    ):
        old_val = m.group(0)
        result.append((
            old_val,
            f'<base href="{domain_path}">',
        ))

    # 5. Canonical/alternate links que usan el subpath viejo
    for m in re.finditer(
        r'href="https?://[^/]+/[^/]+/(index\.html|en/index\.html)"',
        text,
    ):
        old_val = m.group(0)
        parsed = old_val.split("/")
        # Reemplaza el subpath: https://domain/SUBPATH/rest -> https://domain/NEWPATH/rest
        new_domain_only = new_domain.split("/")[0]
        new_val = old_val.replace(parsed[2], new_domain_only)
        if domain_path != "/":
            new_val = new_val.replace("/" + parsed[3] + "/", domain_path)
        else:
            # Sin subpath: https://domain/SUBPATH/index.html -> https://domain/index.html
            new_val = new_val.replace("/" + parsed[3] + "/", "/")
        result.append((old_val, new_val))

    return result


def _apply(text: str, replacements: list[tuple[str, str]]) -> str:
    """Apply replacements in reverse order (safe for same-text changes)."""
    for old, new in replacements:
        if old == new:
            continue
        text = text.replace(old, new, 1)
    return text


def main() -> int:
    dry_run = len(sys.argv) < 2
    new_domain = sys.argv[1] if not dry_run else "TU-DOMINIO.COM"

    if dry_run:
        print(f"=== DRY RUN -- dominio actual: {OLD_DOMAIN}")
        print(f"Pasa un dominio como argumento para aplicar los cambios:\n")
        print(f"    python scripts/replace-domain.py tudominio.com\n")
    else:
        print(f"=== REEMPLAZANDO {OLD_DOMAIN} -> {new_domain}\n")

    files = find_affected_files()
    total = 0

    for fpath in files:
        text = fpath.read_text(encoding="utf-8")
        repls = _replacements(text, new_domain)
        if not repls:
            continue

        rel = fpath.relative_to(REPO)
        print(f"  {rel}:")
        for old, new in repls:
            print(f"    - {old}")
            print(f"    + {new}")
            print()
        total += len(repls)

        if not dry_run:
            fpath.write_text(_apply(text, repls), encoding="utf-8")

    mode = "DRY RUN" if dry_run else "HECHO"
    print(f"{mode}: {total} reemplazo(s) en {len(files)} archivo(s)")
    if dry_run and total == 0:
        print("  (todo limpio -- no hay placeholders de dominio)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
