# Gate Contract — `spec-lint.py`

> Registro detallado de cada grupo de checks del gate ejecutable. Este archivo
> es el complemento operativo de `SPEC.md` §15.3: mientras que el spec define
> *qué* debe pasar, este contrato documenta *cómo* se verifica y la evolución
> empírica de cada invariante.
>
> Para el historial de versiones completo, ver `CHANGELOG.md`.
> Para el contrato de diseño y contenido, ver `SPEC.md`.

A partir de v1.2, la Checklist §10 queda cubierta por un script ejecutable
en la raíz del proyecto:

```
python scripts/spec-lint.py            # human-readable PASS/FAIL table, exit 1 if any FAIL
python scripts/spec-lint.py --json     # machine-readable output
```

Cobertura del script (13 grupos de checks):

1. `sitemap.xml` válido y con exactamente 16 URLs (parsea XML con
   namespace real).
2. Inventario HTML: 17 archivos, ninguno faltante ni sobrante.
3. BUG-001 grep `\b0?\d{1,2}\s*/\s*08\b` → 0 hits en `*.html`, `*.md`,
   `*.xml`.
4. Sin caracteres CJK ni placeholders (`Lorem`, `TODO`, `XXX`, `FIXME`).
5. Por página: `<title>`, descripción ≥ 120 chars, `<link rel=canonical>`,
   `hreflang` ES/EN (excepto `404.html`), exactamente 1 `<h1>`, `<html lang>`
   correcto.
6. Homes: **exactamente** 7 `timeline__item` (= 5 main + 2 `--accent`) por
   home, sin substrings.
7. Homes: paridad de cuenta de `.section`, `.section--soft`, `.stats`,
   `.stat`, `.badges`, `.badge`, `.mission-block`, `.split`, `.hero`,
   `.video-frame`.
8. Páginas de proceso (los 7 pares ES↔EN): eyebrow `Proceso/Process NN / 07`,
   `next-step` presente, paridad de `.depth-block`, `.io-grid`, `<tr>` rows.
9. JSON-LD en ambos homes: presente, parsea como JSON, tiene
   `@context=https://schema.org`.
10. CSS design tokens: `--cream`, `--ink`, `--ink-soft`, `--tobacco-700`,
    `--seed` todos definidos; `@media (prefers-reduced-motion: reduce)` y
    `:focus-visible` presentes.
11. `app.js`: aria-current, data-lang, IntersectionObserver, manejo de
    `prefers-reduced-motion`, rewriter `file://`.
12. `404.html`, `robots.txt` (que apunte a `sitemap.xml`), `og-image.png`,
    `favicon.svg` todos presentes.
13. **Drift detector ES↔EN** para cada par de proceso: extrae el
    `<meta name="description">` y verifica que al menos un término del
    glosario §4 aparezca en AMBAS descripciones. Verificación empírica
    de v1.7 categoriza las 29 equivalencias en:

    - **Activas hoy (29/29)**: las 29 equivalencias disparan en al menos
      un par ES↔EN de proceso. `lote/lots`, `polímero/polymer`,
      `fungicida/fungicide`, `trazabilidad/traceability`,
      `bidireccional/bidirectional`,
      `calibr(?:ad[oa]|ación|ar)/calibrat(?:ion|ing|e)`,
      `recubrimiento/coating`, `bombo/drum`, `turbina/turbine`,
      `secado/drying`, `almacén…/warehouse`, `calidad/quality`,
      `certificad[oa]/certified`, `sellad?[oa]/seal(?:ing|ed)?`,
      `etiqueta/label(?:ing|led)?`, `proveedor/supplier`,
      `semilla/seed`, `limpieza/cleaning`,
      `germin(?:ación|ar)/…`, `impureza/impurity`, `graf(?:o|os)/graph(?:s)?`,
      `rotatori[ao]s?/rotating`, `peletización/pelleting`,
      `arcilla inerte/inert clay`, `almacenero/warehouse operator`,
      `operario/floor operator`,
      `especialista de laboratorio/lab specialist`,
      `nodo de decisión/decision node`, `proceso hero/hero process`.
    - **Dormantes**: ninguna al cierre de v1.9. La categoría queda
      en el spec como contrato futuro: si una equivalencia queda sin
      disparar en descripciones por refactor de contenido, vuelve
      automáticamente a esta lista y se documenta con criterio de
      reactivación en `SPEC.md` §14.
