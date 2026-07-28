# Runtime Proofs — Group #14 of the SDD gate

> Este documento explica en lenguaje humano **qué cubre el grupo #14 del
> gate** (`scripts/smoke-site.py` + `check_runtime_proofs()` en
> `spec-lint.py`), **cuándo conviene correrlo a mano**, y **cómo extender
> el sitio con un proceso 08** sin romper la cadena de drift.

---

## Audiencia

- Un colaborador que no es la persona que escribió `scripts/smoke-site.py`
  pero necesita agregar contenido al sitio.
- Un revisor que valida que el sitio se va a poder desplegar tal cual está.
- El "yo del futuro", dentro de 6 meses, que va a olvidar el contexto.

Si nunca has ejecutado un gate y nunca has tocado el sitemap, este
documento es para vos. Si ya sabes lo que es `spec-lint.py`, §1 es repaso,
§4 es lo que buscás.

---

## 1. El problema que resuelve el grupo #14

El sitio es 100% HTML estático. Tres lados tienen que estar sincronizados
para que un visitante no se pierda:

| Lado | Fuente de verdad | Cómo se valida |
|---|---|---|
| **Sitemap** | `sitemap.xml` — declara las 16 URLs reales para crawlers | el grupo #1 del gate lo analiza |
| **Filesystem** | los archivos en `procesos/`, `procesos/en/`, `en/`, etc. | el grupo #2 los enumera |
| **HTML links** | los `<a href>` y `<link href>` dentro de cada página | hasta v1.9, **nadie los verificaba** |

Antes de v2.0, los grupos 1–13 validaban **estructura**: ¿el sitemap
tiene 16 URLs? ¿existen los 14 archivos de proceso? ¿tienen cada uno las
meta tags correctas? Pero **nadie hacía un `GET` real** para confirmar que
las tres fuentes de verdad coincidían exactamente.

Eso abrió una grieta. Un caso real (cerrado en v2.0 como BUG-005):
`en/index.html` tenía 12 `<a href="/en/procesos/<slug>.html">` apuntando a
rutas que no existían. Cada vez que un visitante hacía click en una
tarjeta del timeline EN, caía en un 404 nativo del servidor — error
silencioso, sin indicador en el gate.

El grupo #14 cierra la grieta: arranca un servidor local, hace GET a cada
URL del sitemap, enumera los HTML referenciados desde cualquier otro HTML,
y verifica que las tres fuentes de verdad cuadren.

---

## 2. Qué cubre exactamente el grupo #14

`spec-lint.py` ahora tiene 14 grupos de checks. Los primeros 13 cubren
**estructura** (regex, namespaces, conteo de atributos). El grupo #14 es
**runtime**: lanza un `python -m http.server` local en `127.0.0.1` sobre
uno de los puertos candidatos, hace un GET a cada `<loc>` del sitemap y
grep-a cada HTML en busca de referencias locales.

| Categoría de drift | Significado | Cómo se reproduce |
|---|---|---|
| `declared-not-served` | El sitemap declara `<loc>X</loc>` pero el servidor devuelve ≠200 al hacer GET a `X` | Se borra un archivo referenciado en sitemap, o se renombra sin actualizar sitemap |
| `served-but-unlisted` | Un `.html` en disco está enlazado desde otro HTML (vía `<a href>`, `<link href>`, `<script src>`, `<img src>`, `<video src|poster>`, etc.) pero el sitemap no lo incluye — crawlers no lo encontrarán | Se crea un nuevo HTML y se enlaza desde otro sin tocar el sitemap |

`404.html` está **explícitamente excluido** del chequeo `served-but-unlisted`.
El sitemap no debe listarlo (ver §10.4 del spec), pero es perfectamente
válido que esté enlazado desde otros HTML (el header y el footer lo hacen).

### Categorías ignoradas a propósito

- **Diferencias de query string** (`?utm=...`): el probe las descarta antes
  de comparar.
- **URLs absolutas externas** (`https://...`, `//cdn...`, `mailto:...`): no
  son nuestro problema, el sitemap no las declara.
- **Assets no-HTML** (`/assets/css/styles.css`, `/assets/js/app.js`): el
  sitemap no los lista por convención (sólo lista páginas). El gate
  estructural ya garantiza que existen vía el grupo #12.
- **`/404.html`**: ver arriba.

---

## 3. Cuándo correr `smoke-site.py` a mano

El grupo #14 corre automáticamente cuando ejecutás el gate completo
(`scripts/check-spec.py` o `spec-lint.py` directo). Rara vez necesitás
correr `smoke-site.py` aislado. Estos son los casos donde conviene:

