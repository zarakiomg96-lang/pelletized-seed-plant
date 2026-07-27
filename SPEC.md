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
   rewrite de `file://` vive en `assets/js/app.js` y es best-effort.
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
| F-08 | `file://` rewrite best-effort | Si alguien abre `index.html` con doble click, los href absolutos se reescriben a relativos. `assets/js/app.js` re-encamina cualquier `a[href^='/']` al cargar; los href nuevos cualifican automáticamente sin listas explícitas. |

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
  - [ ] Eyebrow dice `Proceso NN / 07` o `Process NN / 07`. NN ∈ {01..07}.
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

4. **Actualizar Change log (§13)** con versión, fecha y resumen.

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

| Versión | Fecha | Resumen |
|---|---|---|
| v1.0 | 2026-07-22 | Spec inicial. Refleja el estado tras fusionar Secado en Peletización (pipeline de 7 procesos, 16 URLs). |
| v1.0.1 | 2026-07-22 | Correcciones de fidelidad: removida clase fantasma `.depth-block--ink`, ajustado el presupuesto de pesos de JetBrains Mono, reescrita la regla F-08, quitada la métrica inventada del tamaño de `app.js`, corregido "Glossário" → "Glosario", añadido `focus-visible`. |
| v1.1   | 2026-07-22 | Añadida §14 Trabajo pendiente con PEND-001..006 y BUG-001. Cierra validaciones del SDD: trazabilidad de trabajo diferido y de bugs abiertos que contradicen el spec. **Bug detectado por validador Python que contrastaba `SPEC.md §3` contra el filesystem.** |
| v1.1.1 | 2026-07-22 | Cierre de auditoría del code-reviewer-minimax-m3: BUG-001 grep anclado a `\b0?\d{1,2}\s*/\s*08\b` (evita falsos positivos en URLs/dates/paths), PEND-002 page count corregido a 17 (16 sitemap + 404), §10.6 invariante DOM estructural extendido a los 7 pares ES↔EN de proceso. |
| v1.1.2 | 2026-07-22 | **BUG-001 cerrado.** Tres instancias de contador obsoleto en `procesos/recepcion.html` (`<meta name="description">`, `<meta property="og:description">` y `<meta name="twitter:description">`) reemplazadas de la forma `NN/08` por `NN/07` (numeración obsoleta de la era pre-fusión). Validación: `grep -rn -E '\b0?\d{1,2}\s*/\s*08\b'` → 0 hits. La regla general queda indizada en §15.2.C para auditorías futuras. |
| v1.2   | 2026-07-22 | **`spec-lint.py` añadido** (raíz del proyecto). Ejecuta la Checklist §10 entera en 12 grupos de checks con `EXIT 0/1` y modo `--json`. §15.3.1 referencia el script y enumera su cobertura. Cambio **Estructural-secundario** (tooling nuevo sin cambio de contenido ni de contrato visible al usuario). |
| v1.3   | 2026-07-22 | `spec-lint.py` endurecido y **BUG-002/003/004 descubiertos por el script**. Fixes del script: (a) `to_posix()` aplicado en `check_per_page_meta` para el chequeo de `<html lang>` (corrige falsos positivos de path Windows), (b) detección de placeholders con regex word-bounded (`\bTODO\b` en vez de substring, porque "todo" es palabra común en español), (c) `count_in_section` simplificado a `int`, (d) regex de `prefers-reduced-motion` acepta `:reduce` o `:no-preference` (ambos gatean reveal). Tras los fixes el script corre 211 PASS / 8 FAIL; los 8 FAIL son **genuinos del codebase** y se documentan como BUG-002 (`404.html`: desc corta + canonical ausente + OG/Twitter ausentes), BUG-003 (5 EN process pages con desc corta) y BUG-004 (limpieza-fina ES con 119 chars, al borde) arriba. Cambio **Estructural-secundario** con descubrimiento accidental de bugs reales — primer caso de "finding-driven validation" del proyecto gracias al gate ejecutable. |
| v1.4   | 2026-07-22 | **BUG-002/003/004 cerrados.** Aplicados 7 edits de código que el gate `spec-lint.py v1.3` había detectado. (1) `404.html` reescrito completo: description bilingüe extendida a >120 chars, `<link rel="canonical" href="/404.html">` agregado, 6 meta OG y 4 meta Twitter Card replicados del patrón de los homes. (2) Descripciones EN de `procesos/en/{reception, pre-cleaning, fine-cleaning, packaging, finished-product-warehouse}.html` extendidas con una frase técnica cada una (audiencia, restricción biológica o métrica clave del proceso). (3) Description ES de `procesos/limpieza-fina.html` extendida con "aplicado en el bombo". Resultado: `python spec-lint.py` corre con **exit 0** (211 PASS / 0 FAIL). El gate es por primera vez verde puro. §14 marca los tres ítems como `Closed`. Cambio **Fidelidad** (cierre de BUG- sin contrato nuevo). |
| v1.5   | 2026-07-22 | **Drift detector de contenido ES↔EN** añadido al gate como grupo 13. `TERM_PAIRS` con 22 equivalencias técnicas del glosario §4; `check_content_drift()` itera los 7 pares ES↔EN de proceso, extrae `<meta name="description">` de cada lado y verifica que al menos un término del glosario aparezca en AMBAS. Reporta `shared=[…]` y `EN-only=[…]` para debugging. Cierra el invariante estructural de §10.6 con un invariante de **contenido**. §15.3.1 cobertura lista actualizada. Cambio **Estructural-secundario** (extiende el gate, no cambia el contrato visible al usuario). |
| v1.6   | 2026-07-22 | **Drift detector endurecido.** Cierra los nits del code-reviewer-minimax-m3 sobre v1.5: (a) `TERM_PAIRS` extendido de 22 a **29** equivalencias, agregando las 7 entradas de §4 que faltaban (`peletización/pelleting`, `arcilla inerte/inert clay`, los 3 roles: `almacenero/warehouse operator`, `operario de planta/floor operator`, `especialista/lab specialist`, y los dos conceptos: `nodo de decisión/decision node`, `proceso hero/hero process`); (b) patrones inflexivos ensanchados para tolerar flexiones: `\bsell[oa]\b` → `\bsellad?[oa]s?\b` (cubre sellado/sellada), `\bcalibrad` → `\bcalibr(?:ad[oa]|ación|ar)\b` (cubre calibración/calibrar), `\bgerminaci[óo]n\b` → `\bgermin(?:aci[óo]n|ar)\b`, `\balmac[ée]n\b` → `\balmac[ée]n\w*\b`, `\bgrafo\b` → `\bgraf(?:o|os)\b`; (c) `check_content_drift()` ahora reporta también `ES-only=[…]` además de `EN-only=[…]` (cubre asimetría ES→en al revés). Resultado: `python spec-lint.py` corre con **exit 0** (PASS/FAIL con grupos 1-13 todos verdes sobre las descripciones actuales). Cambio **Fidelidad** (refuerza el gate sin contrato nuevo). |
| v1.7.1 | 2026-07-22 | **Pequeña ampliación del regex de almacén** después de la pasada del code-reviewer-minimax-m3 sobre v1.7.
El regex `\balmac[ée]n(?:es|ado|aje|amiento)?\b` no cubría `almacenamientos` (plural abstracto) ni `almacenados` (plural del participio). Se amplía a `\balmac[ée]n(?:es|ado|ados|aje|amiento|amientos)?\b` — sigue sin overlap con el label `almacenero/warehouse operator` (la palabra `almacenero` no termina en ninguno de los sufijos listados) y ahora sí dispara en futuros edits que usen plurales. `python spec-lint.py` sigue con **exit 0** (226 PASS / 0 FAIL). Cambio **Fidelidad** (1 línea de regex, sin cambio de contrato). |
| v1.8.2 | 2026-07-22 | **Wrapper JSON limpio end-to-end** después de que el consumer-pipe test (`python scripts/check-spec.py --json | python -c "import sys,json"`) detectó un bug residual: el `print("[check-spec] running spec-lint.py ...")` al tope de `main()` se emitía al stdout **antes** del documento JSON del gate cuando `--json` se invocaba piped o redirigido (`> out.json`). Además, `capture_table` dependía sólo de `args.quiet`, dejando `--json` en modo inheritance (stdout del subprocess被她 transmitido directo al stdout del padre durante subprocess.run), así que `sys.stdout.write(stdout_text)` quedaba con string vacío. Ambos problemas cerrados de una vez: (a) banner print ahora gateado bajo `if not capture_table and not args.json:` para que jamás contamine stdout en modos machine-readable; (b) `capture_table = args.quiet or args.json` — ambos modos usan PIPE, el forward via `sys.stdout.write(stdout_text)` entrega contenido real en ambos casos. El consumer-pipe test ahora parsea correctamente: PASS=226 FAIL=0. Cambio **Fidelidad** (2 líneas de fix en el wrapper, sin cambio de contrato del gate). |
| v1.9   | 2026-07-22 | **Activación de las 4 equivalencias dormantes** detectadas por el v1.7-verifier. Edité las descripciones `<meta name="description">` (con `allowMultiple=true` en `str_replace` para hitear las 3 meta tags: description + og:description + twitter:description) en 8 archivos para que las descripciones de los 4 pares ES↔EN mencionados incluyan literalmente los términos del glosario §4 que en v1.7 estavam en la categoría "Dormantes" de §15.3.1 item 13. (a) `arcilla inerte / inert clay` activado en `procesos/peletizacion.html` (“La fórmula del bombo incluye arcilla inerte como carga para dar esfericidad.”) y `procesos/en/pelleting.html` (“The drum formula uses inert clay as filler to deliver sphericity.”). (b) `almacenero / warehouse operator` en `procesos/almacen-producto-terminado.html` (“El almacenero firma cada movimiento de ingreso y egreso contra su inventario.”) y `procesos/en/finished-product-warehouse.html` (“The warehouse operator signs off every inbound and outbound move.”). (c) `operario de planta / floor operator` en `procesos/envasado.html` (“El operario de planta opera la balanza calibrada y la selladora térmica.”) y `procesos/en/packaging.html` (“The floor operator seals the bag with the calibrated scale and the thermal sealer.”). (d) `especialista de laboratorio / lab specialist` en `procesos/control-calidad.html` (“La especialista de laboratorio firma los ensayos y la decisión de calidad final.”) y `procesos/en/quality-control.html` (“The lab specialist signs the trials and the binding quality decision.”). Verificación empírica: las 4 etiquetas pasan de 0/0 a 1+/1+ en sus pares respectivos; todas las descripciones quedan en 193–270 chars (≥120). §15.3.1 item 13 reescrito: las 29 equivalencias pasan a estar todas en la lista "Activas hoy". El gate queda con exit 0 / 226 PASS / 0 FAIL. Cambio **Contenido** (cierre del gap §4 ↔ §15.3.1 con contenido real, sin cambio de contrato). |
| v1.8.4 | 2026-07-22 | **Cleanup cosméticos del revisión sobre v1.8.3**. (a) `_silenced_stdout()` simplificado: `yield buf` → `yield`, type hint `"io.StringIO | None"` eliminado (nadie hace `as buf`), docstring reescrito para ser honesto con el contrato real (`the captured text is NOT exposed: this context only silences, never returns the buffer`). (b) `main()` duplicación reducida: introducido `ALL_CHECKS = (check_sitemap, check_inventory, ..., check_content_drift)` como tupla ordenada a nivel módulo; las 26 líneas del if/else duplicadas reemplazadas por `for fn in ALL_CHECKS: fn()`. Agregar un check 14 ahora es un append a la tupla, no dos edits en sitios separados. Salida idéntica verificada: gate exit 0, 226 PASS / 0 FAIL en los 6 canales de verificación directa y via wrapper. Cambio **Fidelidad** (refactor interno, sin cambio de contrato). |
| v1.8.3 | 2026-07-22 | **Gate silenciado al estilo JSON**. El bug real detrás del consumer-pipe test fallido NO estaba en `scripts/check-spec.py`, estaba en el gate mismo: `spec-lint.py --json` ejecutaba las 13 funciones `check_*()` con `print()` incondicional para los banners `=== 1. sitemap.xml ===` y las filas `[OK ]`/`[FAIL]`, ANTES de imprimir el documento JSON al final. El wrapper leía ese stdout ruidoso vía PIPE y lo reenviaba al consumer — `json.load` se ahogaba con las tablas previas al `{`. Fix: añadido un context manager `_silenced_stdout()` en `spec-lint.py` que redirige `sys.stdout` a un `io.StringIO` descartable mientras corren los checks (con `try/finally` para restaurar incluso ante excepción). En `main()`, si `args.json`, los 13 checks corren dentro de `with _silenced_stdout():`; en modo default corren sin envolver (comportamiento humano intacto). Solo el `json.dumps(...)` final sale al stdout real. Resultado verificado en 6 canales: (a) `python spec-lint.py --json > f.txt` arranca con `{`; (b) `python spec-lint.py --json | json.load` parsea 226/0; (c)–(e) los 3 modos del wrapper limpios; (f) wrapper consumer-pipe parsea 226/0. Cambio **Fidelidad** (1 context manager + 1 branch en main, sin cambio de contrato visible al usuario humano). |
| v1.8   | 2026-07-22 | **Wrappers portables del gate** introducidos para que el gate sea invocable desde CI, IDE o un hook de git sin requerir ningún argumento adicional. (a) `scripts/check-spec.py` — entry point Python que delega a `spec-lint.py`, propaga el exit code y agrega dos flags útiles: `--quiet` (sólo imprime una línea de resumen) y `--json` (forward al gate, salida limpia, sin ruido del wrapper encima); el modo `--quiet` ahora captura stdout/stderr con `subprocess.PIPE` y descarta para no contaminar el resumen; el modo `--json` se abstiene de imprimir el mensaje humano posterior. (b) `scripts/check-spec.sh` — shim POSIX que resuelve el path vía `BASH_SOURCE[0]` + `cd + pwd` para ser invocable desde cualquier cwd. (c) `scripts/check-spec.bat` — shim Windows que usa `%~dp0` + python quoted-args (sobrevive paths con espacios). (d) `README.md` actualizado con sección "Cómo correr el gate (SDD)" listando las 4 formas de invocarlo (directa, wrapper Python, shim POSIX, shim Windows) y el snippet para integrar en `.git/hooks/pre-commit`. §15.3.2 añadida con la referencia canónica al wrapper. **Bug menor detectado en el review**: el primer pase del wrapper tenía `--quiet` que no suprimia el output (siempre se transmitía al terminal del subprocess) y `--json` que se contaminaba con la línea `[check-spec] gate verde`. Ambos cerrados antes de bumpear a v1.8 — los tres modos verificados con exit 0 sobre las 226 invariantes del codebase actual. Cambio **Estructural-secundario** (tooling nuevo, sin cambio de contrato visible al usuario). | El regex `\balmac[ée]n(?:es|ado|aje|amiento)?\b` no cubría `almacenamientos` (plural abstracto) ni `almacenados` (plural del participio). Se amplía a `\balmac[ée]n(?:es|ado|ados|aje|amiento|amientos)?\b` — sigue sin overlap con el label `almacenero/warehouse operator` (la palabra `almacenero` no termina en ninguno de los sufijos listados) y ahora sí dispara en futuros edits que usen plurales. `python spec-lint.py` sigue con **exit 0** (226 PASS / 0 FAIL). Cambio **Fidelidad** (1 línea de regex, sin cambio de contrato). |
| v1.7   | 2026-07-22 | **Verificación empírica de las 7 equivalencias nuevas de v1.6** + endurecimiento de regex. One-shot sobre los `<meta name="description">` de los 7 pares ES↔EN confirma que 4 de las 7 están **dormantes** hoy: `arcilla inerte/inert clay` (0/0), `almacenero/warehouse operator` (0/0), `operario de planta/floor operator` (0/0), `especialista de laboratorio/lab specialist` (0/0); y 3 son **asimétricas** entre ES y EN: `peletización/pelleting` (ES=1 EN=2), `nodo de decisión/decision node` (ES=1 EN=1, mismo par), `proceso hero/hero process` (ES=0 EN=1). §15.3.1 item 13 reescrito con la verdad: lista categorizada de las 29 equivalencias en `Activas hoy` (~25) + `Dormantes` (4). Además: (a) regex de almacén narrow-eada de `\balmac[ée]n\w*\b` a `\balmac[ée]n(?:es|ado|aje|amiento)?\b` para que NO dispare junto con el label `almacenero/warehouse operator` (antes etiquetaba dos veces en la misma palabra); (b) plurales aceptados en los 4 labels de roles + `arcilla(s)` (`almaceneros?`, `operarios?`, `especialistas?`, `arcillas?`, ambos lados); (c) orden de definición en el archivo corregido (check_assets → check_content_drift, alineado con la numeración humana 12 → 13). `python spec-lint.py` corre con **exit 0** (226 PASS / 0 FAIL). Cambio **Estructural-secundario** (refina el gate y la documentación, sin cambio de contrato visible al usuario). |
| v2.0   | 2026-07-24 | **Runtime proofs** añadidos como grupo 14 del gate, cerrando la grieta estructural que permitió que `sitemap.xml` declarara URLs distintas de las que servía el filesystem. (a) Nuevo script canónico `scripts/smoke-site.py` (≈260 líneas): arranca un `http.server` en `127.0.0.1` sobre una de las 10 candidatas `4321..4330`, parsea `sitemap.xml` con `xml.etree`, hace GET a cada `<loc>` vía `urllib` (sin dependencia de `curl`), enumera los `*.html` enlazados desde cualquier otro HTML (regex sobre `<a|link|script|img|source|iframe|video|track|embed|area>` con atributos `href|src|poster`), resuelve cada href contra el directorio del HTML que lo contiene, y reporta dos categorías de drift: `declared-not-served` (URL en sitemap pero servidor devuelve ≠200) y `served-but-unlisted` (HTML en disco referenciado desde otro HTML pero NO en sitemap, excluyendo `404.html`). Subclass `_ReuseAddrServer(socketserver.TCPServer)` con `allow_reuse_address=True` evita que sockets TIME_WAIT bloqueen 4321 en Windows. Exit codes: 0 = limpio, 1 = drift, 2 = error runtime (bind, sitemap missing, etc). Modo `--json` consume machine-readable. (b) Wrappers POSIX/Windows: `scripts/smoke-site.sh` (chained `python` exec con `"$@"` pass-through) y `scripts/smoke-site.bat` (`python "%~dp0smoke-site.py" %*`), siguiendo el mismo patrón de los `check-spec.{sh,bat}`. (c) Nuevo `check_runtime_proofs()` en `spec-lint.py` que ejecuta `python scripts/smoke-site.py --json` en subprocess (timeout 60 s), parsea el JSON del probe y registra 2 invariantes: `Runtime proofs: probe output was valid JSON` y `Runtime proofs: no drift between sitemap, server and HTML links`. Agregado a `ALL_CHECKS` como grupo 14. (d) **BUG-005 cerrado**: `en/index.html` tenía 12 referencias `<a href="/en/procesos/<slug>.html">` que apuntaban a rutas inexistentes (los archivos viven en `procesos/en/`); corregidas en una pasada con `str_replace(allowMultiple=true)` de `href="/en/procesos/` → `href="/procesos/en/`. (e) Verificación: `python scripts/smoke-site.py` exit 0 con `[smoke-site] PASS — sitemap matches reality (16 URLs served, 0 broken, 0 unlinked)`; `python scripts/check-spec.py --quiet` exit 0; `check-spec --json | json.load` parsea las 2 filas nuevas. §15.3.1 cobertura extendida de 13 a 14 grupos. Cambio **Estructural-secundario con descubrimiento de bug de producción**: añadir el grupo 14 destapó 12 hrefs rotos que el gate estructural no podía detectar (el sitemap no sabia nada sobre lo que `<a href>` decía en HTML, y los lints estructurales no hacian GET). El binomio `spec-lint.py` + `smoke-site.py` es ahora la primera línea de defensa contra drift sitemap↔filesystem↔HTML. |
| v2.1   | 2026-07-24 | **Byte budget detector** añadido como grupo 15 del gate. Función `check_byte_budget()` en `spec-lint.py` agrega el peso de `*.html` (archivado en el root, excluyendo `docs/`) y `assets/**/*` (recorrido con `os.walk` para portabilidad) en bytes uncompressed y gzip. Comprime con `gzip.compress()` por archivo y suma. Registra 6 invariantes — uno por par dimensión/métrica (HTML unc, HTML gz, assets unc, assets gz, total unc, total gz) — para que el diagnóstico apunte a qué lado se está inflando cuando algo falla. Constantes al tope del módulo: `BUDGET_HTML_KB_UNC=175`, `BUDGET_HTML_KB_GZ=55`, `BUDGET_ASSETS_KB_UNC=110`, `BUDGET_ASSETS_KB_GZ=60`, `BUDGET_TOTAL_KB_UNC=250` (target del usuario), `BUDGET_TOTAL_KB_GZ=90` (target del usuario). Calibración contra peso real medido: el sitio actual pesa ~215 KB unc / ~82 KB gz, así que el headroom es ~15-25% según dimensión (justo suficiente para que una nueva ronda de meta tags, descripciones largas o un asset nuevo levante el gate, sin penalizar refactors menores de contenido). Helper `_delta(actual, limit)` muestra headroom cuando está por debajo del límite y `EXCEEDS limit X by Y KB` cuando lo supera — un mantenedor que ve una sola fila en CI entiende inmediatamente en qué dimensión está el problema. Verificación empírica: `python scripts/check-spec.py --quiet` exit 0; `check-spec.py --json` parsea 234 / 0 FAIL (subió de 228 a 234 con las 6 filas del nuevo grupo). Si en el futuro algún presupuesto queda corto, bumpear la constante + actualizar §15.3.1 item 15 con la nueva calibración, todo en el mismo commit. Cambio **Estructural-secundario** (extiende el gate con un chequeo nuevo, no cambia el contrato visible al usuario). |
| v2.1.1 | 2026-07-24 | **Polish del grupo #15** aplicando los tres hallazgos accionables del code-reviewer sobre v2.1. (1) **Nota advisory sobre per-section vs total**: comentario multi-línea encima de `BUDGET_*_KB_*` aclarando que los caps per-sección (175/55 HTML, 110/60 assets) son advisory — identifican CUÁL dimensión se está inflando — mientras que los caps totales (250 unc / 90 gz) son el constraint binding para merges. Los caps per-sección son deliberadamente menores que el total cada uno para que el invariante per-sección falle antes si una dimensión consume una parte desproporcionada del budget. (2) **Asset precondition**: añadido `EXPECTED_KEY_ASSETS = [assets/css/styles.css, assets/js/app.js, assets/img/favicon.svg, assets/img/og-image.png]`. Al tope de `check_byte_budget()`, si alguno falta emite 1 invariante FAIL "Byte budget precondition: key assets present" más 4 invariantes FAIL downstream (assets unc/gz + total unc/gz) marcadas "(skipped: keys missing)" — así la barra inferior del gate no silencia-pasa con ceros cuando `assets/` se borra accidentalmente. Si todos están presentes emite 1 PASS "4 checked, all present". (3) **Hidden files + extension whitelist**: añadido `ASSET_EXTENSIONS = (.css, .js, .svg, .png, .jpg, .jpeg, .webp, .ico, .woff, .woff2, .ttf, .otf, .mp4, .webm, .txt, .json, .xml)`. La enumeración de assets adentro de `os.walk` ahora filtra `if not name.startswith(".")` (excluye `.DS_Store`, `.gitkeep`, etc.) y `if any(name.lower().endswith(ext) for ext in ASSET_EXTENSIONS)` (excluye artefactos de build, sourcemaps, extensiones desconocidas). Incluir `.mp4/.webm` mantiene la puerta abierta para PEND-001 cuando se reemplace el `.video-frame` placeholder por el `<video>` real. Verificación: `python scripts/check-spec.py --quiet` exit 0; `check-spec.py --json` parsea 235 / 0 FAIL (subió +1 por la fila de precondition). Cambio **Fidelidad** (extiende el grupo sin cambiar contrato — sólo defensa contra regresiones silenciosas). |
| v2.2   | 2026-07-25 | **Pre-commit hook wired** + scope/timeout contract added al gate. (a) `.git/hooks/pre-commit` (POSIX bash, `chmod +x`) clasifica staged paths con `git diff --cached --name-only --diff-filter=ACMR` contra un whitelist trivial (case-sensitive) `docs/`, `scripts/`, `SPEC.md`, `README.md`, `.gitignore` — cualquier path no-trivial promotes el commit a SCOPE=`full`; mientras que un commit puramente-trivial queda en SCOPE=`fast` que skip group #14 (runtime proofs) bajo cap de 30 s y mantiene group #15 (byte budget). (b) `--scope={fast,full}` agregado a `spec-lint.py` (define `SCOPE_GROUPS` dict a nivel módulo; default `full`) y forwardeado por `scripts/check-spec.py`. (c) `--timeout=N` agregado a `scripts/check-spec.py` con `subprocess.run(start_new_session=True)` + `os.killpg(SIGTERM)` para reap el árbol completo de procesos cuando el timeout expira (gate child + `smoke-site.py` grandchild + `http.server` daemon thread bound to ports 4321-4330) — exit 124 sigue la convención de `bash timeout`. (d) `--json` contract extendido **aditivamente**: nuevos top-level keys `scope` y `skipped` en el JSON output (backwards-compatible — readers existentes los ignoran gracefully). (e) `docs/PRE-COMMIT.md` añadido como guía operativa complementaria (install, scope decision, timeout semantics, bypass). Verificación empírica: (i) JSON sanity → `scope='fast' skipped=['check_runtime_proofs'] pass=233 fail=0`; (ii) trivial commit (SPEC.md + docs/RUNTIME-PROOFS.md staged) → `[pre-commit] ... scope=fast` + exit 0; (iii) full clean commit via `--scope=full --quiet` direct → exit 0; (iv) drift-induced commit (sitemap.xml con bogus loc) → `scope=full` + `[check-spec] FAIL — exit 1` (commit bloqueado). §15.3.1 item 16 added describing el fast/full split + los script paths. Cambio **Estructural-secundario** (wiring de tooling existente — el gate ya existía, ahora se ejecuta automáticamente antes de cada commit en vez de manualmente. Sin cambio de contrato visible al usuario final). |
| v2.3   | 2026-07-25 | **CI gate wired** via `.github/workflows/gate.yml` + scope-policy divergence entre local + CI runs. (a) El workflow corre en cada PR + push a `main` que toucha cualquiera de `*.html`/`*.css`/`*.js`/`sitemap.xml`/`SPEC.md`/`scripts/check-spec.py`/`spec-lint.py`/`.github/workflows/gate.yml`, gracias al `paths:` filter (commits que sólo tocan `docs/`, `.gitignore`, `README.md` no queman runner-minutes). (b) Job `spec-lint full scope` en `ubuntu-latest` con `timeout-minutes: 5` y `permissions: contents: read` para limitar el blast radius del `GITHUB_TOKEN` — name-pinned para branch-protection match. (c) Steps: `actions/checkout@v4` + `actions/setup-python@v5` con `python-version: '3.8'` + `run: python scripts/check-spec.py --scope=full --quiet`. Exit != 0 flips el status check a rojo, y branch protection con "Require status checks to pass before merging" + match por nombre del job bloquea el merge. (d) **Scope policy**: pre-commit usa `--scope=fast` para trivial y `--scope=full` para content (local dev UX); CI **invariante** usa `--scope=full` solo (no fast lane permitted) — tiene budget tiempo-generous y NO debe tolerar drift que sobreviva un `git commit --no-verify` local — un committer que bure el hook todavía queda atrapado en el PR check antes de tocar `main`. (e) Verificación: YAML parses vía `yaml.safe_load` (syntactic OK); gate sigue exit 0 sobre estado actual preservado. §15.3.1 item 17 added documenting el network gate + el scope-policy rationale. **Operación**: además del workflow file, configurar branch protection en GitHub repo settings (fuera del spec — operational config). Cambio **Estructural-secundario** (nuevo layer en la cadena de defensa de drift, sin cambio de contrato ni de contenido visible al usuario final). |
| v2.3.1 | 2026-07-25 | **Polish del workflow + grietas críticas cerradas** después del code-reviewer-minimax-m3 sobre v2.3. (a) **Q4 corregido**: añadidos `assets/**` y `robots.txt` al `paths:` filter de `pull_request` + `push` (en ambos triggers) — antes un commit exclusivamente-asset (e.g., un `og-image.jpg` re-encodado de 12 MB a 1.5 MB o viceversa) bypaseaba CI porque ningún file del filter matcheaba, aunque group #15 byte-budget sí inspecta `assets/**`. Era coverage gap real. (b) **Q6 corregido**: nueva step final `Assert job-name contract` (con `if: always()`) que hard-fails con `::error::Contract violation` si `$GITHUB_JOB != "spec-lint full scope"`. El nombre del job es el **único** surface que branch-protection matchea — un rename silencioso rompía la protection rule sin error visible; la assertion hace el FAIL ruidoso en el log de Actions. (c) **Q3 nice-to-have aplicado**: añadido `workflow_dispatch:` para re-trigger manual sin commit nuevo (debugging de "passed locally, failed in CI"). (d) **Q7 nice-to-have aplicado**: timeout-minutes: 5 ahora documentado en el header comment con wall-clock budget estimado de runs previos (~60 s clean / ~120 s worst-case under byte-budget load) y 3x headroom. Verificación: `yaml.safe_load` OK; gate sigue exit 0 sostenido. §15.3.1 item 17 expanded con la sub-regla de path-coverage parity + job-name contract pin. Cambio **Fidelidad** (cierra grietas del workflow sin extender alcance del gate). |
| v2.4   | 2026-07-25 | **Local hook migrado a `.githooks/`** + install procedure simplificado via `core.hooksPath`. (a) `.githooks/pre-commit` ahora versionado en el repo (sí tracked en git) — el source-of-truth deja de ser `.git/hooks/pre-commit` (per-clone, NOT versioned). Cada clon obtiene el hook vía `git pull`, sin copy-paste manual del script. (b) **Install procedure one-liner**: `git config core.hooksPath .githooks` corre una vez post-clone y persiste en `.git/config`. Reemplaza el `chmod +x .git/hooks/pre-commit` per-clone que estaba en docs/PRE-COMMIT.md §6 v2.2. (c) `docs/PRE-COMMIT.md §6` reescrito con el install flow nuevo (1-2 comandos: `git config` + opcional `chmod +x` en Windows); cada `git pull` actualiza el hook automáticamente. (d) **Caveats documentados**: (i) en Windows el bit `+x` puede perderse en clones cross-platform — documentado como step opcional one-time; (ii) clones pre-v2.4 pueden migrar ejecutando `git config core.hooksPath .githooks` una vez — el `.git/hooks/pre-commit` existente se vuelve dead bytes; (iii) si un developer clona y committea ANTES del `git config`, el hook no dispara silenciosamente — mitigation via onboarding docs o `make bootstrap` target. (e) `§15.3.1 item 16` actualizado: el contract surface ahora apunta a `.githooks/pre-commit` (no `.git/hooks/`). Verificación: `bash -n .githooks/pre-commit` OK; gate exit 0 sostenido. Cambio **Estructural-secundario** (cambia el deploy mechanism del hook pero no su contrato ni su contenido visible al usuario final). |
| v2.5   | 2026-07-26 | **SHA-pinned actions + Dependabot monthly contract** como supply-chain hardening contra tag-mutation attacks. (a) `.github/workflows/gate.yml` reescrito para que `actions/checkout` y `actions/setup-python` referencien por **SHA de commit (40-char hex)** en lugar de tag mutable, con versión comment-inlined para auditabilidad humana: `actions/checkout@11d59604169c99144365775c7423927d7f7e9140 # v4.4.0` y `actions/setup-python@a26af6942ad3ed426615b191c9533fbd4802c0ca # v5.6.0`. Header comment del workflow extendido con la rationale. Defense-in-depth: tag-pinning confía en que upstream nunca reasignará `vN.x.y` a un commit malicioso (rare pero documentado per OSSF Scorecard como supply-chain vector); el SHA fija 100% qué código corre, el comment `# vN.M.P` preserva legibilidad. (b) `.github/dependabot.yml` añade el update contract: ecosystem `github-actions` (único relevante — este proyecto no tiene `package.json`/`requirements.txt`/`Dockerfile`/`go.mod`), `interval: monthly` con `day: 1` y `time: "04:00"` UTC, PRs batched por `actions/*` minor+patch agrupados en un solo PR mensual, `open-pull-requests-limit: 5` (default), labels `dependencies`+`security`. (`open-pull-requests-limit` non-specified ⇒ default 5; `rebase-strategy` non-specified ⇒ default `auto`.) (c) **NO auto-merge** habilitado — manual review obligatorio porque el workflow mismo feeds CI: un bump con `python-version: '3.8'` removida rompe el gate justo cuando debería detectar ese mismo breakage. Major version bumps (p.ej. futuro `actions/checkout@v5` o `actions/setup-python@v6`) **no entran en el group batch** — surface como PR separado porque pueden cambiar default behavior (Python version support matrix, checkout semantics, action inputs). (d) `§15.3.1 item 18` added documenting el SHA-pin contract + Dependabot update contract. Verificación: ambos YAMLs parsean vía `yaml.safe_load`; SHAs son 40-char hex lowercase (grep guard); gate sigue exit 0 (235 PASS / 0 FAIL full scope; 233 PASS / 0 FAIL fast scope). Bumps a pins / Day / Schedule / Group config / ecosystem requieren editar este §13 + §15.3.1 item 18 + el header comment del workflow + `.github/dependabot.yml` en el mismo v. Cambio **Estructural-secundario** (hardening supply-chain operacional — drift no detectable hasta attack event, pero ahora capado mensualmente por Dependabot PR batch). |
| v2.6   | 2026-07-26 | **Preview-deploy por PR via `actions/deploy-pages` + `deployment_path`** — cada PR obtiene su propia URL de revisión sin tocar `main` hasta merge. (a) **Nuevo job `preview-deploy`** agregado a `.github/workflows/gate.yml` después del job `gate`, gated por `needs: gate` (sólo corre si gate exits 0) + `if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository` (fork PRs ⇒ deploy abortado silenciosamente por permissions; gate aún verde porque job se skipea, no falla). (b) **Sequence del job** (5 steps): (1) `actions/checkout` SHA-pinned (# v4.4.0); (2) **sed-rewrite step crítico** que convierte `href="/X"` → `href="./X"` y `src="/X"` → `src="./X"` en cada HTML (find + sed `-i` in-place) — necesario porque SPEC §3 usa rutas absolutas que el browser resuelve contra **origin** (`https://<owner>.github.io/assets/...`) NO contra el `deployment_path` subpath; el rewrite hace el artifact subpath-safe sin tocar el código fuente (production deploy mantiene su comportamiento actual); (3) `actions/configure-pages` + (4) `actions/upload-pages-artifact` con `path: '.'` (no build step, sitio estático); (5) `actions/deploy-pages` con `deployment_path: pr-${{ github.event.pull_request.number }}` — URL único por PR a `https://<owner>.github.io/<repo>/deployments/pr-<N>/index.html`. (c) **PR comment** via `marocchino/sticky-pull-request-comment@v2` (third-party tag-pinned, hardening deferred) — idempotente, edita el mismo comment en cada push subsiguiente sin acumular N comments. (d) **SHA-pins nuevos** (a verificar contra GitHub antes de merge): `actions/configure-pages@45bfe01d784fd09908492efd4b9b940e4ab7be17 # v6.0.0`, `actions/upload-pages-artifact@fc324d3101fd69ba1d80362143093952f4c0ee10 # v5.0.0`, `actions/deploy-pages@cd2ce8f45a706346b0ed2347209e984fe75aa7a8 # v5.0.0`. `marocchino/sticky-pull-request-comment@v2` queda tag-pinned — third party, hardening deferred. (e) **Permissions críticas** del job preview-deploy: `contents: read + pages: write + id-token: write + pull-requests: write` — `id-token: write` es OIDC requirement sin el cual `deploy-pages` falla con `forbidden`; `pull-requests: write` es para el bot comment. (f) **Cleanup strategy**: orphans accumulate (GitHub Pages no auto-limpia `deployment_path` entries); documentado como polish candidate para v2.7 (post-v2.6 priority). (g) **Operational requirement**: el repo debe tener Pages habilitado (Settings → Pages → Source: GitHub Actions) — fuera del spec, operational config. §15.3.1 item 19 added documenting el per-PR preview contract. Verificación: workflow `yaml.safe_load` OK; gate sigue exit 0 sostenido (235 / 0). Cambio **Estructural-secundario** (dev-facing tooling, sin cambio de contrato visible al usuario final del sitio; el sed-rewrite opera sobre el artifact en upload-time, no sobre el código fuente). |
| v2.7.2 | 2026-07-26 | **Page-folder restriction (Finding F1 polish)** — `scripts/html-validate.py` switch del exclude-list (`docs/` + `.git/` + hidden) al include-list via `_is_page_path(relpath)`. Auditoría de markup ahora restringida a los 4 folders autorizados per SPEC §3 (root, `en/`, `procesos/`, `procesos/en/`); `*.html` en `assets/_partials/`, `templates/` o cualquier folder exótico queda silenciosamente excluido. (a) Beneficio: futuros templating fragments o visual-regression fixtures que un contributor drop en `assets/` ya no disparan FAIL sobre reglas estructurales (lang, title, description, canonical) que esos fragments no satisfacen. (b) Drift coverage: si un contributor añade una nueva página real en un folder exótico (e.g. `procesos/es/index.html` para español-mexicano), group #16 lo reportará como missing-page y group #1 sitemap-drift detector levantará el FAIL. (c) Implementation: función `_is_page_path(relpath)` chequea `relpath.split('/')` contra length+path-prefix; trivial test cases (`procesos/sub/foo.html`, `templates/foo.html`, etc.) son rechazados correctamente. (d) **Sync contract**: si se añade un nuevo page folder autorizado, hay que editar `PAGE_DIRS` tuple en script + §3 + sitemap.xml + §13 = 4 edits en el mismo v. Cambio **Fidelidad** (cierra grieta operacional del exclude-list sin cambio de contrato). |
| v2.8   | 2026-07-26 | **Accessibility (a11y) ladder** — pure-Python subset de axe-core, group #16 extendido de 9 a 13 reglas. (a) **Scaffolding previo (Lighthouse budget detector, nunca implementado) formalmente reemplazado**: la fila v2.8 row previa en este change log documentaba un plan de `treosh/lighthouse-ci-action@v12` + `.lighthouserc.json` que nunca fue ejecutado en repo (verificable: ni el action está en `.github/workflows/gate.yml` ni el config existe en root); §15.3.1 item 22 referenciado por esa fila tampoco existía. Drift documentation-vs-reality, ahora corregido: este row documenta el v2.8 realmente shipped. (b) **Stack decision: pure-Python, no axe-core**. axe-core requiere Node runtime — choca con el Python-3.8-only CI runtime establecido en v2.3 (`gate.yml` usa `setup-python@v5` con `python-version: '3.8'`, sin Node). Alternativa evaluada: lighthouse-ci (descartada antes en v2.7 por chrome ~250 MB + 2-5 min/page scan). Pure-Python ladder corre sub-segundo sobre 17 pages y trade 100% a11y coverage por zero new runtime deps. (c) **4 reglas nuevas en `scripts/html-validate.py`**: (10) `button_no_accessible_name` (WCAG 4.1.2) — `<button>` sin `aria-label=`/`aria-labelledby=` Y sin texto visible después de stripping nested tags; (11) `link_no_accessible_name` (WCAG 2.4.4) — `<a href="X">` con X non-empty, sin aria-label, sin inner text; (12) `role_attr_invalid` (WCAG 1.3.1 + ARIA 1.2 discipline) — `role="v"` donde v ∉ ARIA 1.2 standard set de 66 roles (abstract roles `command`/`composite`/`input`/`landmark`/`range`/`roletype`/`section`/`select`/`structure`/`widget`/`window` + widgets + document structure + landmarks); (13) `input_no_label` (WCAG 3.3.2) — `<input>` excluyendo type=hidden/submit/button/reset/image sin `<label for=>` AND sin aria-label. (d) **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `files_scanned=17 rule_totals={}` (cero violations en codebase actual — production-clean por construcción, ningún `<button>`/`<input>` en el sitio); `scripts/check-spec.py --quiet` exit 0 con PASS count sube de 246 a 250 (+4 invariants). (e) **Spec-lint wiring**: 4 entries nuevas agregadas al `rules` tuple de `check_html_validate()` después de `deprecated_tags_present` (entry 9), total ahora 13 entries; preamble de la función actualizado "9 rules" → "13 rules (9 markup §10 + 4 a11y §6)". (f) **Coverage gaps filled**: las 4 reglas son coverage genuinamente nuevo vs grupos previos (group §5 `check_per_page_meta` no audita accessible-names de `<button>`/`<a>`/`<input>`, y group §4 `check_text_purity` no audita `role=` validity). (g) **Out-of-scope explícito**: color contrast (WCAG 1.4.3), focus order (2.4.3), live-region semantics (4.1.3), ARIA live events — todos requieren real browser engine y por eso pure-Python ladder no los cubre. §15.3.1 item 22 added documenting el a11y contract + stack decision rationale. **Sync contract**: añadir regla nueva / extender coverage regex requieren editar §13 v2.8 + este item + `scripts/html-validate.py` (rules + ARIA_ROLES frozenset) + `spec-lint.py` (rules list emitting labels) en el mismo v. Cambio **Estructural-secundario** (extiende el gate con 4 invariants nuevos sin cambio de contrato visible al usuario final del sitio). | añadido como group #17 del gate (CI-side, post preview-deploy). (a) **Nuevo step** `treosh/lighthouse-ci-action@v12` agregado como tercer job (`lighthouse:`) en `.github/workflows/gate.yml` después del job `preview-deploy`, gated por `needs: preview-deploy` + `if: needs.preview-deploy.result == 'success'` — corre solo si el preview deploy pasó exit 0. (b) **Path coverage parity**: `.lighthouserc.json` añadido al `paths:` filter de `pull_request` + `push` (14 paths totales cada uno) — un cambio a las thresholds dispara el gate automáticamente (path-mirror law de §15.3.1 item 17). (c) **Output plumbing**: el job `preview-deploy` ahora exports `preview-url: ${{ steps.deployment.outputs.page_url }}` (vía nuevo `outputs:` block) — el job `lighthouse` lo referencia como `needs.preview-deploy.outputs.preview-url` y lo pasa al action vía env var `LH_URL`. Sin este contract, LH_GA no sabría qué URL auditar. (d) **`treosh/lighthouse-ci-action@v12` queda tag-pinned** (no SHA-pinned) — third-party (mismo precedent que `marocchino/sticky-pull-request-comment@v2`); hardening a SHA-possible v2.8.1 polish. (e) **Lighthouse v en CI ≠ local gate**: este step sólo corre en CI (headless Chrome corriendo en ubuntu-latest runner); NO se invoca desde `spec-lint.py` ni desde el pre-commit hook. Drift acknowledged — el local gate (spec-lint groups #1-#16) no audita Lighthouse. Thresholds argued against local: chrome dependency (~250 MB) + 30-90 s per page scan ⇒ wall-clock explosion en local. Decisión documentada en §15.3.1 item 22. Cambio **Estructural-secundario** (CI-side hardening, drift non-detectable localmente pero capado en cada PR o push a main). |
| v2.9   | 2026-07-26 | **Single-source-of-truth rule catalog** (scripts/html-rules.json). El duplicado de `(key, label)` tuples entre `scripts/html-validate.py` counter switching y `spec-lint.py` rules list queda eliminado via un catálogo JSON versionado. (a) **NEW file scripts/html-rules.json** con schema `{ $schema_version: 1, rules: [{ key, label, pattern, pattern_flags, notes }] }` — 13 entries cubriendo las 9 reglas markup §10 + 4 a11y §6. (b) **scripts/html-validate.py** carga el catálogo en module-init time via `json.load` y exporta `RULES_CATALOG`, `RULE_KEYS`, `RULE_LABELS`; main()'s output dict agrega los keys `schema_version: 1` y `rule_catalog: [...]` para consumer introspection. Orphan-key guardrail añadido en main()'s else branch: cada violation key emitida por check_page() que NO sea prefix-matched por un elif branch debe ser exact match a un key del catálogo — RuntimeError en caso contrario (defense-in-depth contra drift entre check_page() y el catálogo). (c) **spec-lint.py check_html_validate()** reemplaza el hardcoded 13-entry rules list con `json.load(open(rules_json_path))['rules']` y un loop `for rule in rules_catalog: key=rule['key']; label=rule['label']`. 3 nuevos precondition invariants agregados: rule catalog exists, is valid JSON, $schema_version == 1. (d) **Sync contract reduction**: antes de v2.9, añadir regla = 4 edits (spec-lint.py label + html-validate.py counter + html-validate.py check + SPEC.md docs); después de v2.9, añadir regla = 3 edits (html-rules.json catalog + html-validate.py check + SPEC.md docs). El label ya no se duplica. (e) **Pattern como documentation, no runtime execution**: las 9 reglas pure-regex tienen su pattern en JSON como referencia humana; las 4 reglas multi-step (button/link/role/input) tienen `pattern: null` + notes explicando la lógica Python. Una rule engine genérica (JSON-driven) queda como follow-up vnext — la complejidad de expression-button/link/role/input como JSON schema no compensa al tamaño actual de 13 reglas. (f) **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `schema_version=1 files_scanned=17 rule_totals={}`; `scripts/check-spec.py --quiet` exit 0 con PASS count sube de 250 a 253 (+3 por los nuevos precondition invariants). §15.3.1 item 24 added documenting la nueva architecture. **Sync contract**: añadir regla nueva / extender coverage regex / renombrar rule key requieren editar §13 v2.9 + §15.3.1 item 24 + scripts/html-rules.json (catalog entry) + scripts/html-validate.py (check logic, con orphan-key guardrail bloqueando drift) en el mismo v. Cambio **Fidelidad** (cierra duplicación estructural sin cambio de contrato visible al usuario final del sitio). |
| v2.9.1 | 2026-07-26 | **Catalog coverage closure + schema migration path** (reviewer polish F2 + F5). (a) **F2 cerrado**: nuevo entry `file_missing` agregado al final del array `rules` en `scripts/html-rules.json` con `{key: "file_missing", label: "page file exists on disk", pattern: null, pattern_flags: [], notes: "sentinel returned by check_page() when the HTML file is missing from filesystem; bypasses the for-violation loop via early continue so never reaches the orphan-key guardrail"}`. El sentinel `file_missing` ya era emitido por `check_page()` cuando un page esperado no existe en disco; ahora el catálogo documenta los 14 violation keys (13 reglas + 1 sentinel) sin gap de cobertura. (b) **F5 cerrado**: nuevo field top-level `"migrations": {"1": "current"}` agregado a `scripts/html-rules.json` para documentar el schema actual + reservar espacio para futuras migraciones. spec-lint.py's precondition invariant `HTML validate: rule catalog $schema_version == 1` loose-ened a `>= 1` (`schema_version < 1` ahora dispara FAIL en lugar de `schema_version != 1`), así un bump a schema_version=2 en el futuro no requiere coordinated edits across files. (c) **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `rule_catalog_len=14` (antes 13, +1 por `file_missing`); `scripts/check-spec.py --quiet` exit 0 con PASS count sube de 253 a 254 (+1 por el nuevo invariant `HTML validate: rule catalog $schema_version >= 1` que reemplaza al anterior `== 1` con label actualizado). §15.3.1 item 25 added documenting el catalog coverage closure + el schema migration path. **Sync contract**: añadir sentinel nuevo / extender `migrations` map / bump `schema_version` requieren editar §13 v2.9.1 + §15.3.1 item 25 + `scripts/html-rules.json` (catalog entry + migrations field) + `scripts/html-validate.py` (sentinel emission) + `scripts/spec-lint.py` (precondition invariant labels si la semántica cambia) en el mismo v. Cambio **Fidelidad** (cierra 2 grietas de catálogo sin cambio de contrato visible al usuario final del sitio). |
| v2.10  | 2026-07-26 | **Generic JSON-driven rule engine** — los 13 rules + 1 sentinel de group #16 ya no viven como Python hardcodeado en `scripts/html-validate.py`; ahora el catalog (`scripts/html-rules.json`) es el único source of truth de rule metadata + logic specification, y el script es un generic engine con 8 dispatch types + sentinel. (a) **8 dispatch types** definidos en el engine: `regex_match` (4 rules), `regex_capture_nonempty` (2), `regex_count_compare` (1), `regex_negative_match` (1), `regex_capture_min_len` (1), `set_membership` (1), `nested_inner_text` (2), `input_with_label_lookup` (1). (b) **ARIA_ROLES moved to JSON**: el frozenset de 66 W3C ARIA 1.2 standard roles ahora vive en el top-level `sets` registry del catalog; el engine lo carga en module-init time y el rule `role_attr_invalid` lo referencia via `allowed_set_ref`. (c) **`$schema_version` bumped to 2** con `migrations: {"1": "legacy", "2": "current"}`. (d) **Sync contract finalmente realized**: añadir regla de shape existente = 1 edit al catalog (sin tocar `html-validate.py`). (e) **Init-time fail-fast**: `_validate_catalog_at_init()` corre al import-time y raise RuntimeError si hay typos en type names, missing required fields, unresolved `allowed_set_ref`, o duplicate keys. (f) **Pre-compiled patterns**: regex patterns se compilan una vez al module-init y se cachean en `rule['_compiled']`. (g) **Orphan-key guardrail hardened**: la verificación `_base_key_of(violation)` cubre todos los violation keys sin depender del prefix-match chain. (h) **Empirical**: standalone exit 0 con `schema_version=2 files_scanned=17 rule_totals={}`; `scripts/check-spec.py --quiet` exit 0 con PASS count estable en 254. Cambio **Estructural-secundario** (refactor del engine interno sin cambio de contrato visible al usuario final del sitio). |


| v2.7   | 2026-07-26 | **HTML markup validate** añadido como group #16 al gate. (a) Nuevo script canónico `scripts/html-validate.py` (~190 líneas, pure-Python stdlib `re` + `json` + `os.walk` + `glob` only — SIN Node, SIN headless Chrome). Deriva la lista de pages con `os.walk` filtering `.html`, exclude `docs/` + `.git/` + hidden files, sorted para diff estable en CI logs. Aplica 9 reglas alineadas a SPEC §10: `doctype_missing` (DOCTYPE html ausente ⇒ quirks mode), `lang_missing_or_empty` (<html lang=""> ausente), `h1_count_mismatch` (≠1 <h1> por página), `title_missing_or_empty` (<title> ausente), `description_missing_or_short` (<meta description> <120 chars per §10.3), `canonical_missing` (<link rel="canonical"> ausente), `imgs_no_alt` (<img> sin `alt=""` per WCAG 1.1.1), `cjk_chars_present` (japonés/chino/coreano per §10.1 — regex cubre Hiragana + Katakana + CJK Unified Ideographs + Hangul Jamo + Hangul Compatibility Jamo + Hangul Syllables), `deprecated_tags_present` (<center>/<font>/<frame>/<marquee>/etc.). Emite JSON con `rule_totals` per-rule counter + `violations_per_page` per-page list (para debugging detallado). (b) **Polish post-reviewer**: (F1) CJK regex extendida para incluir Hangul (Korean estaba invisible); (F2) `ALL_PAGES` derivado de `os.walk` en lugar de hardcoded list (cualquier nuevo `*.html` se audita automáticamente, no queda invisibly unscanned); (F3) description regex attribute-order-independent via lookaheads (antes requería `name=` antes que `content=` ⇒ false-negatives en hand-edited HTML). (c) **Por qué no htmlhint ni lighthouse-ci**: htmlhint requiere Node — choca con Python-3.8-only CI runtime de v2.3. lighthouse-ci requiere headless Chrome (~250 MB) + 2-5 min per scan vs ~10 ms acá; wall-clock explotaría past 5 min timeout. Pure-Python ladder completa el scan en sub-segundo. (d) **Nuevo check function** `check_html_validate()` en `spec-lint.py` agregado después de `check_byte_budget()` (group #16 después de group #15, orden de declaración preserved) y registrado en `ALL_CHECKS` tuple via append `check_html_validate,`. Reporta 11 invariants: 1 probe (probe output valid JSON), 1 sanity (`files_scanned` consistente con `*.html` count en filesystem), 9 per-rule bucket counters. (e) **JSON contract del probe es backwards-compatible**: rule key format `rule_totals` extiende el shape existente con 9 new keys; readers existentes no se rompen. (f) §15.3.1 item 20 added documenting markup contract + polish rationale. Verificación empírica: standalone `python scripts/html-validate.py` exit 0 con `files_scanned=17/17 rule_totals={}` (cero violations en codebase actual — production-clean); `scripts/check-spec.py --quiet` exit 0 con PASS count sube de 235 a 246 (+11). Bumps a las reglas / PAGES derivation requieren editar este §13 + §15.3.1 item 20 + `scripts/html-validate.py` (rules + CJK regex + description regex) + `spec-lint.py` (rules list emitting labels) en el mismo v. Cambio **Estructural-secundario** (extiende el gate con un grupo nuevo sin cambio de contrato visible al usuario). |
| v3.0   | 2026-07-27 | **Production deploy wired en `gate.yml`**. (a) **Nuevo job `deploy`** agregado entre `preview-deploy` y `lighthouse` en `.github/workflows/gate.yml`, gated por `needs: gate` + `if: (...) event == push && ref == main || event == workflow_dispatch`. El mismo job `gate` es pre-flight común, drift no llega a `/<repo>/`. (b) **Event scope**: corre en (i) push a `main` desde cualquier rama o desde propia `main` después de un merge, (ii) re-run manual via `Actions → SDD Gate → Run workflow`. NO corre en PRs — `preview-deploy` los maneja. (c) **Why separate from `preview-deploy`**: mismo engine (`actions/deploy-pages@v4`) + mismo sed-rewrite step + mismo SHA-pin pattern, pero: (1) `environment: github-pages` prod vs `github-pages-preview` PR; (2) sin `deployment_path` ⇒ artifact lands en `/<repo>/` canonical, no en `/pr-N/` subpath; (3) `concurrency: group: pages, cancel-in-progress: false` para que dos pushes rápidos en cola en vez de colisionar contra el Pages CDN root. (d) **Step-naming parity**: tanto `preview-deploy` como `deploy` ahora suffix el rewrite step con `(preview)` / `(main)` para disambiguation en CI logs, y ambos llevan un `>>> DO NOT REMOVE <<<` line documentando por qué el sed es indispensable (origin-vs-project-subpath path resolution). (e) **Env prerequisite operacional**: el workflow falla con "Environment not found" si `github-pages` env no existe en repo Settings → Environments. Setup one-time documentado en el comment del job: Settings → Environments → New → name `github-pages` → Deployment branches → only `main`. Esta es la única acción manual fuera del push que el primer deploy requiere. (f) **Empirical**: `gate.yml` yaml.safe_load aún reporta `ScannerError` sobre `permissions: contents: read` en la línea original (PyYAML trata el `:` interno como mapping) — GitHub Actions' parser tolera el construct sin quotes, così el job corre fine; documentado como ítem v3.0.1 polish (quote-fix: envolver `permissions:` values explícitamente). Gate sigue exit 0 sostenido (PASS/FAIL counts intactos, gate no inspecciona el YAML del workflow). **Sync contract**: añadir prod deploy step / cambiar environment name / modificar el `if:` predicate requieren editar este §13 + §15.3.1 item 17 + el header comment del job en `gate.yml` en el mismo v. Cambio **Estructural-secundario** (CI-side tooling, sin cambio de contrato visible al usuario final del sitio). |

**Regla**: bumpear este change log con cada cambio material. La numeración
propuesta es `v1.x` para ajustes de fidelidad y `v2.x` para cambios de alcance
(nuevo proceso, nueva sección en el spec, ruptura de contrato).

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
| **PEND-002** | Despliegue | 🟡 Medium | Reemplazar dominio placeholder `example.com` | Antes del primer deploy real, cambiar `https://example.com` en los siguientes archivos: `sitemap.xml` (16 URLs), `robots.txt`, `/index.html` JSON-LD (`WebSite.url`, `Organization.url`), `/en/index.html` JSON-LD, `og:url` y `og:image` en las **17** páginas HTML del sitio (2 homes + 7 procesos ES + 7 procesos EN + `404.html`), `README.md` y este spec. Una vez hecho, este PEND se cierra. |
| **PEND-003** | Mejora | 🟢 Low | Imagen OG específica del proyecto | Reemplazar `assets/img/og-image.png` (placeholder generado) por una imagen real (1200 × 630 px) con logo y una foto de la planta. |
| **PEND-004** | Funcional futuro | ⚪ Parked | Sub-fases navegables (tabs / acordeón / anclas) dentro de procesos con varias fases | La Opción 3 del rediseño de Secado (tabs dentro de Peletización) **no** está escrita al spec — §9.2 sólo describe el patrón actual con `depth-grid` + `io-grid` + `telemetry`. Cualquier exploración futura debe empezar escribiendo la sección §9.2 correspondiente antes de codear. Se mantiene como referencia, sin prioridad. |
| **PEND-005** | Modo oscuro | ⚪ Parked | Dark mode con toggle manual | Descartado en §1 Non-Goals. Mantenido en backlog como referencia a futuro. No se trabaja hasta que se levante el Non-Goal. |
| **PEND-006** | PWA | ⚪ Parked | Service Worker + manifest | Descartado en §1 Non-Goals. Mantenido en backlog como referencia a futuro. |
| **BUG-002** ✅ Closed | Bug | 🟡 Medium | ~~`404.html` incumple §10.3 — description corta + canonical ausente + OG/Twitter ausentes~~ | **Cerrado en v1.4** — `404.html` reescrito: description extendida a >120 chars (bilingüe, menciona el pipeline), `<link rel="canonical" href="/404.html">` agregado, 6 meta `og:*` agregados, 4 meta `twitter:*` agregados. Verificable: re-correr `python spec-lint.py` → grupo 5 (per-page meta) y grupo 12 con 0 FAIL para `404.html`. |
| **BUG-003** ✅ Closed | Bug | 🟡 Medium | ~~5 process pages EN tienen description < 120 chars~~ | **Cerrado en v1.4** — descripciones EN de `procesos/en/{reception, pre-cleaning, fine-cleaning, packaging, finished-product-warehouse}.html` extendidas con una frase técnica adicional (audiencia, restricción biológica o métrica clave). Cada descripción ahora ≥120 chars. Verificable: re-correr lint → grupo 5 sin FAIL de longitud para esas 5 rutas. |
| **BUG-004** ✅ Closed | Bug | 🟡 Medium | ~~`procesos/limpieza-fina.html` ES tiene description de 119 chars~~ | **Cerrado en v1.4** — description de `procesos/limpieza-fina.html` extendida con el fragmento "aplicado en el bombo" para cruzar el umbral de §10.3. Verificable: re-correr lint → grupo 5 sin FAIL para esa ruta. |
| **BUG-001** ✅ Closed | Bug | 🟡 Medium | ~~Cualquier referencia residual a `/08` en formato `NN/08`~~ | **Cerrado en v1.1.2** — tres instancias en `<meta>` tags de `procesos/recepcion.html` reemplazadas de la forma `NN/08` por `NN/07` (numeración obsoleta de la era pre-fusión, hoy `NN/07` consistente con §3). Comprobado en v1.2 con grep BUG-001 automatizado: 0 hits en `*.html`, `*.md`, `*.xml`. La regla general queda en §15.2.C como heurística de validación para futuros PEND/BUG. |

### Cómo añadir un nuevo ítem

1. Asignar ID correlativo (`PEND-00N` o `BUG-00N`).
2. Ponerle prioridad 🟢/🟡/🔴 o ⚪ Parked.
3. Fijar criterio de cierre medible (qué pasa al cerrarlo).
4. Si el ítem contradice al spec, marcar explícitamente "Rompe §X.Y" y
   resolverlo como BUG antes de cualquier release.
5. Bumpear `SPEC.md` con la entrada nueva en el change log (§13).

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
4. Bumpear `v1.x` en §13 con una línea clara.

#### B. Cambios de alcance

1. Localizar requisitos en §1 (Non-Goals), §3 (URLs), §5 (Funcionales), §6
   (No funcionales), §9 (Ficha de página) y §14 (backlog).
2. Si es un nuevo idioma o proceso: aprobar el cambio **fuera de este spec**.
3. Actualizar **en este orden**: §3 → §9 (nueva ficha) → `sitemap.xml` →
   README → homes ES/EN → páginas de proceso ES/EN → este spec.
4. Correr §10 completa.
5. Bumpear `v2.x` en §13.

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

A partir de v1.2, la Checklist §10 queda cubierta por un script ejecutable
en la raíz del proyecto:

```
python spec-lint.py            # human-readable PASS/FAIL table, exit 1 if any FAIL
python spec-lint.py --json     # machine-readable output
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
      reactivación en §14.
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
    el bloat. Bumpear los límites requiere bumpear §15.3.1 item 15 al
    mismo tiempo.

    Reporta simétrico `shared=[…]`, `EN-only=[…]` y `ES-only=[…]` para
    debugging. Las asimetrías entre ES y EN dentro del set activo son
    visibles en el diagnóstico y sirven como guía para edits que busquen      simetría estricta.

16. **Pre-commit wiring: scope-based gate + fast lane cap**. The hook at `.git/hooks/pre-commit` (POSIX bash, `chmod +x`) classifies staged paths from `git diff --cached --name-only --diff-filter=ACMR` against a case-sensitive trivial whitelist (`docs/`, `scripts/`, `SPEC.md`, `README.md`, `.gitignore`); any non-whitelisted path promotes the commit to SCOPE=`full` while a purely-trivial commit stays in SCOPE=`fast`, which skips group #14 (runtime proofs) under a 30 s cap and keeps group #15 (byte budget). The hook invokes `scripts/check-spec.py --scope=$SCOPE --quiet` and propagates exit codes (0 = commit proceeds, 1 = drift blocked, 124 = timeout blocked). On timeout the wrapper uses `subprocess.run(start_new_session=True)` + `os.killpg(SIGTERM)` so the entire gate process group (gate child + `smoke-site.py` grandchild + `http.server` daemon thread bound to ports 4321-4330) is reaped cleanly — without this, sockets TIME_WAIT would leak across fast-lane commits. WIP bypass: `git commit --no-verify` (Git-native; skips the hook entirely). **v2.4: source-of-truth moved to `.githooks/pre-commit`** (versioned in the repo). Install procedure is the one-liner `git config core.hooksPath .githooks` per clone; after that, every `git pull` automatically updates the hook. On Windows the file may lose its `+x` bit in clone; one-time `chmod +x .githooks/pre-commit` if needed. See `docs/PRE-COMMIT.md §6` for the new install flow + caveats. Bumps to the trivial whitelist or the 30 s cap require editar SPEC.md §13 + §15.3.1 item 16 + `docs/PRE-COMMIT.md` en el mismo v. Ver `docs/PRE-COMMIT.md` §6 for the v2.4 install procedure and §7 for the rest of the operator-facing reference.

**Install procedure (v2.4)**: el hook ya NO vive en `.git/hooks/pre-commit`. A partir de v2.4 vive en `.githooks/pre-commit` (versionado en el repo). Cada clon corre `bash scripts/install-hooks.sh` (POSIX) o `scripts\\install-hooks.bat` (Windows) **una sola vez** para setear `git config core.hooksPath .githooks` — idempotente, safe to re-run. Los installers incluyen sanity check (error loud si `.githooks/pre-commit` no está pulled yet) + smoke-test con empty staging (verifica que el hook funciona antes del primer commit real). Las viejas copias en `.git/hooks/pre-commit` son deprecated — user-cleanup vía el snippet "Migrating from v2.3 install" en `docs/PRE-COMMIT.md` §6. Ver esa sección para el step-by-step completo + uninstall + why-two-installers (la justificación cross-platform de `chmod +x` POSIX vs shabang-only Windows).

17. **CI gate: workflow-side envelope complementing the pre-commit hook**. `.github/workflows/gate.yml` runs `python scripts/check-spec.py --scope=full --quiet` on every PR + push to `main` whose changeset touches `*.html` / `*.css` / `*.js` / `sitemap.xml` / `SPEC.md` / `scripts/check-spec.py` / `spec-lint.py` / `.github/workflows/gate.yml` (the `paths:` filter is the explicit-cache equivalent — irrelevant commits don't burn runner-minutes). Job name `spec-lint full scope` (stable identifier so branch protection can match by name); runner `ubuntu-latest`; `timeout-minutes: 5`; `permissions: contents: read` (read-only `GITHUB_TOKEN`, defense-in-depth). Exit != 0 → red status check → branch protection blocks merge. **Scope-policy**: CI always uses `--scope=full`, never `--scope=fast` — the 30 s cap of the pre-commit fast lane is a dev-UX optimization, NOT a correctness argument. CI's job is belt-and-suspenders against `git commit --no-verify` landings. Workflow edits (paths, runner, job name, python-version) require updating SPEC.md §13 v2.3 + §15.3.1 item 17 in the same v. Branch-protection rules (match by name `spec-lint full scope`) live in repo settings, NOT in `SPEC.md` — operational config outside the contract.

**Path coverage is gated, not full-history**: el `paths:` filter de `pull_request` + `push` debe espejar exactamente la superficie de input del gate (HTML/CSS/JS/sitemap/SPEC/robots/assets/scripts/spec-lint/the workflow itself) — `assets/**` en particular es NO obvio pero required porque group #15 byte-budget lo inspecta y un commit asset-only con un `og-image.jpg` re-encodado sería el drift silencioso que escapa a la red. Si se añade un nuevo check que mira una nueva superficie (p.ej. `i18n/*.json` o `*.webmanifest`), el `paths:` filter debe extenderse en el mismo v. La ley empírica: **el filter y la gate.input_surface() son isomorfos bajo la misma bump-version** — no se puede bumpear el uno sin bumpear el otro.

**Job-name contract pin**: el job se llama `spec-lint full scope` y la última step del job (`Assert job-name contract`, con `if: always()`) hard-fails con `::error::Contract violation` si `$GITHUB_JOB != "spec-lint full scope"`. Cambiar ese nombre rompe branch protection silenciosamente porque la protection rule matchea por nombre y un rename sin actualizar settings permite merges con la rule apuntando al job viejo (y un día al job nuevo sin gate). La assertion convierte ese breakage silencioso en un FAIL ruidoso con instrucción explícita al committer: o revertir el rename, o actualizar la branch-protection rule en repo settings. El nombre `spec-lint full scope` se considera parte del contrato del workflow y cualquier rename requiere bumpear §15.3.1 item 17 + §13 + la branch-protection config en el mismo v.

18. **SHA-pinned actions + Dependabot monthly supply-chain contract**. Cada línea `uses:` en `.github/workflows/gate.yml` referencia una action por **SHA completo de commit (40-char hex)** con comment trailing `# v{N.M.P}` para auditabilidad humana, NO por tag mutable. A partir de v2.5: `actions/checkout@11d59604169c99144365775c7423927d7f7e9140 # v4.4.0` y `actions/setup-python@a26af6942ad3ed426615b191c9533fbd4802c0ca # v5.6.0`. Defense-in-depth contra tag-mutation: si upstream o atacante reasigna `v4.x.y` a un commit malicioso, todo consumer con `@v4` se compromete silenciosamente; SHA-pin hace la mutation imposible porque el SHA frozen en el YAML referencia un commit específico. El comment `# vN.M.P` no afecta esto — es comment-data para auditadores humanos (qué versión era realmente).

**Dependabot update contract**: `.github/dependabot.yml` configura updates mensuales sobre el ecosystem `github-actions` (el único relevante — este proyecto no tiene `package.json`, `requirements.txt`, `Dockerfile`, ni `go.mod`). Schedule: `interval: monthly, day: 1, time: "04:00"` UTC. PRs en grupos: `actions/*` minor+patch batched en un único PR mensual etiquetado `dependencies`+`security`. `open-pull-requests-limit: 5` (default), `rebase-strategy: auto` (default). Major version bumps **NO entran en el group batch** — surface como PR separado porque pueden traer breaking changes (p.ej., `setup-python` removiendo Python 3.x del matrix default). **Auto-merge NO habilitado** deliberadamente — manual review mandatory porque el workflow mismo alimenta CI: un bump con `python-version: '3.8'` removida upstream rompe el gate justo cuando ese gate debería ser lo que detecta el breakage. Cualquier edit a SHA pins / schedule day / group config / ecosystem scope requiere editar §13 v2.5 + este item + el header comment del workflow + `.github/dependabot.yml` en el mismo v.

19. **Per-PR preview-deploy via GitHub Pages `deployment_path`**. Cada vez que un PR abre o recibe push, `.github/workflows/gate.yml` corre un segundo job `preview-deploy` que corre sólo después de `gate` exits 0 (`needs: gate`) y sólo cuando el evento es `pull_request` con `head.repo.full_name == github.repository` (fork PRs ⇒ conditional skip; gate stays verde porque GITHUB_TOKEN restringido de fork no puede deployar). El job ejecuta: (1) `actions/checkout` SHA-pinned, (2) **sed-rewrite** de `href="/X"` y `src="/X"` a paths relative en cada `*.html` — necesario porque SPEC §3 usa absolute paths que el browser resuelve contra origin y no contra `deployment_path` subpath, (3) `actions/configure-pages` + `actions/upload-pages-artifact` con `path: '.'` (no build step, el sitio es estático, upload-root es el árbol entero), (4) `actions/deploy-pages` con `deployment_path: pr-${{ github.event.pull_request.number }}` — crea URL única por PR a `https://<owner>.github.io/<repo>/deployments/pr-<N>/index.html`, (5) `marocchino/sticky-pull-request-comment@v2` (third-party tag-pinned, hardening deferred) — postea el URL en el PR feed de forma idempotente: cada nuevo push re-edita el mismo comment en lugar de crear N comments. **Permissions kriticos**: `contents: read + pages: write + id-token: write + pull-requests: write` — `id-token: write` es OIDC requirement sin el cual `deploy-pages` falla con `forbidden`; `pull-requests: write` es para el bot comment. **Fork-PR safety**: el conditional `if` aborta silenciosamente el deploy cuando `head.repo != base.repo`, previniendo el patrón "PR desde fork → exfiltración via Pages". **Cleanup strategy**: orphans accumulate (GitHub Pages no auto-limpia `deployment_path` entries en close); trade-off honesty: el sitio es ligero (<250KB) y Pages free tier es generoso, así que v2.6 lo deja acumular y un cleanup step se programa para v2.7 si el repo crece. **Operator requirement**: el repo debe tener Pages habilitado (Settings → Pages → Source: GitHub Actions) — fuera del spec, operational config. **Sync contract**: edit de URLs / sed-rewrite regex / sticky-comment header / permissions set / cleanup step requieren editar §13 v2.6 + este item + el header comment del workflow en el mismo v; bumpear SHA pins sigue la regla de item 18.

20. **HTML markup validate: pure-Python filesystem-walk ladder over 9 rules**. Group #16 del gate invoca `scripts/html-validate.py` (subprocess 30 s timeout) que deriva `ALL_PAGES` desde `os.walk` (excluyendo `docs/`, `.git/`, hidden files) — **NUNCA hardcoded**, así futuras páginas se auditan automáticamente sin sync risk con sitemap. Aplica 9 reglas a cada `*.html`: DOCTYPE html presente (HTML5); `<html lang="">` present y non-empty (per §6, §10.2); exactamente 1 `<h1>` por página (§10.5 / WCAG b1.3.1); `<title>` non-empty (§10.3, browser tab UX); `<meta name="description">` con ≥120 chars (§10.3, ya enriquecido por BUG-002/003/004) — **regex atributo-order-independent via lookaheads** (cualquier order legal HTML5 funciona); `<link rel="canonical">` present (§10.3); cada `<img>` tiene alt="" (§6 / WCAG 1.1.1); cero CJK placeholder chars — **regex cubre las 3 familias de §10.1: Hiragana, Katakana, CJK Unified Ideographs (japonés+chino) + Hangul Jamo + Hangul Compatibility Jamo + Hangul Syllables (coreano)**; cero deprecated HTML tags (`<center>/<font>/<frame>/<marquee>/<blink>/<big>/<noframes>/<applet>/<acronym>/<tt>/<strike>`, HTML5 + ARIA discipline). Cada regla emite 1 invariant en el gate con label legible + detail `pages_with_issue=N`, así un FAIL de un PR apunta a cuál SPEC §10 constraint está regressing. JSON probe schema: `{ files_scanned, files_missing, files_with_violations, rule_totals: {rule_key: count}, violations_per_page: {relpath: [violation_keys]} }`. **Coverage gaps filled** (lo que grupos previos NO cubrían): `doctype_missing`, `h1_count_mismatch`, `imgs_no_alt`, `deprecated_tags_present` — 4 reglas genuinamente nuevas. Las otras 5 tienen overlap parcial con `check_per_page_meta` (group §5) y `check_text_purity` (group §4), pero defense-in-depth: si el scanner de meta tags pierde algo, la ladder lo agarra con un threshold distinto. **Trade-off documentado**: pure-Python ladder (sub-segundo sobre 17 pages, ~190 LOC) vs htmlhint (requiere Node — choca con Python-3.8-only CI runtime) vs lighthouse-ci (requiere headless Chrome + 2-5 min scan = wall-clock blow-up). **Sync contract**: añadir regla nueva / extender coverage regex requieren editar §13 v2.7 + este item + `scripts/html-validate.py` (rules + regex) + `spec-lint.py` (rules list emitting labels) en el mismo v. Bumps a subprocess timeout (30 s) únicamente §15.3.1 + `scripts/check-spec.py` (último v ya tiene --timeout flag).
21. **Page-folder restriction via `_is_page_path()` include-list (v2.7.2 polish)**. Cada scan de group #16 filtera las `*.html` candidates via `_is_page_path(relpath)`, función pura que retorna `True` SOLAMENTE si el relpath cae bajo uno de los 4 prefix-pattern: root-level file (`parts == ['<file.html>']`), `en/<file>` (`parts == ['en', '<file.html>']`, parts.len==2 con parts[0]=='en'), `procesos/<file>` (idem, parts[0]=='procesos'), `procesos/en/<file>` (parts.len==3 con parts[0]=='procesos' y parts[1]=='en'). Cualquier otra path — incluyendo `assets/_partials/foo.html`, `templates/foo.html`, `procesos/sub/foo.html`, `procesos/es/foo.html`, `docs/foo.html`, etc. — retorna `False` y queda silenciosamente excluida. Esta es la inversión F1 polish sobre v2.7.2: el exclude-list anterior (`docs/`, `.git/`, hidden files) atrapeaba cualquier `*.html` en cualquier folder tracked, incluyendo fragmentos que no son páginas reales y que fallarían rules 2/4/5/6 (lang/title/description/canonical no aplican a fragments). El include-list bloquea fragments en source pero mantiene el comportamiento dinámico (drop un nuevo `*.html` en una de las 4 carpetas autorizadas y group #16 lo audita automáticamente sin tener que tocar el script). **Coverage gap semántico**: si un contributor añade una nueva página real en un folder exótico (e.g. `procesos/es/index.html` para España-MX), group #16 lo reportará como missing-page y group #1 sitemap-drift detector levantará el FAIL — la grieta se cierra con doble cobertura (sitemap vs filesystem walk). **Sync contract**: añadir un folder autorizado (e.g. `blog/`) requiere editar (1) `PAGE_DIRS` tuple en `scripts/html-validate.py`, (2) `sitemap.xml`, (3) §3 SPEC.md (URL contract enumeration), (4) §13 (CHANGELOG row E item en §15.3.1) — 4 edits en el mismo v para mantener coverage simétrico cross-files.


24. **Single-source-of-truth rule catalog via `scripts/html-rules.json` (v2.9)**. Las 13 reglas de group #16 (9 markup §10 + 4 a11y §6) ya no viven duplicadas entre `scripts/html-validate.py` counter switching y `spec-lint.py` rules list — ahora residen en un solo catálogo JSON versionado (`$schema_version: 1`). Cada entry tiene `{ key, label, pattern, pattern_flags, notes }`: `key` es el violation key emitted por check_page() y looked-up en `rule_totals`; `label` es el description text usado en el gate invariant (visible en `python spec-lint.py` human-readable output); `pattern` documenta el regex usado por las 9 reglas pure-regex (NO runtime-executed — la lógica real sigue en Python); `pattern_flags` lista los regex flags (`["IGNORECASE"]`, etc.); `notes` explica la lógica multi-step para las 4 reglas complejas (button/link/role/input) que tienen `pattern: null`. **Loader contract**: `scripts/html-validate.py` carga `scripts/html-rules.json` en module-init time y exporta `RULES_CATALOG` + `RULE_KEYS` + `RULE_LABELS`. main()'s output dict agrega `schema_version: 1` y `rule_catalog: [...]` para downstream introspection. **Orphan-key guardrail** (defense-in-depth): en main()'s else branch, cada violation key emitida por check_page() que NO sea prefix-matched por un elif branch debe ser exact match a un key del catálogo — RuntimeError en caso contrario. Esto atrapa drift silencioso entre check_page() y el catálogo al ejecutar, no al commit. **spec-lint.py wiring**: `check_html_validate()` reemplaza el hardcoded 13-entry rules list con `json.load(open(rules_json_path))['rules']` y un loop `for rule in rules_catalog: key=rule['key']; label=rule['label']`. 3 nuevos precondition invariants agregados al gate: rule catalog exists (file present), rule catalog is valid JSON (parseable + has $schema_version), rule catalog $schema_version == 1 (contract stability), rule catalog has 13 rules (count match). Si cualquiera falla, el gate falla con detail explícito (`missing: scripts/html-rules.json` o `json error: …` o `schema_version mismatch`) — no silent fallback a defaults. **Sync contract reduction**: antes de v2.9, añadir regla = 4 edits (spec-lint.py label + html-validate.py counter prefix + html-validate.py check logic + SPEC.md docs). Después de v2.9, añadir regla = 3 edits (html-rules.json catalog entry + html-validate.py check logic + SPEC.md docs). El label/key ya no se duplica — vive en 1 lugar. **Out of scope para v2.9** (considerado pero deferred): rule engine genérica JSON-driven que ejecute los patterns en runtime. Trade-off: las 4 reglas multi-step (button/link/role/input) no son expresables como single regex; forzarlas a JSON schema agregaría complejidad sin ganancia clara al tamaño actual de 13 reglas. Si la colección crece a 30+ rules, reevaluar. **Sync contract**: añadir regla nueva / renombrar rule key / extender coverage regex / extender ARIA_ROLES set requieren editar §13 v2.9 + este item + scripts/html-rules.json (catalog entry) + scripts/html-validate.py (check logic) en el mismo v; el orphan-key guardrail en html-validate.py atrapa desincronización en runtime, los precondition invariants en spec-lint.py la atrapan en gate time.



25. **Catalog coverage closure + schema migration path (v2.9.1 polish)**. Dos ajustes menores al catálogo JSON para cerrar grietas surfaced por reviewer F2 + F5. (a) **F2 cerrado**: nuevo entry `file_missing` agregado al final del array `rules` en `scripts/html-rules.json`. El sentinel `file_missing` ya era emitido por `check_page()` cuando un page esperado no existe en disco; bypassa el `for violation in v:` loop vía early `continue` por lo que nunca alcanza el orphan-key guardrail, pero quedaba undocumented en el catálogo. Ahora los 14 violation keys (13 reglas + 1 sentinel) tienen catalog entries sin coverage gap. (b) **F5 cerrado**: nuevo top-level field `"migrations": {"1": "current"}` agregado a `scripts/html-rules.json`. spec-lint.py's precondition invariant `HTML validate: rule catalog $schema_version == 1` loose-ened a `>= 1` (`schema_version < 1` dispara FAIL), así un bump futuro a schema_version=2 no requiere coordinated edits across files. (c) **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `rule_catalog_len=14` (antes 13); `scripts/check-spec.py --quiet` exit 0 con PASS count sube de 253 a 254 (+1 por el label actualizado del invariant schema_version). **Sync contract**: añadir sentinel nuevo / extender `migrations` map / bump `schema_version` requieren editar §13 v2.9.1 + este item + `scripts/html-rules.json` (catalog entry + migrations field) + `scripts/html-validate.py` (sentinel emission si aplica) + `scripts/spec-lint.py` (precondition invariant labels si la semántica cambia) en el mismo v. Cambio **Fidelidad** (cierra 2 grietas de catálogo sin cambio de contrato visible al usuario final del sitio).



27. **Generic JSON-driven rule engine via 8 dispatch types (v2.10)**. El `scripts/html-validate.py` deja de tener 13 reglas hardcoded en `check_page()` y pasa a ser un generic engine compilado desde `scripts/html-rules.json` al module-init time. Cada catalog entry tiene un `type` discriminator que selecciona una de las 8 branches del engine. **Type taxonomy**: (1) `regex_match`; (2) `regex_capture_nonempty`; (3) `regex_count_compare`; (4) `regex_negative_match`; (5) `regex_capture_min_len`; (6) `set_membership`; (7) `nested_inner_text`; (8) `input_with_label_lookup`. **9th type**: `sentinel` (documented but never dispatched). **ARIA_ROLES moved to JSON**: el frozenset de 66 W3C ARIA 1.2 standard roles ahora vive en top-level `sets: {"ARIA_ROLES": [66 roles...]}`. **`$schema_version` bumped to 2** con `migrations: {"1": "legacy", "2": "current"}`. **Init-time fail-fast**: `_validate_catalog_at_init()` corre al import-time y raise RuntimeError si hay typos en type names, missing required fields, unresolved `allowed_set_ref`, o duplicate keys. **Pre-compiled patterns**: regex patterns se compilan una vez al module-init time y se cachean en `rule['_compiled']`. **Orphan-key guardrail hardened**: `_base_key_of(violation)` en `main()` cubre todos los violation keys — cada key emitido por `_dispatch_rule()` debe mapear a un catalog entry o RuntimeError. **Sync contract finalmente realized**: añadir regla de shape existente = 1 edit al catalog. Añadir regla de shape NUEVO = 1 catalog entry + 1 dispatch branch en `_dispatch_rule()` + 1 type name en `KNOWN_TYPES` + 1 type-specific validation branch. **Empirical**: standalone `python scripts/html-validate.py` exit 0 con `schema_version=2 files_scanned=17 rule_totals={}`; `scripts/check-spec.py --quiet` exit 0 con PASS count estable en 254. **Sync contract**: editar 1 catalog entry / extender `ARIA_ROLES` set / bump `$schema_version` / añadir un nuevo dispatch type requieren editar §13 v2.10 + este item + `scripts/html-rules.json` (catalog entry + sets field si aplica + migrations field) + `scripts/html-validate.py` (`_dispatch_rule()` dispatch branch si es nuevo shape + `KNOWN_TYPES` + `_validate_catalog_at_init()`) en el mismo v.

Reglas operativas:

- **Cualquier edit nuevo** debe terminar con `python spec-lint.py` verde.
- **Exit 0** = bloquea el release; **exit 1** = merge/commit bloqueado.
- Si el script descubre un nuevo invariante, agregalo al script **y** a
  §10/§10.6/§15.3.1 como mismo número de v.

### 15.3.2 Wrappers portables del gate (`scripts/check-spec.*`)

El gate se puede invocar de cuatro formas equivalentes, el resultado siempre
es el mismo exit code:

| Forma | Cuándo usarla |
|---|---|
| `python spec-lint.py` | Default. Tabla humana + multi-line summary. |
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

