#!/usr/bin/env python3
"""
scripts/html-validate.py — Group #16 input: pure-Python HTML markup validator.

v2.10: generic JSON-driven rule engine. The catalog (scripts/html-rules.json)
is now the ONLY source of rule metadata + logic specification. Adding a rule
of an existing shape = 1 edit to the catalog. Adding a rule of a NEW shape
= 1 catalog entry + 1 dispatch branch in _dispatch_rule().

The engine has 9 dispatch types (8 + sentinel):

  1. regex_match           — fires if regex matches (or doesn't, if negate=true)
  2. regex_capture_nonempty — fires if regex doesn't match OR capture group 1 is empty
  3. regex_count_compare   — fires if regex count != expected
  4. regex_negative_match  — fires if pattern matches (elements without attr)
  5. regex_capture_min_len — fires if regex doesn't match OR captured len < threshold
  6. set_membership        — fires if any captured value not in allowed_set_ref
  7. nested_inner_text     — fires if any element has empty visible inner text + no aria
  8. input_with_label_lookup — fires if any unskip input has no label
  9. sentinel              — documented but never dispatched (file_missing)

Emits JSON to stdout. spec-lint.py's check_html_validate() parses this JSON
and emits one invariant per rule. Sub-second scan over every *.html in the
4 authoritative page folders (root, en/, procesos/, procesos/en/).

Why not htmlhint or lighthouse-ci:
  - htmlhint requires Node — conflicts with the Python-3.8-only CI runtime
    established in v2.3.
  - lighthouse-ci requires headless Chrome (~250 MB) and 2–5 min per page
    scan vs ~10 ms here. Wall-clock budget would explode past the 5-min
    `timeout-minutes` of `gate.yml`.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from typing import List, Tuple

# Force UTF-8 on stdout/stderr (Windows cp1252 cannot encode ≥ ∉ etc that
# appear in rule labels and notes). Mirrors the same reconfigure in
# spec-lint.py so subprocess output round-trips cleanly.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# Page-folder allow-list (v2.7.2 polish, reviewer finding F1). The 4 folders
# that contain real published pages, per SPEC §3. Future additions require
# editing three sources: this tuple, SPEC §3, and sitemap.xml URL contract.
PAGE_DIRS: tuple = ('', 'en', 'procesos', 'procesos/en')


def _is_page_path(relpath: str) -> bool:
    parts = relpath.split('/')
    if len(parts) == 1:
        return True
    if len(parts) == 2 and parts[0] == 'en':
        return True
    if len(parts) == 2 and parts[0] == 'procesos':
        return True
    if len(parts) == 3 and parts[0] == 'procesos' and parts[1] == 'en':
        return True
    return False


# Filesystem walk: derive ALL_PAGES from os.walk at scan time.
ALL_PAGES: List[str] = sorted(
    os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, '/')
    for dirpath, _dirs, files in os.walk(ROOT)
    for name in files
    if name.endswith('.html')
    and not name.startswith('.')
    and _is_page_path(
        os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, '/')
    )
)

# =============================================================================
# v2.10: Generic JSON-driven rule engine.
# =============================================================================
#
# Architecture: catalog (scripts/html-rules.json) is the ONLY source of rule
# metadata + logic specification. Adding a rule of an existing shape = 1 edit
# to the catalog. Adding a rule of a NEW shape = 1 catalog entry + 1 dispatch
# branch in _dispatch_rule(). Named sets (currently ARIA_ROLES) live in the
# top-level `sets` registry and are referenced by `allowed_set_ref`.

RULES_JSON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'html-rules.json'
)
CATALOG_DOC: dict = json.load(open(RULES_JSON_PATH, encoding='utf-8'))
RULES_CATALOG: List[dict] = CATALOG_DOC['rules']
SETS_REGISTRY: dict = {
    name: frozenset(values)
    for name, values in CATALOG_DOC.get('sets', {}).items()
}
SCHEMA_VERSION: int = CATALOG_DOC.get('$schema_version', 1)
MIGRATIONS: dict = CATALOG_DOC.get('migrations', {})

# Rule type taxonomy (v2.10). Adding a new type = edit KNOWN_TYPES + add
# a dispatch branch in _dispatch_rule().
KNOWN_TYPES: frozenset = frozenset({
    'regex_match',
    'regex_capture_nonempty',
    'regex_count_compare',
    'regex_negative_match',
    'regex_capture_min_len',
    'set_membership',
    'nested_inner_text',
    'input_with_label_lookup',
    'sentinel',  # documented but never dispatched (file_missing)
})

RULE_KEYS: frozenset = frozenset(r['key'] for r in RULES_CATALOG)


def _flags_from_names(names) -> int:
    """Convert a list of regex flag names ('IGNORECASE', 'DOTALL', etc.) into
    a combined flag int. Unknown names are silently ignored."""
    out = 0
    for n in names:
        if hasattr(re, n):
            out |= getattr(re, n)
    return out


def _validate_catalog_at_init() -> None:
    """Validate catalog structural integrity at module init (fail-fast per
    v2.10 thinker recommendation). Typos in type names, missing required
    fields, or unresolved allowed_set_ref all crash immediately on import
    rather than silently skipping rules during a scan."""
    seen_keys: set = set()
    for rule in RULES_CATALOG:
        key = rule.get('key')
        if not isinstance(key, str):
            raise RuntimeError(f"rule missing 'key' field: {rule!r}")
        if key in seen_keys:
            raise RuntimeError(f"duplicate rule key in catalog: {key!r}")
        seen_keys.add(key)
        if not isinstance(rule.get('label'), str):
            raise RuntimeError(f"rule {key!r} missing 'label' field")
        rule_type = rule.get('type')
        if rule_type not in KNOWN_TYPES:
            raise RuntimeError(
                f"rule {key!r} has unknown type: {rule_type!r}. "
                f"Known types: {sorted(KNOWN_TYPES)}"
            )
        # Type-specific required fields.
        if rule_type in ('regex_match', 'regex_capture_nonempty',
                         'regex_count_compare', 'regex_negative_match',
                         'regex_capture_min_len', 'set_membership'):
            if not isinstance(rule.get('pattern'), str):
                raise RuntimeError(
                    f"rule {key!r} (type={rule_type!r}) missing 'pattern' field"
                )
        if rule_type == 'regex_count_compare' and 'expected' not in rule:
            raise RuntimeError(
                f"rule {key!r} (type='regex_count_compare') missing 'expected'"
            )
        if rule_type == 'regex_capture_min_len' and 'threshold' not in rule:
            raise RuntimeError(
                f"rule {key!r} (type='regex_capture_min_len') missing 'threshold'"
            )
        if rule_type == 'set_membership':
            ref = rule.get('allowed_set_ref')
            if ref not in SETS_REGISTRY:
                raise RuntimeError(
                    f"rule {key!r} (type='set_membership') references "
                    f"unknown set: {ref!r}. Known sets: {sorted(SETS_REGISTRY)}"
                )
        if rule_type == 'nested_inner_text':
            if not isinstance(rule.get('element'), str):
                raise RuntimeError(
                    f"rule {key!r} (type='nested_inner_text') missing 'element'"
                )


_validate_catalog_at_init()


def _precompile_patterns() -> None:
    """Compile each rule's regex pattern at module init (one-time cost, then
    cached into the rule dict as _compiled per v2.10 thinker recommendation)."""
    for rule in RULES_CATALOG:
        if rule.get('pattern') and rule['type'] != 'sentinel':
            try:
                rule['_compiled'] = re.compile(
                    rule['pattern'],
                    _flags_from_names(rule.get('pattern_flags', []))
                )
            except re.error as exc:
                raise RuntimeError(
                    f"rule {rule['key']!r} pattern failed to compile: {exc}"
                )


_precompile_patterns()


def _strip_html_tags(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)


def _dispatch_rule(rule: dict, text: str) -> List[str]:
    """Generic rule dispatcher. Returns a list of violation keys (possibly empty)."""
    rule_type = rule['type']

    if rule_type == 'sentinel':
        return []

    if rule_type == 'regex_match':
        negate = rule.get('negate', False)
        match_found = rule['_compiled'].search(text) is not None
        if match_found != negate:  # v2.10.1 fix: was == (inverted semantics)
            return [rule['key']]
        return []

    if rule_type == 'regex_capture_nonempty':
        m = rule['_compiled'].search(text)
        if not m or not m.group(1).strip():
            return [rule['key']]
        return []

    if rule_type == 'regex_count_compare':
        expected = rule.get('expected', 1)
        actual = sum(1 for _ in rule['_compiled'].finditer(text))
        if actual != expected:
            return [f"{rule['key']}_{actual}"]
        return []

    if rule_type == 'regex_negative_match':
        matches = rule['_compiled'].findall(text)
        if matches:
            return [f"{rule['key']}_{len(matches)}"]
        return []

    if rule_type == 'regex_capture_min_len':
        threshold = rule.get('threshold', 1)
        m = rule['_compiled'].search(text)
        if not m:
            return [f"{rule['key']}_missing"]
        actual = len(m.group(1))
        if actual < threshold:
            return [f"{rule['key']}_{actual}_chars_lt_{threshold}"]
        return []

    if rule_type == 'set_membership':
        allowed_set = SETS_REGISTRY[rule['allowed_set_ref']]
        values = rule['_compiled'].findall(text)
        invalid = [v for v in values if v.lower() not in allowed_set]
        if invalid:
            return [f"{rule['key']}_{len(invalid)}"]
        return []

    if rule_type == 'nested_inner_text':
        element = rule['element']
        attrs_required = rule.get('attrs_required', [])
        aria_attrs = rule.get('aria_attrs', ['aria-label', 'aria-labelledby'])
        element_pattern = re.compile(
            rf'<{element}\b([^>]*?)>(.*?)</{element}>',
            re.DOTALL | re.IGNORECASE
        )
        missing = 0
        for attrs, inner in element_pattern.findall(text):
            # attrs_required filter (e.g., <a> without href is skipped)
            skip = False
            for req in attrs_required:
                name = req['name']
                if not re.search(rf'\b{name}=', attrs):
                    skip = True
                    break
                if req.get('non_empty'):
                    val_match = re.search(rf'\b{name}="([^"]*)"', attrs)
                    if val_match and not val_match.group(1).strip():
                        skip = True
                        break
            if skip:
                continue
            # aria-label / aria-labelledby short-circuit
            if any(f'{aa}=' in attrs for aa in aria_attrs):
                continue
            visible = _strip_html_tags(inner).strip()
            if not visible:
                missing += 1
        if missing:
            return [f"{rule['key']}_{missing}"]
        return []

    if rule_type == 'input_with_label_lookup':
        label_for_attr = rule.get('label_for_attribute', 'for')
        labelled_ids = set(re.findall(
            rf'<label\b[^>]*\b{label_for_attr}="([^"]+)"',
            text, re.IGNORECASE))
        skip_input_types = frozenset(rule.get('skip_input_types', []))
        aria_attrs = rule.get('aria_attrs', ['aria-label', 'aria-labelledby'])
        input_pattern = re.compile(r'<input\b([^>]*?)/?>', re.IGNORECASE)
        unlabelled = 0
        for inp_attrs in input_pattern.findall(text):
            type_match = re.search(r'\btype="([^"]*)"', inp_attrs, re.IGNORECASE)
            inp_type = (type_match.group(1).lower() if type_match else 'text')
            if inp_type in skip_input_types:
                continue
            if any(f'{aa}=' in inp_attrs for aa in aria_attrs):
                continue
            id_match = re.search(r'\bid="([^"]*)"', inp_attrs)
            if id_match and id_match.group(1) in labelled_ids:
                continue
            unlabelled += 1
        if unlabelled:
            return [f"{rule['key']}_{unlabelled}"]
        return []

    raise RuntimeError(f"unhandled rule_type: {rule_type!r}")


def check_page(relpath: str) -> List[str]:
    abspath = os.path.join(ROOT, relpath)
    if not os.path.isfile(abspath):
        return ['file_missing']
    with open(abspath, 'r', encoding='utf-8') as f:
        text = f.read()
    violations: List[str] = []
    for rule in RULES_CATALOG:
        violations.extend(_dispatch_rule(rule, text))
    return violations


def _base_key_of(violation: str) -> str:
    """Map a violation key (which may have _{N} suffix) to its base catalog key.
    Returns the base key if found, None otherwise (caller treats as orphan)."""
    for r in RULES_CATALOG:
        key = r['key']
        if violation == key:
            return key
        if violation.startswith(key + '_'):
            return key
    return None


def _public_catalog() -> list:
    """Return the rule catalog stripped of internal engine state (keys
    starting with `_`). `_precompile_patterns()` mutates each rule dict
    in-place to cache `_compiled` (regex Pattern), but Pattern objects
    aren't JSON-serializable, so the public catalog view excludes them.
    Defensive: also strips any other future `_`-prefixed internal keys."""
    return [
        {k: v for k, v in rule.items() if not k.startswith('_')}
        for rule in RULES_CATALOG
    ]


def _parse_args(argv: List[str]) -> argparse.Namespace:
    """Parse CLI args. v2.10.2 adds --test-dir for the fixtures scaffold."""
    parser = argparse.ArgumentParser(
        description=(
            "Pure-Python HTML markup validator (v2.10 generic JSON-driven engine). "
            "Scans *.html via os.walk over the 4 authoritative page folders."
        )
    )
    parser.add_argument(
        "--test-dir",
        metavar="PATH",
        default=None,
        help=(
            "Override the production scanner: walk this directory as if every "
            "*.html were a real page, bypassing _is_page_path() allow-list. "
            "Test scaffold only (scripts/test-rules.py). The output JSON "
            "includes a non-empty 'test_page_dirs' list when this flag is set."
        ),
    )
    return parser.parse_args(argv)


def main() -> int:
    args = _parse_args(sys.argv[1:])
    counter: Counter = Counter()
    violations_per_page = {}
    files_scanned = 0
    files_missing = 0
    files_with_violations = 0
    test_page_dirs: Tuple[str, ...] = ()

    if args.test_dir:
        # Test scaffold mode: walk the test-dir, use absolute paths,
        # bypass the production _is_page_path() allow-list.
        test_dir_abs = os.path.abspath(args.test_dir)
        test_page_dirs = (test_dir_abs,)
        pages: List[str] = sorted([
            os.path.abspath(os.path.join(dp, f))
            for dp, _, fns in os.walk(test_dir_abs)
            for f in fns
            if f.endswith(".html") and not f.startswith(".")
        ])
    else:
        pages = ALL_PAGES

    for relpath in pages:
        v = check_page(relpath)
        violations_per_page[relpath] = v
        if 'file_missing' in v:
            files_missing += 1
            continue
        files_scanned += 1
        if v:
            files_with_violations += 1
        for violation in v:
            base_key = _base_key_of(violation)
            if base_key is not None:
                counter[base_key] += 1
                continue
            # Orphan-key guardrail (v2.10 hardened): every emitted violation
            # key must map to a catalog entry. Catches silent drift between
            # _dispatch_rule() and the catalog.
            raise RuntimeError(
                f"orphan violation key {violation!r} not in rule catalog"
            )

    output = {
        'schema_version': SCHEMA_VERSION,
        'files_scanned': files_scanned,
        'files_missing': files_missing,
        'files_with_violations': files_with_violations,
        'rule_catalog': _public_catalog(),
        'rule_totals': dict(counter),
        'violations_per_page': violations_per_page,
        'test_page_dirs': list(test_page_dirs),
    }

    json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