14. **Runtime proofs: sitemap ↔ servidor ↔ filesystem**. Delega la prueba a
    `scripts/smoke-site.py` (subprocess JSON, timeout 60 s). Reporta dos
    invariantes: (a) el probe produce JSON parseable, (b) cero drift entre
    las URLs que el sitemap declara, las que el servidor sirve y las que
    las páginas HTML enlazan. Drift = `declared-not-served` (sitemap dice
    URL pero servidor devuelve ≠200) o `served-but-unlisted` (HTML
    referenciado desde otro HTML vía `<a|link|script|img|source|iframe|
    video|track|embed|area>` pero no presente en sitemap). Excluye 404.html.
    Cubrió el **BUG-005 (12 hrefs rotos en `en/index.html`** en su primera
    pasada y queda como contrato permanente contra futuros renames de
    archivos.
15. **Byte budget: HTML + assets, uncompressed + gzip**. Aggregate el peso
    de `*.html` (root, excluyendo `docs/`) y `assets/**/*` y assert que
    cada par (HTML unc, HTML gz, assets unc, assets gz, total unc, total
    gz) esté por debajo de su presupuesto declarado como constante al tope
    de `spec-lint.py`. Targets calibrados al cierre de v2.1:
    `BUDGET_HTML_KB_UNC=175`, `BUDGET_HTML_KB_GZ=55`,
    `BUDGET_ASSETS_KB_UNC=110`, `BUDGET_ASSETS_KB_GZ=60`,
    `BUDGET_TOTAL_KB_UNC=250`, `BUDGET_TOTAL_KB_GZ=90`. Reporta headroom en
    filas PASS y `EXCEEDS limit X by Y KB` en filas FAIL — un mantenedor
    que vea UNA fila en CI entiende inmediatamente en qué dimensión está
    el bloat. Bumpear los límites requiere bumpear este item al
    mismo tiempo.

    Reporta simétrico `shared=[…]`, `EN-only=[…]` y `ES-only=[…]` para
    debugging. Las asimetrías entre ES y EN dentro del set activo son
    visibles en el diagnóstico y sirven como guía para edits que busquen      simetría estricta.

16. **Pre-commit wiring: scope-based gate + fast lane cap**. The hook at `.git/hooks/pre-commit` (POSIX bash, `chmod +x`) classifies staged paths from `git diff --cached --name-only --diff-filter=ACMR` against a case-sensitive trivial whitelist (`docs/`, `scripts/`, `SPEC.md`, `README.md`, `.gitignore`); any non-whitelisted path promotes the commit to SCOPE=`full` while a purely-trivial commit stays in SCOPE=`fast`, which skips group #14 (runtime proofs) under a 30 s cap and keeps group #15 (byte budget). The hook invokes `scripts/check-spec.py --scope=$SCOPE --quiet` and propagates exit codes (0 = commit proceeds, 1 = drift blocked, 124 = timeout blocked). On timeout the wrapper uses `subprocess.run(start_new_session=True)` + `os.killpg(SIGTERM)` so the entire gate process group (gate child + `smoke-site.py` grandchild + `http.server` daemon thread bound to ports 4321-4330) is reaped cleanly — without this, sockets TIME_WAIT would leak across fast-lane commits. WIP bypass: `git commit --no-verify` (Git-native; skips the hook entirely). **v2.4: source-of-truth moved to `.githooks/pre-commit`** (versioned in the repo). Install procedure is the one-liner `git config core.hooksPath .githooks` per clone; after that, every `git pull` automatically updates the hook. On Windows the file may lose its `+x` bit in clone; one-time `chmod +x .githooks/pre-commit` if needed. See `docs/PRE-COMMIT.md §6` for the new install flow + caveats. Bumps to the trivial whitelist or the 30 s cap require editar `CHANGELOG.md` + este item + `docs/PRE-COMMIT.md` en el mismo v. Ver `docs/PRE-COMMIT.md` §6 for the v2.4 install procedure and §7 for the rest of the operator-facing reference.

**Install procedure (v2.4)**: el hook ya NO vive en `.git/hooks/pre-commit`. A partir de v2.4 vive en `.githooks/pre-commit` (versionado en el repo). Cada clon corre `bash scripts/install-hooks.sh` (POSIX) o `scripts\\install-hooks.bat` (Windows) **una sola vez** para setear `git config core.hooksPath .githooks` — idempotente, safe to re-run. Los installers incluyen sanity check (error loud si `.githooks/pre-commit` no está pulled yet) + smoke-test con empty staging (verifica que el hook funciona antes del primer commit real). Las viejas copias en `.git/hooks/pre-commit` son deprecated — user-cleanup vía el snippet "Migrating from v2.3 install" en `docs/PRE-COMMIT.md` §6. Ver esa sección para el step-by-step completo + uninstall + why-two-installers (la justificación cross-platform de `chmod +x` POSIX vs shabang-only Windows).

17. **CI gate: workflow-side envelope complementing the pre-commit hook**. `.github/workflows/gate.yml` runs `python scripts/check-spec.py --scope=full --quiet` on every PR + push to `main` whose changeset touches `*.html` / `*.css` / `*.js` / `sitemap.xml` / `SPEC.md` / `scripts/check-spec.py` / `spec-lint.py` / `.github/workflows/gate.yml` (the `paths:` filter is the explicit-cache equivalent — irrelevant commits don't burn runner-minutes). Job name `spec-lint full scope` (stable identifier so branch protection can match by name); runner `ubuntu-latest`; `timeout-minutes: 5`; `permissions: contents: read` (read-only `GITHUB_TOKEN`, defense-in-depth). Exit != 0 → red status check → branch protection blocks merge. **Scope-policy**: CI always uses `--scope=full`, never `--scope=fast` — the 30 s cap of the pre-commit fast lane is a dev-UX optimization, NOT a correctness argument. CI's job is belt-and-suspenders against `git commit --no-verify` landings. Workflow edits (paths, runner, job name, python-version) require updating `CHANGELOG.md` + este item in the same v. Branch-protection rules (match by name `spec-lint full scope`) live in repo settings, NOT in `SPEC.md` — operational config outside the contract.

**Path coverage is gated, not full-history**: el `paths:` filter de `pull_request` + `push` debe espejar exactamente la superficie de input del gate (HTML/CSS/JS/sitemap/SPEC/robots/assets/scripts/spec-lint/the workflow itself) — `assets/**` en particular es NO obvio pero required porque group #15 byte-budget lo inspecta y un commit asset-only con un `og-image.jpg` re-encodado sería el drift silencioso que escapa a la red. Si se añade un nuevo check que mira una nueva superficie (p.ej. `i18n/*.json` o `*.webmanifest`), el `paths:` filter debe extenderse en el mismo v. La ley empírica: **el filter y la gate.input_surface() son isomorfos bajo la misma bump-version** — no se puede bumpear el uno sin bumpear el otro.

**Job-name contract pin**: el job se llama `spec-lint full scope` y la última step del job (`Assert job-name contract`, con `if: always()`) hard-fails con `::error::Contract violation` si `$GITHUB_JOB != "spec-lint full scope"`. Cambiar ese nombre rompe branch protection silenciosamente porque la protection rule matchea por nombre y un rename sin actualizar settings permite merges con la rule apuntando al job viejo (y un día al job nuevo sin gate). La assertion convierte ese breakage silencioso en un FAIL ruidoso con instrucción explícita al committer: o revertir el rename, o actualizar la branch-protection rule en repo settings. El nombre `spec-lint full scope` se considera parte del contrato del workflow y cualquier rename requiere bumpear este item + `CHANGELOG.md` + la branch-protection config en el mismo v.

18. **SHA-pinned actions + Dependabot monthly supply-chain contract**. Cada línea `uses:` en `.github/workflows/gate.yml` referencia una action por **SHA completo de commit (40-char hex)** con comment trailing `# v{N.M.P}` para auditabilidad humana, NO por tag mutable. A partir de v2.5: `actions/checkout@11d59604169c99144365775c7423927d7f7e9140 # v4.4.0` y `actions/setup-python@a26af6942ad3ed426615b191c9533fbd4802c0ca # v5.6.0`. Defense-in-depth contra tag-mutation: si upstream o atacante reasigna `v4.x.y` a un commit malicioso, todo consumer con `@v4` se compromete silenciosamente; SHA-pin hace la mutation imposible porque el SHA frozen en el YAML referencia un commit específico. El comment `# vN.M.P` no afecta esto — es comment-data para auditadores humanos (qué versión era realmente).

**Dependabot update contract**: `.github/dependabot.yml` configura updates mensuales sobre el ecosystem `github-actions` (el único relevante — este proyecto no tiene `package.json`, `requirements.txt`, `Dockerfile`, ni `go.mod`). Schedule: `interval: monthly, day: 1, time: "04:00"` UTC. PRs en grupos: `actions/*` minor+patch batched en un único PR mensual etiquetado `dependencies`+`security`. `open-pull-requests-limit: 5` (default), `rebase-strategy: auto` (default). Major version bumps **NO entran en el group batch** — surface como PR separado porque pueden traer breaking changes (p.ej., `setup-python` removiendo Python 3.x del matrix default). **Auto-merge NO habilitado** deliberadamente — manual review mandatory porque el workflow mismo alimenta CI: un bump con `python-version: '3.8'` removida upstream rompe el gate justo cuando ese gate debería ser lo que detecta el breakage. Cualquier edit a SHA pins / schedule day / group config / ecosystem scope requiere editar `CHANGELOG.md` + este item + el header comment del workflow + `.github/dependabot.yml` en el mismo v.

19. **Per-PR preview-deploy via GitHub Pages `deployment_path`**. Cada vez que un PR abre o recibe push, `.github/workflows/gate.yml` corre un segundo job `preview-deploy` que corre sólo después de `gate` exits 0 (`needs: gate`) y sólo cuando el evento es `pull_request` con `head.repo.full_name == github.repository` (fork PRs ⇒ conditional skip; gate stays verde porque GITHUB_TOKEN restringido de fork no puede deployar). El job ejecuta: (1) `actions/checkout` SHA-pinned, (2) **sed-rewrite** de `href="/X"` y `src="/X"` a paths relative en cada `*.html` — necesario porque SPEC §3 usa absolute paths que el browser resuelve contra origin y no contra `deployment_path` subpath, (3) `actions/configure-pages` + `actions/upload-pages-artifact` con `path: '.'` (no build step, el sitio es estático, upload-root es el árbol entero), (4) `actions/deploy-pages` con `deployment_path: pr-${{ github.event.pull_request.number }}` — crea URL única por PR a `https://<owner>.github.io/<repo>/deployments/pr-<N>/index.html`, (5) `marocchino/sticky-pull-request-comment@v2` (third-party tag-pinned, hardening deferred) — postea el URL en el PR feed de forma idempotente: cada nuevo push re-edita el mismo comment en lugar de crear N comments. **Permissions kriticos**: `contents: read + pages: write + id-token: write + pull-requests: write` — `id-token: write` es OIDC requirement sin el cual `deploy-pages` falla con `forbidden`; `pull-requests: write` es para el bot comment. **Fork-PR safety**: el conditional `if` aborta silenciosamente el deploy cuando `head.repo != base.repo`, previniendo el patrón "PR desde fork → exfiltración via Pages". **Cleanup strategy**: orphans accumulate (GitHub Pages no auto-limpia `deployment_path` entries en close); trade-off honesty: el sitio es ligero (<250KB) y Pages free tier es generoso, así que v2.6 lo deja acumular y un cleanup step se programa para v2.7 si el repo crece. **Operator requirement**: el repo debe tener Pages habilitado (Settings → Pages → Source: GitHub Actions). **Friction documentada**: el sed-rewrite step muta temporalmente el árbol de trabajo del runner — esto corre después de checkout y antes de upload-pages-artifact, NO deja artifacts contaminados en el repo (el working directory del runner es efímero). Un mantenedor que debuggee un preview rotto debe revisar que el sed cubra todas las extensiones de assets (`href="*.css"`, `src="*.js"`, `src="*.svg"`, `src="*.png"`, `src="*.ico"`, `src="*.webp"`, `src="*.jpg"` en find pattern).

20. **HTML markup validate: pure-Python filesystem-walk ladder over 9 rules**. Group #16 del gate invoca `scripts/html-validate.py` (subprocess 30 s timeout) que deriva `ALL_PAGES` desde `os.walk` (excluyendo `docs/`, `.git/`, hidden files) — **NUNCA hardcoded**, así futuras páginas se auditan automáticamente sin sync risk con sitemap. Aplica 9 reglas a cada `*.html`: DOCTYPE html presente (HTML5); `<html lang="">` present y non-empty (per §6, §10.2); exactamente 1 `<h1>` por página (§10.5 / WCAG b1.3.1); `<title>` non-empty (§10.3, browser tab UX); `<meta name="description">` con ≥120 chars (§10.3, ya enriquecido por BUG-002/003/004) — **regex atributo-order-independent via lookaheads** (cualquier order legal HTML5 funciona); `<link rel="canonical">` present (§10.3); cada `<img>` tiene alt="" (§6 / WCAG 1.1.1); cero CJK placeholder chars — **regex cubre las 3 familias de §10.1: Hiragana, Katakana, CJK Unified Ideographs (japonés+chino) + Hangul Jamo + Hangul Compatibility Jamo + Hangul Syllables (coreano)**; cero deprecated HTML tags (`<center>/<font>/<frame>/<marquee>/<blink>/<big>/<noframes>/<applet>/<acronym>/<tt>/<strike>`, HTML5 + ARIA discipline). Cada regla emite 1 invariant en el gate con label legible + detail `pages_with_issue=N`, así un FAIL de un PR apunta a cuál SPEC §10 constraint está regressing. JSON probe schema: `{ files_scanned, files_missing, files_with_violations, rule_totals: {rule_key: count}, violations_per_page: {relpath: [violation_keys]} }`. **Coverage gaps filled** (lo que grupos previos NO cubrían): `doctype_missing`, `h1_count_mismatch`, `imgs_no_alt`, `deprecated_tags_present` — 4 reglas genuinamente nuevas. Las otras 5 tienen overlap parcial con `check_per_page_meta` (group §5) y `check_text_purity` (group §4), pero defense-in-depth: si el scanner de meta tags pierde algo, la ladder lo agarra con un threshold distinto. **Trade-off documentado**: pure-Python ladder (sub-segundo sobre 17 pages, ~190 LOC) vs htmlhint (requiere Node — choca con CI Python-3.8-only runtime) vs lighthouse-ci (Chrome headless ~250 MB). **Stack elegido**: pure-Python, stdlib-only. **No-False-Positive guard**: si un future edit mueve páginas a subdirectorios no escaneados, group #1 (sitemap vs inventory) lo detecta como `declared-not-served` en el próximo full-scope run.

21. **Page-folder restriction via `_is_page_path()` include-list (v2.7.2 polish)**. Cada scan de group #16 filtera las `*.html` candidates via `_is_page_path(relpath)`, función pura que retorna `True` SOLAMENTE si el relpath cae bajo uno de los 4 prefix-pattern: root-level file (`parts == ['<file.html>']`), `en/<file>` (`parts == ['en', '<file.html>']`, parts.len==2 con parts[0]=='en'), `procesos/<file>` (idem, parts[0]=='procesos'), `procesos/en/<file>` (parts.len==3 con parts[0]=='procesos' y parts[1]=='en'). Cualquier otra path — incluyendo `assets/_partials/foo.html`, `templates/foo.html`, `procesos/sub/foo.html`, `procesos/es/foo.html`, `docs/foo.html`, etc. — retorna `False` y queda silenciosamente excluida. Esta es la inversión F1 polish sobre v2.7.2: el exclude-list anterior (`docs/`, `.git/`, hidden files) atrapeaba cualquier `*.html` en cualquier folder tracked, incluyendo fragmentos que no son páginas reales y que fallarían rules 2/4/5/6 (lang/title/description/canonical no aplican a fragments). El include-list bloquea fragments en source pero mantiene el comportamiento dinámico (drop un nuevo `*.html` en una de las 4 carpetas autorizadas y group #16 lo audita automáticamente sin tener que tocar el script). **Coverage gap semántico**: si un contributor añade una nueva página real en un folder exótico (e.g. `procesos/es/index.html` para España-MX), group #16 lo reportará como missing-page y group #1 sitemap-drift detector levantará el FAIL — la grieta se cierra con doble cobertura (sitemap vs filesystem walk). **Sync contract**: añadir un folder autorizado (e.g. `blog/`) requiere editar (1) `PAGE_DIRS` tuple en `scripts/html-validate.py`, (2) `sitemap.xml`, (3) `SPEC.md` §3 (URL contract enumeration), (4) `CHANGELOG.md` + este item — 4 edits en el mismo v para mantener coverage simétrico cross-files.

24. **Single-source-of-truth rule catalog via `scripts/data/html-rules.json` (v2.9)**. Las 13 reglas de group #16 (9 markup §10 + 4 a11y §6) ya no viven duplicadas entre `scripts/html-validate.py` counter switching y `spec-lint.py` rules list — ahora residen en un solo catálogo JSON versionado (`$schema_version: 1`). Cada entry tiene `{ key, label, pattern, pattern_flags, notes }`: `key` es el violation key emitted por check_page() y looked-up en `rule_totals`; `label` es el description text usado en el gate invariant (visible en `python scripts/spec-lint.py` human-readable output); `pattern` documenta el regex usado por las 9 reglas pure-regex (NO runtime-executed — la lógica real sigue en Python); `pattern_flags` lista los regex flags (`["IGNORECASE"]`, etc.); `notes` explica la lógica multi-step para las 4 reglas complejas (button/link/role/input) que tienen `pattern: null`. **Loader contract**: `scripts/html-validate.py` carga `scripts/data/html-rules.json` en module-init time y exporta `RULES_CATALOG` + `RULE_KEYS` + `RULE_LABELS`. main()'s output dict agrega `schema_version: 1` y `rule_catalog: [...]` para downstream introspection. **Orphan-key guardrail** (defense-in-depth): en main()'s else branch, cada violation key emitida por check_page() que NO sea prefix-matched por un elif branch debe ser exact match a un key del catálogo — RuntimeError en caso contrario. Esto atrapa drift silencioso entre check_page() y el catálogo al ejecutar, no al commit. **spec-lint.py wiring**: `check_html_validate()` reemplaza el hardcoded 13-entry rules list con `json.load(open(rules_json_path))['rules']` y un loop `for rule in rules_catalog: key=rule['key']; label=rule['label']`. 3 nuevos precondition invariants agregados al gate: rule catalog exists (file present), rule catalog is valid JSON (parseable + has $schema_version), rule catalog $schema_version == 1 (contract stability), rule catalog has 13 rules (count match). Si cualquiera falla, el gate falla con detail explícito.

25. **Catalog coverage closure + schema migration path (v2.9.1 polish)**. Dos ajustes menores al catálogo JSON para cerrar grietas surfaced por reviewer F2 + F5. (a) **F2 cerrado**: nuevo entry `file_missing` agregado al final del array `rules` en `scripts/data/html-rules.json`. El sentinel `file_missing` ya era emitido por `check_page()` cuando un page esperado no existe en disco; bypassa el `for violation in v:` loop vía early `continue` por lo que nunca alcanza el orphan-key guardrail, pero quedaba undocumented en el catálogo. Ahora los 14 violation keys (13 reglas + 1 sentinel) tienen catalog entries sin coverage gap. (b) **F5 cerrado**: nuevo top-level field `"migrations": {"1": "current"}` agregado a `scripts/data/html-rules.json`. spec-lint.py's precondition invariant `HTML validate: rule catalog $schema_version == 1` loose-ened a `>= 1` (`schema_version < 1` dispara FAIL), así un bump futuro a schema_version=2 no requiere coordinated edits across files. (c) **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `rule_catalog_len=14` (antes 13); `scripts/check-spec.py --quiet` exit 0 con PASS count sube de 253 a 254 (+1 por el label actualizado del invariant schema_version). **Sync contract**: añadir sentinel nuevo / extender `migrations` map / bump `schema_version` requieren editar `CHANGELOG.md` + este item + `scripts/data/html-rules.json` (catalog entry + migrations field) + `scripts/html-validate.py` (sentinel emission si aplica) + `scripts/spec-lint.py` (precondition invariant labels si la semántica cambia) en el mismo v. Cambio **Fidelidad** (cierra 2 grietas de catálogo sin cambio de contrato visible al usuario final del sitio).

27. **Generic JSON-driven rule engine via 8 dispatch types (v2.10)**. El `scripts/html-validate.py` deja de tener 13 reglas hardcoded en `check_page()` y pasa a ser un generic engine compilado desde `scripts/data/html-rules.json` al module-init time. Cada catalog entry tiene un `type` discriminator que selecciona una de las 8 branches del engine. **Type taxonomy**: (1) `regex_match`; (2) `regex_capture_nonempty`; (3) `regex_count_compare`; (4) `regex_negative_match`; (5) `regex_capture_min_len`; (6) `set_membership`; (7) `nested_inner_text`; (8) `input_with_label_lookup`. **9th type**: `sentinel` (documented but never dispatched). **ARIA_ROLES moved to JSON**: el frozenset de 66 W3C ARIA 1.2 standard roles ahora vive en top-level `sets: {"ARIA_ROLES": [66 roles...]}`. **`$schema_version` bumped to 2** con `migrations: {"1": "legacy", "2": "current"}`. **Init-time fail-fast**: `_validate_catalog_at_init()` corre al import-time y raise RuntimeError si hay typos en type names, missing required fields, unresolved `allowed_set_ref`, o duplicate keys. **Pre-compiled patterns**: regex patterns se compilan una vez al module-init time y se cachean en `rule['_compiled']`. **Orphan-key guardrail hardened**: `_base_key_of(violation)` en `main()` cubre todos los violation keys — cada key emitido por `_dispatch_rule()` debe mapear a un catalog entry o RuntimeError. **Sync contract finalmente realized**: añadir regla de shape existente = 1 edit al catalog. Añadir regla de shape NUEVO = 1 catalog entry + 1 dispatch branch en `_dispatch_rule()` + 1 type name en `KNOWN_TYPES` + 1 type-specific validation branch. **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `schema_version=2 files_scanned=17 rule_totals={}`; `scripts/check-spec.py --quiet` exit 0 con PASS count estable en 254. **Sync contract**: editar 1 catalog entry / extender `ARIA_ROLES` set / bump `$schema_version` / añadir un nuevo dispatch type requieren editar `CHANGELOG.md` + este item + `scripts/data/html-rules.json` (catalog + sets) + `scripts/html-validate.py` (nuevo dispatch branch si aplica) + `scripts/spec-lint.py` (precondition invariant labels si cambia el schema_version check) en el mismo v.

Reglas operativas:

- **Cualquier edit nuevo** debe terminar con `python scripts/spec-lint.py` verde.
- **Exit 0** = bloquea el release; **exit 1** = merge/commit bloqueado.
- Si el script descubre un nuevo invariante, agregalo al script **y** a
  este documento como mismo número de v.