| Escenario | Comando | Por qué a mano |
|---|---|---|
| **Vas a renombrar o borrar varios archivos a la vez** | `python scripts/smoke-site.py` después del rename | Más rápido que pasar el gate entero y salida más legible |
| **Vas a desplegar y querés un re-check antes de `git push`** | `python scripts/smoke-site.py --quiet` | Sólo imprime la línea de resolución; ideal para CI exit codes |
| **Querés un JSON consumible para un dashboard o hook** | `python scripts/smoke-site.py --json` | Salida parseable: `pass`, `fail`, `declared_not_served[]`, `served_but_unlisted[]`, `port`, `sitemap_urls_count` |
| **Sospechás que las invariantes del gate están mintiendo** | `python scripts/smoke-site.py --json \| python -m json.tool` | El JSON mode es la verdad de fuente única; el modo humano sólo formatea |

### Lo que NO vas a ver

- El probe **no** chequea que el HTML se vea "bonito" en pantalla — eso
  requiere un navegador real (futuro: PEND-001 reemplazo del `<video>`).
- El probe **no** chequea performance — no mide peso, ni tiempo de carga,
  ni accesibilidad WCAG. Esos chequeos viven en otros grupos y/o serían
  grupo #15+.
- El probe **no** detiene servidores que ya estén corriendo en 4321.
  En lugar de eso, intenta los candidatos `4321, 4322, ..., 4330` y se
  rinde con exit 2 si los 10 están ocupados. Si tenés tu propio
  `python -m http.server 4321` corriendo en otra terminal, **no hay
  conflicto** — vas a ver que smoke-site elige 4322 y se queda con el
  puerto libre.

---

## 4. Walkthrough — agregar proceso 08

Este ejemplo asume que el Instituto decide agregar **"Entrega a
Productores"** como proceso 08/08, después del almacén de producto
terminado. Es una adición al **final** del pipeline: no rompe la
numeración existente (procesos 01–07 siguen como están), pero requiere
sincronizar sitemap, filesystem, gateway PROCESS_PAIRS, y el next-step
del proceso 07.

> Si vas a insertar el proceso nuevo en el medio del pipeline, además
> tendrás que renumerar los eyebrow `Proceso NN/07` de los procesos
> siguientes y el gate te exigirá que actualices `EXPECTED_TOTAL_HTML` en
> `spec-lint.py`. Es legal, pero más invasivo. Agregar **al final** es
> el caso más limpio.

### 4.1 Elegir slugs ES/EN

Los slugs son kebab-case en ambos idiomas:

| ES | EN |
|---|---|
| `entrega` | `delivery` |

Vas a escribir:
- `procesos/entrega.html` (ES)
- `procesos/en/delivery.html` (EN)

### 4.2 Crear los dos archivos HTML

Copiá la estructura de un proceso existente (por ejemplo
`procesos/almacen-producto-terminado.html`) y adaptá:

- `<html lang="es">` o `<html lang="en">`.
- `<title>` y `<meta name="description">` únicos por idioma.
- `class="eyebrow"` que diga `Proceso 08 / 08` / `Process 08 / 08`.
- Bloques `.depth-grid` + `.io-grid` + `.telemetry` (recomendado, no
  obligatorio — pero hace pasar el gate estructural más fácil).
- Como es el último paso, **no** incluás `<a class="next-step">`.

### 4.3 Actualizar `sitemap.xml`

Agregar dos `<url>` blocks al sitemap, **respetando el orden visual** (los
procesos van antes que cualquier otra cosa que se sume en el futuro):

```xml
<url><loc>https://zarakiomg96-lang.github.io/pelletized-seed-plant/procesos/entrega.html</loc>
     <changefreq>monthly</changefreq><priority>0.8</priority></url>
<url><loc>https://zarakiomg96-lang.github.io/pelletized-seed-plant/procesos/en/delivery.html</loc>
     <changefreq>monthly</changefreq><priority>0.8</priority></url>
```

El total de URLs del sitemap pasará de **16** a **18**.

### 4.4 Actualizar los homes ES y EN

En `index.html` y `en/index.html`, agregar una octava tarjeta al timeline
(la `.timeline`), siguiendo la estructura `class="timeline__item"`. La
tarjeta debe enlazar a la nueva página:

```html
<a class="timeline__item" href="/procesos/entrega.html">
  ...
</a>
```

Para el EN:

```html
<a class="timeline__item" href="/procesos/en/delivery.html">
  ...
</a>
```

> Los acentos visuales (`class="timeline__item--accent"`) siguen siendo 2:
> procesos 04 (Peletización y Secado) y 06 (Control de Calidad).
> Proceso 08 no es acento — es la salida del pipeline.

El gate estructural va a fallar el grupo #6 si la cuenta de
`timeline__item` es distinta de 8 o si la cuenta de `--accent` no es 2.
Esto es **a propósito**: structural identity entre ES y EN es contract.

