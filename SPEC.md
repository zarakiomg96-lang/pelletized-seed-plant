# SPEC — Planta de Semillas Peletizadas

> Especificación formal (Specification-Driven Development) del sitio informativo
> bilingüe (ES / EN) de la **Planta de Semillas Peletizadas** del
> **Instituto de Investigación del Tabaco**.
>
> Este documento es el contrato entre la intención ("qué tiene que hacer el
> sitio") y la implementación ("el HTML/CSS/JS que ya existe"). Cualquier cambio
> futuro debe empezar por actualizar este archivo y terminar pasando la
> **Checklist de validación** (sección §10).

---

## 1. Goals, Non-Goals & Out of Scope

### Goals (objetivos afirmativos)

- **Informar**, no transaccionar: explicar los 7 procesos de la Planta a tres
  audiencias superpuestas (público general, estudiantes/auditores, personal del
  taller), en español y en inglés.
- **Cero fricción de despliegue**: 100 % HTML/CSS/JS estático, sin build step,
  sin runtime de Node en producción, sin framework JS, sin base de datos.
- **Independencia de plataforma**: el sitio debe verse igual sirviéndose desde
  `python -m http.server`, GitHub Pages, Netlify, Cloudflare Pages o cualquier
  servidor HTTP que respete Content-Type.
- **Accesibilidad de primer orden**: WCAG 2.1 AA como mínimo.
- **Descubribilidad**: cada página tiene ruta canónica + hreflang ES/EN + meta
  Open Graph + Twitter Card. Schema.org vive en las dos páginas de inicio.

### Non-Goals (decisiones explícitas de no-hacer)

- **No** hay login, **no** hay autenticación, **no** hay formularios con POST.
- **No** hay CMS, **no** hay base de datos, **no** hay backend.
- **No** hay React, Vue, Svelte, Astro, 11ty ni cualquier SSG (la tentación ya
  se probó y rompió el flujo npm).
- **No** hay analytics (Plausible, GA, etc.) hasta que se decida lo contrario.
- **No** hay Service Worker / PWA / manifest hasta que se decida lo contrario.
- **No** hay dark mode (se puede añadir más adelante como capa sobre el mismo
  design system).

### Out of Scope (no se contempla)

- Migrar la Planta a una app transaccional o un sistema de tickets.
- Reemplazar el contenido de la tesis: el contenido se sintetiza de la tesis
  existente (Manso González, 2026); este sitio no la sustituye.
- Cualquier cosa que requiera un programador para actualizarse: el cambio de
  contenido debe hacerse editando HTML directamente.

---

## 2. Audience Model

El sitio está escrito para tres audiencias que conviven en cada ficha de proceso.
La profundidad de lectura es opt-in: nadie tiene que leer las tres capas.

| Audiencia | Necesita encontrar… | Capa preferida |
|---|---|---|
| **Público general** (estudiante de preuniversitario, vecino curioso) | Qué pasa y por qué importa. | **En simple / In simple** |
| **Auditor, técnico agrícola, prensa especializada** | Cómo se hace, qué se controla, qué se mide. | **En detalle / In detail** + **Datos / Data** |
| **Operario de planta, ingeniero de procesos, laboratorista** | Rangos, unidades, variables críticas, decisión binaria. | **Datos / Data** + telemetría completa |

Cada página de proceso expone las tres capas en ese orden visual.

---

## 3. Information Architecture & URL Contract

### Mapa de páginas (16 URLs en sitemap)

| # | ES (ruta) | EN (ruta) | Tipo |
|---|---|---|---|
| 1 | `/index.html` | `/en/index.html` | Inicio |
| 2 | `/procesos/recepcion.html` | `/procesos/en/reception.html` | Proceso 01/07 |
| 3 | `/procesos/pre-limpieza.html` | `/procesos/en/pre-cleaning.html` | Proceso 02/07 |
| 4 | `/procesos/limpieza-fina.html` | `/procesos/en/fine-cleaning.html` | Proceso 03/07 |
| 5 | `/procesos/peletizacion.html` | `/procesos/en/pelleting.html` | Proceso 04/07 · Hero (incluye Secado 04.2) |
| 6 | `/procesos/envasado.html` | `/procesos/en/packaging.html` | Proceso 05/07 |
| 7 | `/procesos/control-calidad.html` | `/procesos/en/quality-control.html` | Proceso 06/07 · Decision node |
| 8 | `/procesos/almacen-producto-terminado.html` | `/procesos/en/finished-product-warehouse.html` | Proceso 07/07 |
| – | `/404.html` | (bilingüe en una sola página) | Error |

**Total servido por sitemap**: 16 URLs.

### Reglas de URL (inviolables)

1. **Rutas absolutas** en HTML (`/assets/...`, `/procesos/...`, `/en/...`). El
    El soporte `file://` se eliminó en v2.2 — serví con HTTP.
2. **Slugs asimétricos entre idiomas**, pero **uno a uno** y mantenidos en una
   tabla de pairing (la de arriba). Cambiar un slug es un cambio breaking.
3. **Proceso 04 = Peletización y Secado**: el Secado **no** tiene URL propia
   desde v1.0 de este spec. Vive como `Fase 04.2` dentro de
   `/procesos/peletizacion.html`.
4. **`404.html`** es bilingüe en una sola página (la lógica del servidor
   estático no conoce el idioma del cliente en la respuesta de error).
5. **Las rutas que no existan** deben apuntar a `/404.html` o ser capturadas
   por el comportamiento default del servidor (404 nativo).

### Profundidad de carpetas

```
.
├── index.html
├── 404.html
├── robots.txt
├── sitemap.xml
├── SPEC.md                      ← este archivo
├── README.md                    ← guía operativa humana
├── assets/
│   ├── css/styles.css
│   ├── js/app.js
│   └── img/   (favicon.svg, og-image.png, *.svg)
├── en/index.html
└── procesos/
    ├── {slug}.html              (ES)
    └── en/{slug-en}.html        (EN)
```

**Regla de oro**: nadie crea nuevas carpetas sin actualizar este spec,
`sitemap.xml` y `README.md`.

---

## 4. i18n Contract

### Lo que debe estar traducido

- Contenido textual visible de cada página (h1, párrafos, tablas, captions).
- `<html lang="es">` o `<html lang="en">` según corresponda.
- `<title>` y `<meta name="description">`.
- `og:title`, `og:description`, `og:locale`.
- JSON-LD: nombres `name` y descripciones en el idioma de la página.
- Etiquetas ARIA (`aria-label`).
- Schema.org `inLanguage`.

### Lo que NO se traduce

- Nombres de clases CSS.
- Nombres de archivos relativos en `href`/`src`.
- Slugs de URL (la asimetría ES/EN es intencional).
- En `.telemetry`, las unidades técnicas (`°C`, `min`, `kg`, `%`, `rpm`, `g/g`,
  `%`, etc.) **no** se traducen; los `<caption>`, los nombres de parámetros y
  el header de la columna sí.

### Glosario de términos固定 (no se renegocia sin discusión)

| ES | EN |
|---|---|
| Planta de Semillas Peletizadas | Pelleted Seed Plant |
| Instituto de Investigación del Tabaco | Tobacco Research Institute |
| Peletización | Pelleting |
| Secado (subproceso 04.2) | Drying |
| Bombo peletizador | Pelleting drum |
| Turbina de secado | Drying turbine |
| Polímero | Polymer |
| Fungicida | Fungicide |
| Arcilla inerte | Inert clay |
| Almacenero | Warehouse operator |
| Operario de planta | Floor operator |
| Especialista de laboratorio | Lab specialist |
| Lote | Lot |
| Trazabilidad bidireccional | Bidirectional traceability |
| Nodo de decisión | Decision node |
| Proceso hero | Hero process |
| En simple | In simple |
| En detalle | In detail |
| Datos | Data |

### Mecánica del toggle de idioma

Implementado en `assets/js/app.js`:

- El header contiene `<nav class="lang-toggle">` con dos `<a data-lang="es|en">`.
- Al cargar, el script detecta el idioma actual por path y aplica
  `aria-current="true"` + `.is-active` al botón correspondiente.
- Los href siguen siendo absolutos (`/index.html`, `/en/index.html`) para que
  un cambio de idioma sea predecible desde cualquier profundidad.

---

## 5. Functional Requirements (Features observables)

| ID | Requisito | Evidencia verificable |
|---|---|---|
| F-01 | Bilingual toggle funciona en cualquier página | Click en `data-lang="en"` desde `/procesos/peletizacion.html` llega a `/procesos/en/pelleting.html`. |
| F-02 | Toggle marca idioma activo con `aria-current="true"` | DOM al cargar página ES contiene `nav.lang-toggle a[data-lang="es"][aria-current="true"]`. |
| F-03 | Video placeholder clickable y accesible | `.video-frame` tiene `role="button"`, `tabindex="0"`, responde a click y a Enter/Space. Al integrar `<video>` real, se quita `role` y `tabindex`. |
| F-04 | Skip link funcional al `<main>` | Primer `Tab` muestra "Saltar al contenido principal / Skip to content" (inyectado por JS si no existe). |
| F-05 | Smooth scroll en anchors `#…` | Click en un CTA con `href="#pipeline"` hace scroll suave. |
| F-06 | Reveal-on-scroll progresivo | Elementos con `data-reveal` aparecen con stagger reducido (≤ 6 elementos). Sin JS o con `prefers-reduced-motion`, todas las cards son visibles inmediatamente. |
| F-07 | Link entre procesos consecutivos | Cada proceso tiene `<a class="next-step">` apuntando al paso siguiente en su idioma. |
| F-08 | Servir con HTTP (file:// deprecado) | El sitio requiere un servidor HTTP para funcionar correctamente (sprite SVG externo, enlaces, Open Graph). Usá `python -m http.server 8000`, Live Server de VSCode, o cualquier HTTP server. El soporte `file://` se eliminó en v2.2. |

---

## 6. Non-Functional Requirements

### Accesibilidad (WCAG 2.1 AA)

- **Idioma**: `<html lang>` correcto en cada página.
- **Jerarquía de headings**: h1 único por página; h2 por sección; h3 anidado bajo h2.
- **Color y contraste**: los textos pequeños sobre fondos `--cream`/`--ink` usan
  ratios que cumplen AA. Las variables `--ink`, `--ink-soft`, `--tobacco-700`
  y `--seed` cumplen ≥ 4.5:1 para texto normal.
- **Teclado**: todo interactivo es accesible con Tab + Enter/Space. Foco
  visible (`:focus-visible` definido en `styles.css`).
- **Movimiento reducido**: `prefers-reduced-motion: reduce` desactiva reveal y
  smooth scroll.
- **Etiquetas**: microcopy en `<caption>` para tablas de telemetría; cada
  `.video-frame` tiene `aria-label`.

### SEO

- Cada página expone `title`, `description`, `canonical`, dos `hreflang` (es/en),
  Open Graph (6 campos) y Twitter Card (4 campos).
- `sitemap.xml` válido y referenciado desde `robots.txt`.
- `og:image` por defecto es `/assets/img/og-image.png` (1200 × 630 px).
- `og:url` y `og:domain` son rutas relativas — al desplegar, hay que
  reemplazarlas por absolutas (ver sección §10 checklist).

### Performance

- Sin frameworks JS. `assets/js/app.js` se mantiene pequeño y sin dependencias
  externas (actualmente alrededor de 3 KB sin minificar; objetivo: no superar
  esa cifra al añadir interacciones).
- Fonts vía Google Fonts con `preconnect` + `display=swap`.
- Imágenes OG en PNG optimizado; SVGs inline sólo cuando son < 1 KB, si no
  archivo externo.
- Sin Tailwind, SCSS, ni cualquier bundler.

### Seguridad

- Sin formularios. Sin almacenamiento local. Sin cookies. Sin contenido embebido
  de terceros fuera de Google Fonts.
- `Content-Security-Policy` no es necesario mientras no haya scripts externos.

---

## 7. Design System Contract

### Paleta (variables CSS en `:root`)

| Variable | Valor | Uso principal |
|---|---|---|
| `--cream` | `#faf6ee` | Fondo papel principal |
| `--ink` | `#0c1f17` | Texto principal |
| `--ink-soft` | derivado | Texto secundario |
| `--tobacco-700` | `#1f4a36` | Verde tobacco profundo (acentos de fondo) |
| `--seed` | `#c19a3b` | Acento dorado (iconos, énfasis) |

Cualquier token nuevo se agrega en `styles.css` con un comentario explicando su
rol y se referencia en este spec.

### Tipografía

| Familia | Variable de stack | Uso |
|---|---|---|
| **Fraunces** | (display serif) | Títulos h1/h2, hero, números destacados |
| **Inter** | (sans body) | Texto corrido, párrafos |
| **JetBrains Mono** | (mono) | `eyebrow`, captions de tabla, `next-step__label`, telemetría |

Ninguna fuente se sirve por archivo local; vienen de Google Fonts.
Fraunces e Inter se cargan en tres pesos (400/500/600); JetBrains Mono en dos
(400/500).

### Inventario de componentes (clases BEM-ish)

- **Chrome**: `.topbar`, `.brand`, `.brand__mark`, `.brand__text`, `.lang-toggle`.
- **Layout**: `.container`, `.section`, `.section--soft`, `.footer`,
  `.footer__grid`, `.footer__bottom`.
- **Hero / proceso hero**: `.hero`, `.hero__grid`, `.hero__title`,
  `.hero__lede`, `.hero__cta`, `.proc-hero`, `.proc-hero--accent`,
  `.proc-hero__back`, `.proc-hero__lede`, `.proc-hero__meta`.
- **Pipeline**: `.timeline`, `.timeline__item`, `.timeline__item--accent`,
  `.timeline__icon--decision`, `.timeline__order`, `.timeline__title`,
  `.timeline__role`, `.timeline__arrow`.
- **Profundidad**: `.depth-grid`, `.depth-grid--tight`, `.depth-block`,
  `.depth-block__label`, `.depth-block--simple`, `.depth-block--detail`,
  `.depth-block--data`, `.depth-block--critical`.
- **IO / datos**: `.io-grid`, `.io__heading`, `.io__list`, `.io__item`,
  `.io__item--out`, `.telemetry`.
- **Stats / badges**: `.stats`, `.stat`, `.stat__num`, `.stat__suffix`,
  `.badges`, `.badge`, `.badge__dot`.
- **Botones / meta_chips**: `.btn`, `.btn--primary`, `.btn--ghost`,
  `.meta-chip`, `.meta-chip--accent`, `.meta-chip--ink`.
- **Continuidad**: `.next-step`, `.next-step__label`, `.next-step__title`,
  `.next-step__arrow`.
- **Video**: `.video-frame`, `.video-frame__inner`, `.video-frame__play`,
  `.video-frame__title`, `.video-frame__hint`, `.video-frame__corner`.

**Regla**: cada clase nueva se documenta aquí; los componentes sin doc se
consideran deuda.

---

## 8. Asset & Media Contract

### Tipos permitidos

- **Iconos / ilustraciones**: SVG, preferentemente inline si < 1 KB, si no en
  `assets/img/{nombre}.svg`.
- **Favicon**: `assets/img/favicon.svg`.
- **Open Graph image**: `assets/img/og-image.png` (1200 × 630 px). Antes de
  publicar, reemplazable por una versión específica del proyecto.
- **Video institucional** (futuro): `assets/video/intro.mp4` (preferentemente)
  y/o `intro.webm` como fallback. Reemplaza el `.video-frame` placeholder en
  `/index.html` y `/en/index.html`.

### Lo que no se hace

- **No** se introducen fuentes custom locales.
- **No** se introducen imágenes pesadas (> 400 KB) sin pensar primero en SVG o
  poster.
- **No** se descargan trackers de terceros.

---

## 9. Page-Level Specifications (Fichas por página)

### 9.1 Inicio ES (`/index.html`) e Inicio EN (`/en/index.html`)

- **Propósito**: presentar la Planta, el pipeline completo y dar entrada al
  flujo.
- **Bloques obligatorios**:
  1. `<header class="topbar">` con brand + lang toggle.
  2. `<section class="hero">` con `hero__grid` (copy + video-frame).
  3. `<section class="section section--soft" id="pipeline">` con el timeline
     de 7 procesos.
  4. `<section class="section">` con split explicativo y stats.
  5. `<section class="section section--soft">` con mission-block.
  6. `<footer class="footer">` con 4 columnas.
- **Criterios de aceptación**:
  - [ ] JSON-LD con `WebSite` + `Organization` en el idioma de la página.
  - [ ] Timeline lista **exactamente 7** procesos; peletización y control de
        calidad con `.timeline__item--accent`.
  - [ ] `.video-frame` con `role="button"`, `tabindex="0"`, `aria-label` y
        textos en el idioma correcto.
  - [ ] CTAs del hero: `#pipeline` (interno) y `/procesos/peletizacion.html`
        (o su gemelo EN).
  - [ ] Footer enlaza a los 4 procesos principales + idiomas + atribución
        de la tesis.

### 9.2 Páginas de proceso (ES + EN) — patrón general

Cada uno de los 7 procesos sigue este esqueleto. Sólo cambia el contenido.

- **Propósito**: explicar un paso del pipeline con sus entradas, sus salidas y
  la telemetría esperada.
- **Bloques obligatorios**:
  1. `<header class="topbar">` (igual al home, menos acento de marca).
  2. `<section class="proc-hero">` con back-link, eyebrow `Proceso NN / 07`,
     h1, `proc-hero__lede` y `proc-hero__meta` con chips.
  3. `<div class="container proc-body">` con:
     - `.depth-grid` que contiene `.depth-block--simple` y `.depth-block--detail`.
     - `.io-grid` con entradas y salidas.
     - `.depth-block--data` con `<table class="telemetry">`.
     - (sólo para Peletización) sub-sección Fase 04.2 · Secado.
     - `<a class="next-step">` apuntando al proceso siguiente.
  4. `<footer class="footer">` (igual al home).
- **Criterios de aceptación genéricos**:
  - [ ] Eyebrow dice `Proceso NN / 07` o `Process NN / 07`. NN ∈ `{01..07}`.
  - [ ] `<h1>` único con el nombre del proceso.
  - [ ] Al menos un `.depth-block--simple` y un `.depth-block--detail`.
  - [ ] `.io-grid` con entradas y salidas en `<span class="io__item">` /
        `<span class="io__item--out">`.
  - [ ] Tabla `.telemetry` con `<caption>` y `<thead>` (`scope="col"` en
        próximas mejoras, hoy opcional pero recomendado).
  - [ ] `next-step` apunta al slug correcto.
  - [ ] `hreflang` apunta a su gemelo EN/ES.

#### 9.2.1 Proceso 01 / 07 — Recepción (`recepcion.html` / `reception.html`)

- **Acento**: `.meta-chip--ink` "Almacén de Materia Prima" / "Raw Materials
  Warehouse". Es el origen del grafo de trazabilidad.
- **next-step →** `/procesos/pre-limpieza.html`.

#### 9.2.2 Proceso 02 / 07 — Prelimpieza (`pre-limpieza.html` / `pre-cleaning.html`)

- **Rol**: Operario de planta · Limpieza.
- **next-step →** `/procesos/limpieza-fina.html`.

#### 9.2.3 Proceso 03 / 07 — Limpieza Fina (`limpieza-fina.html` / `fine-cleaning.html`)

- **Rol**: Operario de planta · Limpieza.
- **Precondición crítica**: si no pasa, el bombo se bloquea. Esta precondición
  debe aparecer explícita en la página.
- **next-step →** `/procesos/peletizacion.html`.

#### 9.2.4 Proceso 04 / 07 — Peletización y Secado (`peletizacion.html` / `pelleting.html`)

- **Acento visual**: `.proc-hero--accent` y `.timeline__item--accent` en el
  home.
- **Bloques adicionales OBLIGATORIOS**:
  - [ ] `.depth-block--critical` explicando por qué este paso es el corazón
        del pipeline y no puede saltarse.
  - [ ] Sub-sección `Fase 04.2 · Secado` con su propio `.proc-hero--accent`,
        `.depth-grid`, `.io-grid` y `.telemetry`.
- **next-step →** `/procesos/envasado.html`.

#### 9.2.5 Proceso 05 / 07 — Envasado (`envasado.html` / `packaging.html`)

- **Rol**: Operario de planta.
- **next-step →** `/procesos/control-calidad.html`.

#### 9.2.6 Proceso 06 / 07 — Control de Calidad (`control-calidad.html` / `quality-control.html`)

- **Acento visual**: `.timeline__item--accent` y `.timeline__icon--decision`
  en el home. Es el **nodo de decisión**: o se libera al almacén o se
  rechaza el lote.
- **Bloques adicionales**:
  - [ ] Tabla de telemetría del laboratorio.
  - [ ] Criterio binario aprobación/rechazo explícito en `.depth-block--detail`.
- **next-step →** `/procesos/almacen-producto-terminado.html`.

#### 9.2.7 Proceso 07 / 07 — Almacén de Producto Terminado

  - **Rol**: Almacenero · Almacén final.
  - **Bloques adicionales**: activación de la **trazabilidad bidireccional**
    en la `.io-grid` de salidas.
  - **No tiene `next-step`**: es el último proceso.

### 9.3 Error (`/404.html`)

- **Propósito**: atrapar enlaces rotos o rutas inválidas con un mensaje
  bilingüe.
- **Bloques obligatorios**:
  - [ ] Header y footer mínimos (topbar + footer .
  - [ ] Mensaje en ES y EN en la misma página.
  - [ ] Botón primario "Volver al inicio · Back home".
  - [ ] Botón fantasma a `/en/index.html`.
- **Criterios de aceptación**:
  - [ ] La página responde 404 nativo del servidor cuando se sirve con
        `python -m http.server` o cualquier host estático.
  - [ ] Las rutas a assets son absolutas (`/assets/...`).

---

## 10. Validation Checklist (Definition of Done)

Antes de cerrar cualquier cambio en el sitio, correr esta lista. Si algo
falla, el cambio no está completo.

### 10.1 Contenido y formato

- [ ] No hay caracteres CJK (japonés, chino, coreano) flotantes en ningún
      archivo HTML.
- [ ] No hay cadenas placeholder sin reemplazar (`Lorem ipsum`, `TODO`,
      `XXX`).
- [ ] Cada proceso describe las tres capas (simple / detalle / datos).

### 10.2 i18n

- [ ] Para cada cambio de contenido en ES, existe el mirror EN y viceversa.
- [ ] `<html lang>` correcto en cada página.
- [ ] Los slugs ES/EN siguen la tabla §3.

### 10.3 SEO por página

- [ ] `<title>` único y descriptivo.
- [ ] `<meta name="description">` ≥ 120 caracteres y describe la página.
- [ ] `<link rel="canonical">` con ruta absoluta.
- [ ] `<link rel="alternate" hreflang="es">` y `<link rel="alternate"
      hreflang="en">`.
- [ ] `og:title`, `og:description`, `og:type`, `og:url`, `og:image`,
      `og:locale`.
- [ ] `twitter:card`, `twitter:title`, `twitter:description`,
      `twitter:image`.

### 10.4 SEO a nivel sitio

- [ ] `sitemap.xml` lista exactamente las **16 URLs reales** sin urls que
      devuelvan 404.
- [ ] `robots.txt` apunta al sitemap.
- [ ] `404.html` existe y maneja enlaces válidos al home en ambos idiomas.
- [ ] JSON-LD válido en `/index.html` y `/en/index.html` (WebSite +
      Organization, en el idioma correcto).

### 10.5 Accesibilidad

- [ ] Primer `<h1>` único por página; jerarquía sin saltos.
- [ ] Tablas `.telemetry` con `<caption>`.
- [ ] El skip link funciona (primer `Tab` lo enfoca).
- [ ] Con `prefers-reduced-motion: reduce`, no hay reveal ni smooth scroll.
- [ ] El toggle de idioma muestra `aria-current="true"` en el activo.

### 10.6 Routing y enlaces

- [ ] `next-step` en cada proceso apunta al paso siguiente correcto.
- [ ] El pie de página enumera 4 procesos + 2 idiomas + atribución.
- [ ] Todos los href dentro de `<main>` apuntan a páginas que existen.
- [ ] Cada home (`/index.html` y `/en/index.html`) muestra **exactamente 7**
      tarjetas de proceso, con **2** de ellas con clase adicional
      `.timeline__item--accent` (procesos 04 y 06). Verificable contando
      atributos `class="timeline__item"` y `class="timeline__item--accent"`
      por separado (cuenta de subcadena libre da falsos positivos — ver §15).
- [ ] Los árboles DOM de `/index.html` y `/en/index.html` son
      **estructuralmente idénticos**: mismo número y orden de secciones
      principales, mismo número de timeline cards, mismo número y orden de
      `.stats`. Sin este invariante, migraciones a mano pueden causar drift
      ES↔EN que sólo se detecta después de publicar.
- [ ] Cada par de páginas ES↔EN de proceso (`procesos/{slug}.html` vs
      `procesos/en/{slug-en}.html`, los 7 pares) tiene regiones
      **estructuralmente idénticas** en `.depth-grid`, `.io-grid`,
      `.telemetry` y `.next-step`. Misma cantidad de `.depth-block`, mismas
      filas en la tabla de telemetría, mismo `next-step href` apuntando al
      siguiente proceso en su idioma. Drift aquí es más difícil de detectar
      visualmente que en los homes.

### 10.7 Despliegue

- [ ] Si cambia el dominio, `example.com` está reemplazado en `sitemap.xml`,
      `robots.txt`, JSON-LD, README.
- [ ] La imagen OG (`assets/img/og-image.png`) sigue siendo 1200 × 630 px.

---

## 11. Change Protocol (cómo modificar el spec)

1. **Detectar el tipo de cambio**:
   - ¿Cambia contenido de un proceso? → actualizar ambas versiones
     (ES + EN) + `sitemap.xml` si cambia slug.
   - ¿Cambia paleta, tipografía o aparece un componente nuevo? → actualizar §7
     y, si la clase ya existe, **migrar su uso antes de declarar deprecated**.
   - ¿Se agrega un proceso? → actualizar §3, §9, `sitemap.xml`,
     `README.md`, ambos homes.
   - ¿Se retira un proceso? → mismo path, pero invirtiendo.
   - ¿Cambia el dominio? → actualizar `example.com` en archivos afectados +
     este spec (§10.7).

2. **Aplicar el cambio en código** siguiendo las reglas del spec.

3. **Correr la Checklist §10** completa antes de cerrar.

4. **Actualizar [`CHANGELOG.md`](./CHANGELOG.md)** con versión, fecha y resumen.

5. **No commitear** sin pasar 1–4.

---

## 12. Glosario Complementario (operativo)

Términos que se usan en microcopy fijo y deben quedar consistentes:

- **"Sitio informativo · no transaccional"** (footer): nunca cambiar la forma
  ni agregar CTA aquí.
- **"Tres niveles de profundidad"** (mission-block): eslogan del modelo de
  tres capas. No reformular a "dos niveles" sin discutir.
- **"El recorrido de un lote" / "A lot's journey"**: eyebrow del hero.
- **"Video institucional · próximamente"** mientras el video no exista.
- **"REC · 02:30"**: badge visual del `.video-frame` placeholder.
- **"Continúa con el paso N" / "Continue with step N"**: microcopy del
  `.next-step__label`.

---

## 13. Change Log

Ver [`CHANGELOG.md`](./CHANGELOG.md) para el historial completo de versiones.

---

## 14. Trabajo pendiente (PEND-*) y Bugs abiertos (BUG-*)

Esta sección sirve de backlog vivo. Cada ítem tiene un ID, una prioridad y el
**motivo** por el que no se cerró junto con el resto del spec. Los BUG-*
representan contradicciones activas entre el código y el spec que hay que
corregir antes de cerrar cualquier v2.x.

### Backlog

| ID | Tipo | Prioridad | Título | Criterio de cierre |
|---|---|---|---|---|
| **PEND-001** | Mejora | 🟡 Medium | Reemplazar `video-frame` por `<video>` real | Cuando existan `assets/video/intro.mp4` (y `.webm`) y los `<div class="video-frame">` de `/index.html` y `/en/index.html` se reemplacen por elementos `<video>` con `poster` y `preload="metadata"`. Mientras tanto el placeholder sigue siendo accesible. |
| **PEND-002** | Despliegue | 🟡 Medium | Reemplazar dominio placeholder `example.com` | Correr `python scripts/replace-domain.py tudominio.com` para reemplazar `https://zarakiomg96-lang.github.io/pelletized-seed-plant` y las URLs relativas de og:url/og:image en todas las páginas. Sin argumento hace dry-run. Creado en v3.1. |
| **PEND-003** | Mejora | 🟢 Low | Imagen OG específica del proyecto | Reemplazar `assets/img/og-image.png` (placeholder generado) por una imagen real (1200 × 630 px) con logo y una foto de la planta. |
| **PEND-004** | Funcional futuro | ⚪ Parked | Sub-fases navegables (tabs / acordeón / anclas) dentro de procesos con varias fases | La Opción 3 del rediseño de Secado (tabs dentro de Peletización) **no** está escrita al spec — §9.2 sólo describe el patrón actual con `depth-grid` + `io-grid` + `telemetry`. Cualquier exploración futura debe empezar escribiendo la sección §9.2 correspondiente antes de codear. Se mantiene como referencia, sin prioridad. |
| **PEND-005** | Modo oscuro | ⚪ Parked | Dark mode con toggle manual | Descartado en §1 Non-Goals. Mantenido en backlog como referencia a futuro. No se trabaja hasta que se levante el Non-Goal. |
| **PEND-006** | PWA | ⚪ Parked | Service Worker + manifest | Descartado en §1 Non-Goals. Mantenido en backlog como referencia a futuro. |
| **BUG-002** ✅ Closed | Bug | 🟡 Medium | ~~`404.html` incumple §10.3 — description corta + canonical ausente + OG/Twitter ausentes~~ | **Cerrado en v1.4** — `404.html` reescrito: description extendida a >120 chars (bilingüe, menciona el pipeline), `<link rel="canonical" href="/404.html">` agregado, 6 meta `og:*` agregados, 4 meta `twitter:*` agregados. Verificable: re-correr `python scripts/spec-lint.py` → grupo 5 (per-page meta) y grupo 12 con 0 FAIL para `404.html`. |
| **BUG-003** ✅ Closed | Bug | 🟡 Medium | ~~5 process pages EN tienen description < 120 chars~~ | **Cerrado en v1.4** — descripciones EN de `procesos/en/{reception, pre-cleaning, fine-cleaning, packaging, finished-product-warehouse}.html` extendidas con una frase técnica adicional (audiencia, restricción biológica o métrica clave). Cada descripción ahora ≥120 chars. Verificable: re-correr lint → grupo 5 sin FAIL de longitud para esas 5 rutas. |
| **BUG-004** ✅ Closed | Bug | 🟡 Medium | ~~`procesos/limpieza-fina.html` ES tiene description de 119 chars~~ | **Cerrado en v1.4** — description de `procesos/limpieza-fina.html` extendida con el fragmento "aplicado en el bombo" para cruzar el umbral de §10.3. Verificable: re-correr lint → grupo 5 sin FAIL para esa ruta. |
| **BUG-001** ✅ Closed | Bug | 🟡 Medium | ~~Cualquier referencia residual a `/08` en formato `NN/08`~~ | **Cerrado en v1.1.2** — tres instancias en `<meta>` tags de `procesos/recepcion.html` reemplazadas de la forma `NN/08` por `NN/07` (numeración obsoleta de la era pre-fusión, hoy `NN/07` consistente con §3). Comprobado en v1.2 con grep BUG-001 automatizado: 0 hits en `*.html`, `*.md`, `*.xml`. La regla general queda en §15.2.C como heurística de validación para futuros PEND/BUG. |

### Cómo añadir un nuevo ítem

1. Asignar ID correlativo (`PEND-00N` o `BUG-00N`).
2. Ponerle prioridad 🟢/🟡/🔴 o ⚪ Parked.
3. Fijar criterio de cierre medible (qué pasa al cerrarlo).
4. Si el ítem contradice al spec, marcar explícitamente "Rompe §X.Y" y
   resolverlo como BUG antes de cualquier release.
5. Bumpear `SPEC.md` con la entrada nueva en [`CHANGELOG.md`](./CHANGELOG.md).

### Cómo cerrar un ítem

1. Resolver la causa que lo originó (código o spec).
2. Pasar la Checklist §10 completa.
3. Mover la fila a "Closed" en una subsiguiente revisión del backlog (o
   borrarla si es de baja utilidad histórica).

---

## 15. Cómo usar este spec (Workflow SDD)

Para cualquier cambio, primero identificar el **tipo**, después seguir el
camino correspondiente.

### 15.1 Tipos de cambio y versionado

| Tipo | Ejemplos | Versión |
|---|---|---|
| **Fidelidad** (typo, link roto, mejora de contraste, ajuste de microcopy, fix de aria) | "Cambié `--seed-dark` por `--tobacco-700` en `.depth-block__label`"; "Corregí `via los整机` por `las sembradoras` en index.html" | Bumpear `v1.x` |
| **Alcance estricto** (nuevo proceso, nueva página, nuevo idioma, nueva sección de spec, ruptura de contrato) | "Agrego proceso 08 al pipeline, pasando a 16 procesos"; "Agrego sub-página de glosario en `/glosario.html`" | Bumpear `v2.x` |
| **Estructural-secundario** (nuevas tablas o checklists en spec, sin cambio de contrato ni de alcance de usuario) | "Añado §14 trabajo pendiente"; "Añado §15 workflow"; "Añado checklist §10.X" | Bumpear `v1.x` con nota explícita en el change log |

> Borderline: v1.1 del 2026-07-22 (donde estamos) cae en **Estructural-secundario** —
> añadimos §14/§15 y un nuevo BUG- pero no cambió el contenido visible al usuario.

### 15.2 Workflow por tipo

#### A. Cambios de fidelidad / estructurales-secundarios

1. Localizar la sección aplicable (§7, §9, §10, §12 según el área).
2. Aplicar el cambio en código (HTML/CSS/JS) **y/o** en este spec.
3. Correr la Checklist §10 completa.
4. Bumpear `v1.x` en [`CHANGELOG.md`](./CHANGELOG.md) con una línea clara.

#### B. Cambios de alcance

1. Localizar requisitos en §1 (Non-Goals), §3 (URLs), §5 (Funcionales), §6
   (No funcionales), §9 (Ficha de página) y §14 (backlog).
2. Si es un nuevo idioma o proceso: aprobar el cambio **fuera de este spec**.
3. Actualizar **en este orden**: §3 → §9 (nueva ficha) → `sitemap.xml` →
   README → homes ES/EN → páginas de proceso ES/EN → este spec.
4. Correr §10 completa.
5. Bumpear `v2.x` en [`CHANGELOG.md`](./CHANGELOG.md).

#### C. Bugs abiertos (BUG-*)

1. Localizar el BUG-* en §14 y leer el criterio de cierre.
2. Escribir primero el test o comando de verificación que lo demuestra
   (idealmente un one-liner en Python o un grep reproducible — ver §15.3).
3. Aplicar el fix mínimo en código.
4. Correr §10 completa **y** el comando del paso 2.
5. Cerrar la fila de §14 explícitamente (no borrarla: dejarla visible
   en el change log como `BUG-00N cerrado en vX.Y por <commit>`).

### 15.3 Cómo escribir un validador para un BUG-*

Para evitar falsos positivos, los validadores que escribas **deben**:

- Usar regex de atributo completo para contar clases CSS. Ejemplo:
  `re.findall(r'\bclass="timeline__item(?:\s+timeline__item--accent)?"', text)`
  en vez de `text.count('timeline__item')` (subcadena).
- Parsear `sitemap.xml` con `xml.etree.ElementTree` y contar URLs por la
  `namespace` real (`{http://www.sitemaps.org/schemas/sitemap/0.9}loc`).
- Reportar siempre PASS/FAIL explícito por check, no sólo el resumen.

Pegar el validador usado en el comment de cada PEND/BUG en §14 para que la
próxima persona pueda revalidar sin reinventarlo.

### 15.3.1 Validador ejecutable: `spec-lint.py`

El detalle completo de cada grupo de checks (items 1–27) y su evolución
se ha movido a [`docs/GATE-CONTRACT.md`](./docs/GATE-CONTRACT.md) para
mantener este spec enfocado en el contrato.

### 15.3.2 Wrappers portables del gate (`scripts/check-spec.*`)

El gate se puede invocar de cuatro formas equivalentes, el resultado siempre
es el mismo exit code:

| Forma | Cuándo usarla |
|---|---|
| `python scripts/spec-lint.py` | Default. Tabla humana + multi-line summary. |
| `python scripts/check-spec.py` | Wrapper Python recomendación general. Imprime tabla humana + un `[check-spec] exit` multi-línea al final. |
| `python scripts/check-spec.py --quiet` | IDE / editor que sólo necesita un booleano verde/rojo. Captura stdout/stderr del gate y emite **una sola línea**. |
| `python scripts/check-spec.py --json` | CI / pipe machine-readable. Forward al gate, **no** agrega el resumen humano, salida válida como JSON.parse. |

Shims por shell para usar el wrapper sin tipear el path completo:

```bash
bash scripts/check-spec.sh          # POSIX / git-bash / WSL
scripts\check-spec.bat               # Windows cmd / PowerShell
```

Snippet para `.git/hooks/pre-commit` (cuando el proyecto se versione):

```bash
#!/usr/bin/env bash
set -e
exec python scripts/check-spec.py --quiet
```

Reglas operativas:

- `--quiet` y `--json` son exclusivos por diseño: en cualquiera de los dos
  modos, el wrapper **no** emite la multi-línea de resolución posterior.
- `--json` siempre adelante al gate sin pre/post-procesar; el JSON es lo
  que produce `spec-lint.py --json` directamente.
- El wrapper no atrapa excepciones de `subprocess`: si `spec-lint.py`
  falta, el traceback de Python queda visible al usuario (loud fail,
  acceptable for dev tooling).

### 15.4 Cómo cerrar la §10 sin contradecir el spec

§15.2.C.4 obliga a correr §10 después del fix de un BUG-*. Si §10 descubre
el BUG-, es legítimo cerrar el ciclo así:

1. Anotar el BUG en §14 (BUG-N).
2. Bumpear `v1.x` (no `v2.x`: cerrar un BUG no es cambio de alcance).
3. Aplicar el fix correspondiente.
4. Re-correr §10 hasta que pase.
5. Cerrar la fila de §14 según §15.2.C.5.

> El spec **no se commitea** con BUGs abiertos en estado distinto de **Parked**
> o **Closed**. Los PEND-* pueden commitearse sin cerrarlos; los BUG-*
> activos, no.

---

