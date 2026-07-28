#!/usr/bin/env python3
"""Add <base href="/"> to every HTML page."""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HTML_FILES = [
    "index.html",
    "en/index.html",
    "404.html",
    "procesos/recepcion.html",
    "procesos/pre-limpieza.html",
    "procesos/limpieza-fina.html",
    "procesos/peletizacion.html",
    "procesos/envasado.html",
    "procesos/control-calidad.html",
    "procesos/almacen-producto-terminado.html",
    "procesos/en/reception.html",
    "procesos/en/pre-cleaning.html",
    "procesos/en/fine-cleaning.html",
    "procesos/en/pelleting.html",
    "procesos/en/packaging.html",
    "procesos/en/quality-control.html",
    "procesos/en/finished-product-warehouse.html",
]

VIEWPORT = '<meta name="viewport" content="width=device-width, initial-scale=1">'
BASE_TAG = '  <base href="/">'


def main() -> int:
    for relpath in HTML_FILES:
        fpath = os.path.join(ROOT, relpath)
        with open(fpath, encoding="utf-8") as f:
            html = f.read()

        if '<base href=' in html:
            print(f"  SKIP {relpath}: already has <base>")
            continue

        old = VIEWPORT + "\n"
        new = VIEWPORT + "\n" + BASE_TAG + "\n"
        html = html.replace(old, new, 1)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  OK  {relpath}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