### 4.5 Extender `PROCESS_PAIRS` en `spec-lint.py`

Buscá:

```python
PROCESS_PAIRS: dict[str, str] = {
    "recepcion": "reception",
    ...
    "almacen-producto-terminado": "finished-product-warehouse",
}
```

Agregá la nueva entrada (en orden de pipeline):

```python
PROCESS_PAIRS: dict[str, str] = {
    "recepcion": "reception",
    "pre-limpieza": "pre-cleaning",
    "limpieza-fina": "fine-cleaning",
    "peletizacion": "pelleting",
    "envasado": "packaging",
    "control-calidad": "quality-control",
    "almacen-producto-terminado": "finished-product-warehouse",
    "entrega": "delivery",   # ← proceso 08/08
}
```

Agregar también requiere extender **tres** constantes en `spec-lint.py`
para que el gate siga verde (señalá los cuatro cambios — tres constantes
+ la entrada nueva en `PROCESS_PAIRS` — en el mismo commit):

- `"EXPECTED_SITEMAP_URLS = 16"` → `18` (sumamos 2 URLs al sitemap: una
  para el slug ES + una para el slug EN).
- `"EXPECTED_TOTAL_HTML = 17"` → `19` (sumamos **2 archivos** al disco: el
  ES y el EN; breakdown: 2 homes + 8 ES + 8 EN + 1 404 = 19).
- `"N_HOME_TIMELINE = 7"` → `8` (cada home ahora muestra 8 tarjetas en el
  timeline, no 7).
- `check_process_pages()` en `spec-lint.py` tiene **DOS regex inline**
  hardcoded con `\s*/\s*07` para validar el formato del eyebrow
  (`Proceso NN / 07` en ES y `Process NN / 07` en EN). Como ahora hay 8
  procesos en el pipeline, ambos regex deben pasar a `\s*/\s*08` **y**
  los 7 procesos ya existentes deben actualizar el texto de su eyebrow:
  `Proceso 01 / 07` → `Proceso 01 / 08`, ..., `Proceso 07 / 07` →
  `Proceso 07 / 08`, y los mismos 7 en EN. Sin esto, el gate grupo #8
  falla en los 7 procesos viejos (no reconoce el patrón `/ 07`) y
  tampoco reconoce el eyebrow `Proceso 08 / 08` del proceso nuevo.

### 4.6 Reenlazar el `next-step` del proceso 07

En `procesos/almacen-producto-terminado.html` y
`procesos/en/finished-product-warehouse.html`, el `next-step` actualmente
NO existe (proceso 07 era el último). Ahora proceso 08 lo es. Agregar:

ES:
```html
<a class="next-step" href="/procesos/entrega.html">
  <span class="next-step__label">Continúa con el paso 8</span>
  <span class="next-step__title">Entrega a productores</span>
  <span class="next-step__arrow">›</span>
</a>
```

EN:
```html
<a class="next-step" href="/procesos/en/delivery.html">
  <span class="next-step__label">Continue with step 8</span>
  <span class="next-step__title">Delivery to growers</span>
  <span class="next-step__arrow">›</span>
</a>
```

### 4.7 Actualizar el spec en `SPEC.md`

Documentá la nueva ficha siguiendo el patrón de §9.2.7:

- Agregá la fila en §3 IA table (proceso 08 al final).
- Nueva subsección §9.2.8 con bloque `next-step →` (none — fin del pipeline).
- Bumpeá a `v2.1` en [`CHANGELOG.md`](../CHANGELOG.md) con una nota explicando la cadena de cambios.

### 4.8 Correr el gate

```bash
python scripts/check-spec.py --quiet
```

El primer pase **debe** pasar verde. Si no:

| Síntoma | Probable causa |
|---|---|
| `[FAIL] Sitemap has exactly 16 URLs: got 18` | Olvidaste agregar el `<url>` al sitemap (o agregaste duplicado) |
| `[FAIL] 18 HTML files present: got 16` | Olvidaste crear uno de los dos HTMLs del par |
| `[FAIL] procesos/entrega / … pair present` | El ES existe pero el EN no (o viceversa) |
| `[FAIL] No unexpected HTML files` | Hay un .html en una carpeta que no debería |
| `[FAIL] Runtime proofs: no drift` | Tu nuevo HTML no está referenced en `sitemap.xml` pero sí lo enlazaste desde otro |

Si pasa **todos los grupos** incluido el #14, el sitio está en estado
desplegable con proceso 08.

---

## 5. Quick reference

### Comandos diarios

```bash
# Gate completo, modo silencioso (ideal para CI)
python scripts/check-spec.py --quiet

# Gate completo, salida detallada (para debugging humano)
python scripts/check-spec.py

# Sólo el grupo #14 (rápido cuando ya sabés que los primeros 13 pasan)
python scripts/smoke-site.py

# JSON mode para pipe
python scripts/smoke-site.py --json | python -m json.tool
```

