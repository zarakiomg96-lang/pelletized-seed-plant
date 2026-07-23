# Planta de Semillas Peletizadas — Sitio informativo

Sitio informativo bilingüe (ES / EN) sobre la Planta de Semillas Peletizadas del Instituto de Investigación del Tabaco, la producción certificada de semillas y los siete procesos que recorren un lote desde la recepción hasta el almacén de producto terminado.

Construido como sitio estático (HTML + CSS + JS) — sin build step, sin dependencias.

## Estructura

```
.
├── index.html                  Inicio (español)
├── en/
│   └── index.html              Inicio (inglés)
├── procesos/                   Páginas de los 7 procesos (ES)
│   ├── recepcion.html
│   ├── pre-limpieza.html
│   ├── limpieza-fina.html
│   ├── peletizacion.html       ⭐ Proceso Hero (incluye Secado)
│   ├── envasado.html
│   ├── control-calidad.html    ⭐ Nodo de decisión
│   ├── almacen-producto-terminado.html
│   └── en/                     Misma estructura en inglés
├── assets/
│   ├── css/styles.css
│   ├── js/app.js
│   ├── img/                    SVG decorativos (logo, favicon, og-image.png)
│   └── video/                  Carpeta para tu video institucional
├── scripts/                    Wrappers del gate (SDD)
│   ├── check-spec.py           Entrada portable (Python)
│   ├── check-spec.sh           Shim POSIX
│   └── check-spec.bat          Shim Windows
├── spec-lint.py                Gate ejecutable de §15.3.1
├── SPEC.md                     Contrato Specification-Driven
└── README.md                   Esta guía
```

## SEO e i18n

Cada página incluye:

