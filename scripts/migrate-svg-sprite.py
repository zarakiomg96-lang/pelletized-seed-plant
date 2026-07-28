#!/usr/bin/env python3
"""Replace all inline SVGs with <use> references to assets/icons/sprite.svg."""

import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPRITE_IDS = [
    'brand',
    'play',
    'timeline-recepcion',
    'timeline-prelimpieza',
    'timeline-limpieza-fina',
    'timeline-peletizacion',
    'timeline-envasado',
    'timeline-control-calidad',
    'timeline-almacen',
]

BASE = ['index.html', 'en/index.html', '404.html']
ES_SLUGS = ['recepcion', 'pre-limpieza', 'limpieza-fina', 'peletizacion',
            'envasado', 'control-calidad', 'almacen-producto-terminado']
EN_SLUGS = ['reception', 'pre-cleaning', 'fine-cleaning', 'pelleting',
            'packaging', 'quality-control', 'finished-product-warehouse']

HTML_FILES = (
    BASE
    + [f'procesos/{s}.html' for s in ES_SLUGS]
    + [f'procesos/en/{s}.html' for s in EN_SLUGS]
)


def main() -> int:
    modified = 0
    for filepath in HTML_FILES:
        fpath = os.path.join(ROOT, filepath)
        with open(fpath, encoding='utf-8') as f:
            html = f.read()

        svgs = list(re.finditer(r'<svg[^>]*>.*?</svg>', html, re.DOTALL))
        n = len(svgs)
        if n == 0:
            print(f'  SKIP {filepath}: no SVGs')
            continue

        for i, m in reversed(list(enumerate(svgs))):
            if n == 1:
                sprite_id = 'brand'
            elif n == 9 and i < len(SPRITE_IDS):
                sprite_id = SPRITE_IDS[i]
            else:
                print(f'  WARN {filepath}: unexpected #SVGs={n} at idx={i}')
                continue

            old_svg = m.group(0)
            vb = re.search(r'viewBox="([^"]+)"', old_svg)
            vb_str = vb.group(1) if vb else '0 0 24 24'
            new_svg = f'<svg viewBox="{vb_str}"><use href="/assets/icons/sprite.svg#{sprite_id}"/></svg>'
            html = html[:m.start()] + new_svg + html[m.end():]

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  OK {filepath}: {n} SVG(s) replaced')
        modified += 1

    print(f'\nDone: {modified} files modified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