### Salidas que vas a ver cuando todo está bien

```
[smoke-site] PASS — sitemap matches reality on port 4321
              (18 URLs served, 0 broken, 0 unlinked HTML pages)
```

```
[check-spec] PASS — exit 0 (gate verde)
```

```
{
  "pass": 1,
  "fail": 0,
  "sitemap_urls_count": 18,
  "declared_not_served": [],
  "served_but_unlisted": [],
  "port": 4321
}
```

### Salidas que vas a ver cuando algo está mal

```
[smoke-site] FAIL — drift detected on port 4321 (1 broken, 2 unlinked)
  declared-not-served:
    [404] http://127.0.0.1:4321/procesos/entrega.html
  served-but-unlisted:
    procesos/scratch.html
    procesos/legacy-test.html
```

El primer bloque te dice "el servidor no encuentra este archivo". El
segundo bloque te dice "estos archivos existen y son referenciados desde
otros, pero no están en el sitemap — crawlers no los van a encontrar".

---

## 6. Errores comunes (pitfalls)

### A) El sitemap dice una cosa pero el HTML linkea otra

Esto fue el **BUG-005**. Síntoma: el probe detecta **7 paths distintos**
en `served-but-unlinked` (todos apuntando a `en/procesos/<slug>.html` que
NO existen como archivos — los archivos reales están en `procesos/en/`).
Detrás de esos 7 paths hay **12 ocurrencias** de `<a href>` en
`en/index.html` (las 7 tarjetas del timeline + 4 entradas del footer
nav + 1 CTA "Start at pelleting"), que colapsan a los mismos 7 paths
distintos porque hay múltiples enlaces al mismo slug. La causa: el home
EN los escribía como si vivieran en una subcarpeta `en/` pero la
realidad del filesystem es `procesos/en/`. Fix: cambiar los hrefs para
que apunten a las rutas reales en `procesos/en/`.

### B) Olvidaste enlistar el nuevo proceso en el sitemap

Síntoma: `declared-not-served` lista la nueva URL. Causa: el proceso 08
existe como HTML y está enlazado desde el home, pero el `<url>` falta en
`sitemap.xml`. Fix: agregar las 2 entradas (`<loc>` ES + `<loc>` EN) al
sitemap.

### C) Renombrás un HTML pero no actualizás los hrefs

Síntoma: `declared-not-served` lista la URL vieja que ya no existe, y
`served-but-unlisted` lista el nuevo nombre que no está en sitemap.
Fix: editar sitemap + actualizar todos los hrefs que apuntaban al
nombre viejo, en una sola pasada (grep primero para no perder ninguno).

### D) El puerto 4321 está "ocupado para siempre" en Windows

Síntoma: cada corrida del probe usa un puerto distinto (4321, 4322,
4323, ...). Causa: sockets TIME_WAIT de un `http.server` matado con
fuerza bruta. Fix: ya está mitigado por `_ReuseAddrServer` con
`allow_reuse_address = True` (en `scripts/smoke-site.py`). Si ves el
problema en una versión vieja del script, actualizá.

### E) Tu CI mata las probe después de 30 segundos

Síntoma: `check-spec.py` reporta `[FAIL] Runtime proofs: smoke probe
completed within 60s`. Causa: el probe arrancó 10 servidores fallidos
antes de encontrar uno libre, o el sistema estaba bajo carga. Fix:
el timeout default de `subprocess.run` en `spec-lint.py` es 60s. Si
necesitás bajar, ajustá la línea `timeout=60` en
`check_runtime_proofs()`.

---

## 7. Referencias cruzadas

- `docs/GATE-CONTRACT.md item 14` — descripción formal del grupo #14.
- `CHANGELOG.md v2.0` — change log con el momento en que este grupo
  entró al gate y el BUG-005 que destapó.
- `scripts/smoke-site.py` — el script canónico. ~260 líneas, totalmente
  legible de arriba a abajo.
- `scripts/check-spec.{py,sh,bat}` — wrappers portables para invocar
  el gate desde CI/IDE/git hooks.
- `scripts/check-runtime-proofs` directos: el grupo #14 vive en
  `spec-lint.py` bajo `def check_runtime_proofs():`. Esa función hace el
  `subprocess.run(['python', 'scripts/smoke-site.py', '--json'])` y
  parsea el JSON.

---

> **Última revisión**: este documento entra en vigencia con `v2.0` del
> spec. Si cambia el comportamiento del probe (nuevas categorías de drift,
> nuevos tags cubiertos, etc.), actualizar acá **y** en
> `docs/GATE-CONTRACT.md item 14` al mismo tiempo.
