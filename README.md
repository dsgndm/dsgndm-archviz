# dsgn·dm archviz — web (home + proyectos)

Sitio estático (HTML/CSS/JS, sin framework). Abre `index.html` o sirve la carpeta (Vercel, Netlify…).

## Estructura

```
index.html · projects.html · projects/<carpeta>.html     (generados por build.py)
                               El HTML de cada proyecto se llama igual que su carpeta de assets:
                               projects/01-collective-housing.html  ↔  assets/projects/01-collective-housing/
css/style.css · js/main.js
assets/fonts/                  Archivo + IBM Plex Mono (locales)
assets/brand/studio.jpg        1200 × 1500 px (4:5)
assets/projects/<carpeta>/
    hero.jpg                   2400 × 1350 (16:9)   cabecera de proyecto (y carrusel home en los 4 destacados)
    index.jpg                  1200 × 800  (3:2)    tarjeta en projects.html
    thumb.jpg                  480 × 320   (3:2)    lista de la home
    card.jpg                   tamaño según proyecto (solo los 4 destacados, tarjeta de la home)
    exterior-01.jpg …          galería de exteriores (tamaño según "kind")
    interior-01.jpg …          galería de interiores
    video-poster.jpg           1920 × 1080 (si el proyecto tiene vídeo)
    pass-wire / pass-clay / pass-final.jpg   2400 × 1350 (opcional)
data/projects.json             Datos, textos y estructura de galerías
build.py                       Regenera todas las páginas
tools/make_placeholders.py     Crea los placeholders que falten (con su tamaño escrito)
```

## Flujo

1. Sustituye cada placeholder por tu render, mismo nombre y proporción (el tamaño está escrito en cada uno).
2. Edita `data/projects.json` → `python3 build.py`. Para renombrar un proyecto, cambia `folder` (y renombra la carpeta de assets): la URL de la página cambia con él.
3. Si añades o quitas imágenes: cambia las listas `exterior` / `interior` del proyecto y ejecuta `python3 tools/make_placeholders.py` y `python3 build.py`.

### Tipos de imagen en galería (cada fila suma 12)
`full` 12 col · 2400×1350 · `wide` 8 col · 2000×1125 · `half` 6 col · 1800×1200 · `tall` 4 col · 1200×1500  
Combinaciones que cuadran: full · half+half · wide+tall · tall+tall+tall.

### Vídeo
En `projects.json`: `"video": {"src": "video.mp4", "embed": ""}`. Pon el MP4 en la carpeta del proyecto, o un enlace de Vimeo/YouTube en `embed` (formato `https://player.vimeo.com/video/ID`). `"video": null` quita el bloque.

### Texto
Proyectos destacados (`"tier": "major"`): `brief` + `approach` + lista "Delivered" automática.  
Menores: una frase (`summary`) + "Delivered" automático.

### Contenido nuevo: clientes, precios, servicios
Todo en `data/site.json` (luego `python3 build.py`). Lo que está entre `[ corchetes ]` es placeholder y se ve en gris: cifras, logos de clientes, testimonios y precios. Páginas generadas: `pricing.html`, `services/*.html` (4 servicios + Santander & Cantabria).
Para logos de clientes, sustituye el texto en `clients` y, si quieres imagen, añade `<img>` en `trust_section()` de `build.py`.

### SEO y formulario
- `SITE_URL` (cabecera de `build.py`): pon el dominio final. Con él se generan canonical, vista previa social, datos estructurados, `sitemap.xml` y `robots.txt`. Vacío = se omiten.
- `assets/og.jpg` 1200 × 630: imagen por defecto al compartir (los proyectos usan su propio hero).
- `FORM_ENDPOINT`: URL de Formspree (o similar) para enviar el formulario sin abrir el correo. Vacío = abre el cliente de correo con el brief escrito.

### Idiomas (EN por defecto + ES en /es/)
`python3 build.py` genera las dos versiones. Inglés en la raíz; español en `es/` (`es/proyectos.html`, `es/precios.html`, `es/servicios/…`, `es/proyectos/<carpeta>.html`).
Dónde está cada texto en español:
- `data/ui.es.json` — textos de interfaz (clave = texto en inglés, valor = español). Si añades un texto nuevo en `build.py`, el build avisa de lo que falte traducir.
- `data/site.es.json` — servicios (incluido `slug_es`, la URL en español), tarifas, cifras, testimonios.
- `data/projects.es.json` — resumen, briefing y enfoque de cada proyecto. Los títulos de proyecto quedan en inglés.
Selector EN / ES en la cabecera (y en el menú móvil), que lleva a la misma página en el otro idioma. Con `SITE_URL` puesto se generan `hreflang` y un sitemap con las dos versiones.

### Herramientas y opciones nuevas
- **Imágenes ligeras:** `python3 tools/optimize_images.py` crea versiones WebP en varios tamaños junto a cada JPG; `python3 build.py` las sirve con `srcset`. Ejecútalo cada vez que sueltes renders nuevos.
- **PDF del portfolio:** `python3 build.py && python3 tools/make_pdf.py` genera `portfolio-dsgndm-en.pdf` y `-es.pdf` (páginas 16:9). Las páginas de origen están en `print/` (no enlazadas, `noindex`); el estilo en `css/print.css`.
- **Vídeo en bucle de portada:** en un proyecto de `projects.json` añade `"loop": "hero-loop.mp4"` (MP4 mudo, 5–8 s, 1920×1080, idealmente <4 MB) en su carpeta de assets. Sustituye a la imagen en la home y en su página; se reproduce solo cuando se ve y nunca con "reducir movimiento".
- **Caso de estudio y cita de cliente (opcional por proyecto):** `"story": {"challenge": "", "solution": "", "result": ""}` y `"quote": {"text": "", "name": "", "role": ""}` en `projects.json` (y su versión en `projects.es.json`).
- **Tarifas:** formatos, extras y factores en `data/site.json` / `data/site.es.json` (`pricing`).
- **Analítica sin cookies:** `ANALYTICS` y `ANALYTICS_ID` en `build.py` ("plausible", "umami" o "cloudflare").
- **Página Studio:** `studio.html` / `es/estudio.html`. Retrato en `assets/brand/studio.jpg` (1200 × 1500).
- Modo cine (vídeo y lightbox oscuros), botón de contacto fijo en móvil y enlace "saltar al contenido" ya incluidos.

### Animación
Micro-animaciones: revelado de imágenes (máscara), titulares palabra a palabra, etiqueta "View"/"Expand" en el cursor, transición entre páginas, parallax suave en la cabecera de proyecto, línea de progreso de scroll y marcas de recorte que se cierran al pasar el ratón.
Se desactivan solas con `prefers-reduced-motion`. Para apagarlas del todo: `ANIMATIONS = False` en `build.py` y `python3 build.py`.

Logo: constante `LOGO` en `build.py`. Contacto y enlaces: cabecera de `build.py`.