- `<link rel="canonical">` y `<link rel="alternate" hreflang="...">` para la versión ES y EN.
- Meta tags **Open Graph** (`og:title`, `og:description`, `og:url`, `og:image`, `og:locale`).
- Meta tags **Twitter Cards** (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`).

La imagen social por defecto es `assets/img/og-image.png` (1200 × 630 px). Si cambiás el dominio final, buscá el placeholder `/assets/img/og-image.png` y reemplazalo por una URL absoluta a tu imagen preferida. Lo mismo para `og:url`, que actualmente usa rutas relativas `/`.

## Cómo previsualizar

### Opción 1 — directamente en el navegador

Abre `index.html` con doble click desde el explorador de archivos.

### Opción 2 — servidor local (recomendado para desarrollo)

Con Python 3 instalado:

```bash
python -m http.server 4321
```

Luego abrí `http://localhost:4321/` en Chrome.

Con Node (sin instalar nada global):

```bash
npx --yes serve -l 4321 .
```

## Cómo correr el gate (SDD)

El proyecto usa **Specification-Driven Development** (ver `SPEC.md` §10 y §15.3.1). El gate ejecutable vive en `spec-lint.py` y aplica los 13 grupos de checks sobre el código + la spec. Cualquier edit de código debe pasar el gate antes de mergear.

Formas equivalentes de invocarlo:

```bash
# Forma directa (raíz del proyecto)
python spec-lint.py
python spec-lint.py --json     # salida máquina-leible

# Wrapper portable (recomendado para CI, hooks, IDE)
python scripts/check-spec.py            # tabla humana + guía de FAIL
python scripts/check-spec.py --quiet    # sólo una línea de resumen
python scripts/check-spec.py --json     # máquina-leible

# Shims por shell (si tu IDE necesita un ejecutable sin args)
bash scripts/check-spec.sh              # POSIX / git-bash / WSL
scripts\\check-spec.bat                  # Windows cmd / PowerShell
```

Si el gate sale con **exit 0** el cambio es mergeable. Si sale con **exit ≠ 0**:

1. Releé las líneas `[FAIL]` que imprime la tabla.
2. Editá HTML/CSS/JS o la spec según corresponda.
3. Re-corré el gate hasta que quede en exit 0.
4. Si descubriste un nuevo invariante roto, anotalo en `SPEC.md` §14 (BUG-N) antes de mergear.

Para integrar el gate en un pre-commit hook nativo de git (cuando inicies git en este proyecto), el wrapper es el comando a invocar:

```bash
# pegar dentro de .git/hooks/pre-commit después de `git init &&` :
exec python scripts/check-spec.py --quiet
```

## Cómo agregar el video institucional

1. Guardá tu video en `assets/video/intro.mp4` (o `.webm`).
2. En `index.html` reemplazá el bloque `<div class="video-frame">…</div>` por un elemento `<video>`. Ejemplo:

```html
<video class="video-frame" controls preload="metadata" poster="/assets/img/hero-poster.jpg">
  <source src="/assets/video/intro.mp4" type="video/mp4">
  <source src="/assets/video/intro.webm" type="video/webm">
  Tu navegador no soporta video HTML5.
</video>
```

3. Para mantener el aspect ratio responsive, ya está estilado con `aspect-ratio: 16/10` y `border-radius` en `assets/css/styles.css`.

## Cómo cambiar el contenido

Cada proceso es un archivo HTML autocontenido en `procesos/` (ES) o `procesos/en/` (EN). El bloque central sigue el patrón:

- En simple — un párrafo en lenguaje claro (audiencia general)
- En detalle — explicación técnica de densidad media
- Datos — tabla de telemetría y rangos

Para agregar más procesos o reordenar:

1. Editá los archivos existentes.
2. Mantené los mismos `meta-chip` y los enlaces cruzados (`next-step`) entre páginas.
3. Si agregás uno nuevo, actualizá los enlaces de `next-step` del proceso anterior.

## Paleta y tipografía

| Variable | Valor | Uso |
|---|---|---|
| `--cream` | `#faf6ee` | Fondo papel |
| `--ink` | `#0c1f17` | Texto principal |
| `--tobacco-700` | `#1f4a36` | Verde tobacco profundo |
| `--seed` | `#c19a3b` | Acento dorado (semilla) |

Fuentes cargadas vía Google Fonts:

- **Fraunces** — display serif (títulos)
- **Inter** — sans body
- **JetBrains Mono** — códigos, telemetría, eyebrow caps

## Despliegue

El sitio es 100% estático, pero usa **rutas absolutas** (`/assets/...`, `/procesos/...`). Eso significa que para verlo localmente necesitás un servidor HTTP (no basta abrir el `index.html` con doble click, a menos que el navegador soporte correctamente `file://`).

Funciona en:

- GitHub Pages
- Netlify / Vercel
- Cloudflare Pages
- Cualquier servidor HTTP

Para GitHub Pages: subí todo a un repo, activá Pages apuntando a la raíz.

### Antes de publicar

1. Reemplazá `og:image`, `og:url` y las URLs de `sitemap.xml`, `robots.txt` y JSON-LD con URLs absolutas de tu dominio final (actualmente usan `https://example.com`).
2. Generá una imagen OG propia de 1200 × 630 px y guardala en `assets/img/og-image.png`.
3. Si agregás el video institucional, actualizá el placeholder del home y reemplazalo por un `<video>`.

## Robots, sitemap y 404

- `robots.txt` permite a los rastreadores indexar todo y apunta al sitemap.
- `sitemap.xml` lista las 16 páginas del sitio.
- `404.html` es una página de error bilingüe con navegación de regreso.
- `index.html` y `en/index.html` incluyen datos estructurados **Schema.org** (`WebSite` + `Organization`).

## Origen del contenido

El contenido de cada proceso fue sintetizado de la tesis:

> Manso González, Osvel. *Sistema para la Digitalización de la Producción de Semillas Peletizadas en el Instituto de Investigación del Tabaco*. Trabajo de diploma — Universidad de las Ciencias Informáticas, La Habana, junio de 2026.

En particular:

- Pipeline de procesos (Diagrama de actividades, Figura 1)
- Lista de roles / actores del sistema (Diagrama de casos de uso, Figura 2)
- Restricciones biológicas y variables de manufactura

## Licencia del código

MIT.
