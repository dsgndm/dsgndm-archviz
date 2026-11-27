#!/usr/bin/env python3
"""Builds the static site from data/projects.json.
Usage: python3 build.py   ->   index.html, projects.html, projects/<slug>.html"""
import re
import base64, copy, html, json, posixpath
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
SITE_EN = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
SITE_ES = json.loads((ROOT / "data" / "site.es.json").read_text(encoding="utf-8"))
PROJ_ES = json.loads((ROOT / "data" / "projects.es.json").read_text(encoding="utf-8"))
UI_ES = json.loads((ROOT / "data" / "ui.es.json").read_text(encoding="utf-8"))
SITE, SVCS = SITE_EN, SITE_EN["services"]
LANG = "en"
MISSING = set()
SVC_ES_SLUG = {x["slug"]: x["slug_es"] for x in SITE_ES["services"]}
ES_PAGES = {"projects.html": "proyectos.html", "pricing.html": "precios.html", "about.html": "sobre-mi.html", "services.html": "servicios.html", "contact.html": "contacto.html"}
KINDS, DATA = CFG["kinds"], CFG["projects"]
DATA_EN = DATA
for _p in DATA:  # page URL = asset folder name, so both always match
    _p["slug"] = _p["folder"]
MAJOR = [p for p in DATA if p["tier"] == "major"]
MINOR = [p for p in DATA if p["tier"] == "minor"]


def set_lang(lang):
    """Switch every global the page builders read: language, project texts, site texts."""
    global LANG, DATA, MAJOR, MINOR, SITE, SVCS, idx
    LANG = lang
    DATA = copy.deepcopy(DATA_EN)
    if lang == "es":
        for p in DATA:
            p.update(PROJ_ES.get(p["folder"], {}))
        SITE = SITE_ES
    else:
        SITE = SITE_EN
    SVCS = SITE["services"]
    MAJOR = [p for p in DATA if p["tier"] == "major"]
    MINOR = [p for p in DATA if p["tier"] == "minor"]
    idx = {p["slug"]: n + 1 for n, p in enumerate(DATA)}
    global SHOW_TYPE
    SHOW_TYPE = len({p["type"] for p in DATA}) > 1


SHOW_TYPE = False
typ = lambda p, sep=" · ": (e(t(p["type"])) + sep) if SHOW_TYPE else ""


def t(s):
    """UI string in the current language. English text is the key; Spanish lives in data/ui.es.json."""
    if LANG == "en":
        return s
    if s in UI_ES:
        return UI_ES[s]
    MISSING.add(s)
    return s


def loc(path, lang):
    """Site-root-relative file for an English logical path ('projects/x.html') in the given language."""
    if lang == "en":
        return path
    if path == "index.html":
        return "es/index.html"
    if path in ES_PAGES:
        return "es/" + ES_PAGES[path]
    if path.startswith("projects/"):
        return "es/proyectos/" + path[len("projects/"):]
    if path.startswith("services/"):
        return "es/servicios/" + SVC_ES_SLUG[path[len("services/"):-5]] + ".html"
    raise ValueError(path)


def pg(path):
    """Link target relative to the current language root."""
    full = loc(path, LANG)
    return full[3:] if LANG == "es" else full


def ab(base):
    """Prefix from the current page to the site root (assets, css, js)."""
    return base + ("../" if LANG == "es" else "")

# ----- Brand & contact settings (edit here) -----
SITE_NAME = "dsgn·dm archviz"
MAIN_SITE = "https://dsgndm.vercel.app"
BEHANCE = "https://www.behance.net/dsgndm"
EMAIL = "dsgndm@proton.me"
PHONE = "637795740"
# Public address of the site, no trailing slash (e.g. "https://archviz.dsgndm.com"). Needed for canonical URLs,
# social previews, structured data and sitemap.xml. Leave empty until the domain is known.
SITE_URL = ""
# Quote form: paste a Formspree (or similar) endpoint to send briefs by POST. Empty = opens the visitor's email app.
FORM_ENDPOINT = ""
# Privacy-friendly analytics (no cookies, no consent banner needed). provider: "plausible" | "umami" | "cloudflare" | ""
#   plausible -> ANALYTICS_ID = your domain (e.g. "archviz.dsgndm.com")
#   umami     -> ANALYTICS_ID = website id        cloudflare -> ANALYTICS_ID = beacon token
ANALYTICS = ""
ANALYTICS_ID = ""
# Micro-animations on/off (False = static site, no motion at all)
ANIMATIONS = True
# Logo: assets/brand/logo.svg (stacked wordmark). {root} is replaced with the path to the site root.
LOGO = ('<img class="logo-img logo-l" src="{root}assets/brand/logo.svg" alt="dsgn·dm archviz" width="120" height="32">'
        '<img class="logo-img logo-d" src="{root}assets/brand/logo-dark.svg" alt="dsgn·dm archviz" width="120" height="32">'
        '<img class="logo-img logo-w" src="{root}assets/brand/logo-white.svg" alt="" width="120" height="32">')
logo = lambda base="": LOGO.replace("{root}", ab(base))
# Studio portrait: transparent line drawing (PNG/WebP). Turned into particles on the page.
PORTRAIT = "portrait.png"

e = html.escape
b64 = lambda s: base64.b64encode(s.encode()).decode()
num = lambda i: f"{i:02d}"
idx = {p["slug"]: n + 1 for n, p in enumerate(DATA)}
def rs(p, name, sizes, base=""):
    """srcset/sizes attributes for an image if tools/optimize_images.py has produced WebP variants."""
    stem = name.rsplit(".", 1)[0]
    d = ROOT / "assets" / "projects" / p["folder"]
    ws = sorted(int(f.stem.rsplit("-", 1)[1]) for f in d.glob(f"{stem}-*.webp") if f.stem.rsplit("-", 1)[1].isdigit())
    if not ws:
        return ""
    ss = ", ".join(f"{ab(base)}assets/projects/{p['folder']}/{stem}-{w}.webp {w}w" for w in ws)
    return f' srcset="{ss}" sizes="{sizes}"'


href = lambda p, base="": f"{base}{pg('projects/' + p['slug'] + '.html')}"
img = lambda p, name, base="": f"{ab(base)}assets/projects/{p['folder']}/{name}"

SERVICES = [
    ("Exteriors", "Facades and surroundings, photo-integrated when the project needs it. Light, vegetation and scale that place the building in its real context."),
    ("Interiors", "Furnished and styled spaces with honest materials and natural light, built to validate the project with the client before construction."),
    ("Animation", "Full HD walkthroughs and flythroughs that show the building in motion, with calm and deliberate camera work."),
    ("Sales material", "Colour floor plans, infographics and assets for brochures, site hoardings and promotion websites."),
]
STEPS = [
    ("Brief & documents", "Plans, material specification, location and references. We agree which images are needed and in what order."),
    ("Modelling & materials", "I prepare the 3D model, cameras and finishes. Framings are approved before anything is rendered."),
    ("Light & test renders", "Lighting and atmosphere are tuned through low-resolution tests you can react to early."),
    ("Delivery & revisions", "Final render and retouching. Two revision rounds are included; more may adjust the price."),
]
FAQS = [
    ("What do you need to get started?", "Plans, the materials specification, the location and, if available, a reference of the surroundings such as a photo or drone view. With that I can prepare a closed proposal."),
    ("How long does a project take?", "It depends on the number of images and their complexity. Every proposal includes a week-by-week schedule with a delivery date for each milestone."),
    ("How many revision rounds are included?", "Two rounds are included in the price. If more are needed we talk before continuing, so there are no surprises."),
    ("Which formats do you deliver?", "High-resolution images ready for print or web, and Full HD video. If you need another size or format, tell me at the start."),
    ("Can you start from sketches or an early design?", "Yes. For early-stage images a clear massing model, or even sketches with dimensions, can be enough. We agree the level of detail in the brief so the image matches the stage of the project."),
    ("How do we review the work?", "Previews arrive as private links or PDFs with numbered views, so every comment can point to a specific image. Final files are delivered through a download link."),
    ("What if the design changes after approval?", "Corrections are part of the revision rounds. Changes to the design itself mean rebuilding parts of the model, so I quote them separately and tell you before doing any extra work."),
    ("Do you work with architects and developers?", "Yes. I usually collaborate with architecture studios, developers and interior designers: they bring the project and I turn it into images."),
]

FAVICON = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23F1F3F7'/%3E%3Crect x='14' y='44' width='9' height='9' fill='%231E33FF'/%3E%3C/svg%3E"


# ---------------------------------------------------------------- shared
THEME = ("<script>(function(d){try{var m=localStorage.getItem('dm-theme')}catch(e){}"
         "var t=m||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');d.setAttribute('data-theme',t)})(document.documentElement)</script>")
GATE = ("<script>(function(d){d.classList.add('js');"
        "if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;"
        "d.classList.add('anim');"
        "setTimeout(function(){if(!window.__dm)d.classList.remove('anim')},3000)})(document.documentElement)</script>")


def analytics_tag():
    if not (ANALYTICS and ANALYTICS_ID):
        return ""
    return {
        "plausible": f'<script defer data-domain="{e(ANALYTICS_ID)}" src="https://plausible.io/js/script.js"></script>',
        "umami": f'<script defer src="https://cloud.umami.is/script.js" data-website-id="{e(ANALYTICS_ID)}"></script>',
        "cloudflare": f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\": \"{e(ANALYTICS_ID)}\"}}'></script>",
    }.get(ANALYTICS, "")


def faq_ld():
    return {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": LANG,
            "mainEntity": [{"@type": "Question", "name": html.unescape(t(q)), "acceptedAnswer": {"@type": "Answer", "text": html.unescape(t(a))}} for q, a in FAQS]}


def abs_url(path):
    return f"{SITE_URL.rstrip('/')}/{path}" if SITE_URL else ""


def canon(path, lang):
    """Public URL of a page (EN logical path) in a language."""
    f = loc(path, lang)
    return abs_url({"index.html": "", "es/index.html": "es/"}.get(f, f))


def head(title, desc, base="", path=None, ld=None, og="assets/og.jpg"):
    gate = GATE if ANIMATIONS else ""
    seo = ""
    if SITE_URL and path is not None:
        url = canon(path, LANG)
        alt = "".join(f'\n<link rel="alternate" hreflang="{l}" href="{canon(path, l)}">' for l in ("en", "es"))
        alt += f'\n<link rel="alternate" hreflang="x-default" href="{canon(path, "en")}">'
        seo = (f'<link rel="canonical" href="{url}">{alt}\n<meta property="og:url" content="{url}">\n'
               f'<meta property="og:image" content="{abs_url(og)}">\n<meta name="twitter:card" content="summary_large_image">')
        if ld:
            seo += "\n" + "\n".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld)
    return f"""<!doctype html>
<html lang="{LANG}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="{'es_ES' if LANG == 'es' else 'en_GB'}">
<meta name="theme-color" content="#F1F3F7" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121212" media="(prefers-color-scheme: dark)">
{THEME}
{seo}
<link rel="icon" href="{ab(base)}assets/brand/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{ab(base)}assets/brand/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{ab(base)}assets/brand/apple-touch-icon.png">
{gate}
<link rel="preload" href="{ab(base)}assets/fonts/archivo-wdth.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{ab(base)}css/style.css">
{analytics_tag()}
</head>
"""


def crumbs(items):
    """items: [(name, EN logical path)] -> BreadcrumbList JSON-LD"""
    out = []
    for i, (n, p) in enumerate(items):
        pp, _, frag = p.partition("#")
        out.append({"@type": "ListItem", "position": i + 1, "name": n, "item": canon(pp, LANG) + (("#" + frag) if frag else "")})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": out}


def lang_links(cur):
    """(desktop switcher html, mobile link html) pointing at the same page in the other language."""
    if not cur:
        return "", ""
    other = "es" if LANG == "en" else "en"
    here, there = loc(cur, LANG), loc(cur, other)
    target = posixpath.relpath(there, posixpath.dirname(here) or ".")
    parts = []
    for l in ("en", "es"):
        if l == LANG:
            parts.append(f'<span class="on" aria-current="true">{l.upper()}</span>')
        else:
            parts.append(f'<a href="{target}" lang="{l}" hreflang="{l}" aria-label="{"Español" if l == "es" else "English"}">{l.upper()}</a>')
    desk = f'<span class="lang mono">{parts[0]}<i>/</i>{parts[1]}</span>'
    mob = f'<a class="mm-lang mono" href="{target}" lang="{other}" hreflang="{other}">{"Español" if other == "es" else "English"}</a>'
    return desk, mob


def NAV(base=""):
    """Main pages, same order in header, mobile menu and footer."""
    return [(t("Projects"), f"{base}{pg('projects.html')}"), (t("Services"), f"{base}{pg('services.html')}"), (t("About"), f"{base}{pg('about.html')}"),
            (t("Process &amp; pricing"), f"{base}{pg('pricing.html')}"), (t("Contact"), f"{base}{pg('contact.html')}")]


def header(base="", home=None, cur=None):
    if home is None:
        home = f"{base}index.html" if base else ""
    links = NAV(base)
    home_i = f'<a class="nav-home" href="{base}index.html" aria-label="{t("Home")}"><svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M3 9.2 10 3l7 6.2V17h-4.6v-4.6H7.6V17H3z" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg></a>'
    nav = home_i + "".join(f'<a href="{h}">{x}</a>' for x, h in links)
    desk, mob = lang_links(cur)
    return f"""<body id="page">
<a class="skip" href="#main">{t("Skip to content")}</a>
<header class="site-header">
  <a class="logo" href="{home or '#top'}" aria-label="{SITE_NAME} — {t('home')}">{logo(base)}</a>
  <nav class="nav-desktop" aria-label="Main">{nav}</nav>
  <div class="head-right">{desk}<button class="theme-sw" type="button" role="switch" aria-checked="false" aria-label="{t('Dark mode')}"><span class="knob"></span></button><a class="btn head-cta" href="{base}{pg('contact.html')}">{t("Let’s talk")}</a></div>
  <button class="menu-btn" type="button" aria-label="{t('Open menu')}">{t("Menu")}</button>
</header>
<div class="mobile-menu" aria-label="Menu"><a href="{base}index.html">{t("Home")}</a>{"".join(f'<a href="{h}">{x}</a>' for x, h in links)}{mob}<div class="theme-row"><button class="theme-sw" type="button" role="switch" aria-checked="false" aria-label="{t('Dark mode')}"><span class="knob"></span></button><span>{t("Dark mode")}</span></div></div>
"""


def footer(base=""):
    nav = NAV(base)
    links = "".join(f'<a href="{h}">{x}</a>' for x, h in nav)
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="foot-row">
      <a class="logo" href="{base}index.html">{logo(base)}</a>
      <nav class="foot-nav mono" aria-label="Footer">{links}</nav>
    </div>
    <div class="foot-bottom mono"><span>© 2026 {SITE_NAME} · Santander</span><span class="foot-ext"><a href="{BEHANCE}" target="_blank" rel="noopener">Behance ↗</a><a href="{MAIN_SITE}" target="_blank" rel="noopener">dsgn·dm ↗</a></span><a href="#page">{t("Back to top ↑")}</a></div>
  </div>
</footer>
<a class="sticky-cta" href="{base}{pg('contact.html')}" aria-label="{t("Let’s talk")}">{t("Let’s talk")}</a>
<script src="{ab(base)}js/main.js" defer></script>
</body>
</html>
"""


def marks():
    return '<span class="mark tl"></span><span class="mark tr"></span><span class="mark bl"></span><span class="mark br"></span>'


# ---------------------------------------------------------------- home
def hero():
    """Full-width image hero: the featured projects crossfade behind the headline; the index below drives them."""
    def slide(p, n):
        if p.get("loop"):
            return (f'<video class="hx-img{" on" if n == 0 else ""}" data-loop src="{ab("")}assets/projects/{p["folder"]}/{p["loop"]}" poster="{img(p, "hero.jpg")}" '
                    f'muted loop playsinline preload="metadata" aria-label="{e(p["title"])}" width="2400" height="1350"></video>')
        return None
    imgs = "".join(
        slide(p, n) or f'<img class="hx-img{" on" if n == 0 else ""}" src="{img(p, "hero.jpg")}"{rs(p, "hero.jpg", "(max-width:900px) and (orientation:portrait) 170vh, 100vw")} alt="{e(p["title"])}" width="2400" height="1350"'
        f'{' fetchpriority="high"' if n == 0 else " loading=lazy"}>' for n, p in enumerate(MAJOR))
    items = "".join(
        f'<button class="hx-item" type="button" data-title="{e(p["title"])}" data-dims="{e(p["location"])}" data-href="{href(p)}" aria-label="{e(p["title"])}"></button>'
        for n, p in enumerate(MAJOR))
    return f"""<section class="hero hero-bleed" id="top">
  <h1 class="sr-only">{t("Architecture, seen <em>before</em> it’s built.").replace("<em>", "").replace("</em>", "")}</h1>
  <div class="hx-stage">
      <div class="hx-frame on-img">
        {imgs}
        <div class="hx-shade" aria-hidden="true"></div>
        <a class="hx-cap hx-l" href="#"><span class="hx-t"></span><span class="mono hx-d"></span><span class="hx-n" hidden></span></a>
        <div class="hx-list" style="--n:{len(MAJOR)}">{items}</div>
      </div>
  </div>
</section>"""


def spread(p, n):
    """Featured project card on the home: one frame whose images change with a soft horizontal wipe."""
    names = [x for x in ["hero.jpg", "exterior-01.jpg", "interior-01.jpg", "exterior-02.jpg", "interior-02.jpg"]
             if (ROOT / "assets" / "projects" / p["folder"] / x).exists()][:4]
    imgs = "".join(f'<img class="fc-img{" on" if k == 0 else ""}" src="{img(p, x)}"{rs(p, x, "(max-width:700px) 100vw, " + ("100vw" if n == 0 else "50vw"))} alt="{e(p["title"]) if k == 0 else ""}" width="1800" height="1200" loading="lazy">' for k, x in enumerate(names))
    dots = "".join(f'<i{" class=on" if k == 0 else ""}></i>' for k in range(len(names)))
    return f"""    <a class="fcard rv" href="{href(p)}" style="--d:{n}">
      <span class="fc-frame">{imgs}<span class="fc-shade" aria-hidden="true"></span>
        <span class="fc-cap"><span class="fc-dots" aria-hidden="true">{dots}</span><span class="fc-t">{e(p['title'])}</span><span class="mono fc-m">{e(p['location'])}</span><span class="fc-go" aria-hidden="true">→</span></span></span>
    </a>"""


def pcard(p, base="", sizes="(max-width:700px) 100vw, (max-width:1100px) 50vw, 33vw", heading="h3"):
    """Project card used in every project grid: image, name, location and image count. No numbers."""
    count = len(p["exterior"]) + len(p["interior"])
    return f"""      <a class="pcard" href="{href(p, base)}" data-n="{idx[p['slug']]}" data-title="{e(p['title'])}" data-loc="{e(p['location'])}" data-type="{e(t(p['type']))}">
        <span class="frame"><img src="{img(p, 'index.jpg', base)}"{rs(p, 'index.jpg', sizes, base)} alt="{e(p['title'])}" width="1200" height="800" loading="lazy"></span>
        <span class="pc-cap"><{heading} class="pc-t">{e(p['title'])}</{heading}><span class="ar" aria-hidden="true">→</span>
          <span class="mono pc-m">{typ(p)}{e(p['location'])}</span></span>
      </a>"""


def sorter():
    sort = "".join(f'<button class="ix-sort{" on" if k == "n" else ""}" type="button" data-sort="{k}" aria-pressed="{"true" if k == "n" else "false"}">{lbl}</button>' for k, lbl in (("n", t("Selection")), ("title", "A–Z"), ("loc", t("Location"))))
    return f'<div class="ix-sorts mono" role="group" aria-label="{t("Sort projects")}">{sort}</div>'

def work_card(p, n):
    c = p["card"]
    return f"""      <a class="work w{n + 1} rv" href="{href(p)}">
        <div class="frame"><img src="{img(p, 'card.jpg')}"{rs(p, 'card.jpg', '(max-width:900px) 100vw, 50vw')} alt="{e(p['title'])}" width="{c['w']}" height="{c['h']}" loading="lazy"></div>
        <div class="cap"><span class="mono n">{num(n + 1)}</span><h3>{e(p['title'])}</h3><span class="mono tag">{e(t(p['type']))} · {e(p['location'])}</span><p>{e(p['summary'])}</p></div>
      </a>"""


def row(p):
    return f"""      <a class="row" href="{href(p)}" data-img="{img(p, 'thumb.jpg')}">
        <span class="mono n">{num(idx[p['slug']])}</span>
        <div class="row-thumb"><img src="{img(p, 'thumb.jpg')}" alt="" width="480" height="320" loading="lazy"></div>
        <h3>{e(p['title'])}</h3>
        <span class="mono type">{e(t(p['type']))}</span>
        <span class="mono loc">{e(p['location'])}</span>
        <span class="ar">↗</span>
      </a>"""


def portrait(base=""):
    """Studio portrait: line drawing rebuilt with WebGL particles (js/main.js, .pp). The drawing itself is the fallback."""
    src = f"{ab(base)}assets/brand/{PORTRAIT}"
    return f"""<div class="frame pp" data-src="{src}">
        <img class="pp-still" src="{src}" alt="{t("Portrait of Diego Moreno, line drawing")}" width="1230" height="1279" loading="lazy">
        <canvas aria-hidden="true"></canvas></div>"""


def archive_section(rows):
    """Minor projects list. Omitted entirely while there are none."""
    if not MINOR:
        return ""
    return f"""<section id="archive" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Archive")})</span><h2 class="display">{t("More<br>projects")}</h2></div>
      <a class="mono ulink" href="{pg("projects.html")}">{t("All projects →")}</a></div>
    <div class="list rv">
{rows}
    </div>
  </div>
</section>
<div class="preview" aria-hidden="true"><img alt="" src="" width="480" height="320"></div>"""


def teaser(label, text, link, link_label, items=""):
    """One quiet line on the home that points to a full page."""
    return f"""<section class="teaser">
  <div class="wrap tz rv">
    <span class="mono label">({label})</span>
    <div class="tz-body"><p class="tz-lead">{text}</p>{items}<a class="mono ulink" href="{link}">{link_label}</a></div>
  </div>
</section>"""


# Home: before/after comparison. "placeholder": True while the clay pass is a stand-in generated from the final render.
HOME_COMPARE = {"project": "quinta-atlantica", "clay": "pass-clay.jpg", "final": "hero.jpg", "placeholder": True}
# Home: a full-width image pause between blocks (project folder, image)
HOME_PAUSE = ("novalinas", "exterior-03.jpg")


def statement():
    return f"""<section class="statement">
  <div class="wrap"><p class="st-line rv">{t("Architectural visualization from Santander — light, material and calm.")}</p></div>
</section>"""


def compare_block():
    c = HOME_COMPARE
    p = next((x for x in DATA if x["folder"] == c["project"]), None)
    if not p or not (ROOT / "assets" / "projects" / p["folder"] / c["clay"]).exists():
        return ""
    note = f'<span class="mono phold ba-note">[ {t("clay pass pending")} ]</span>' if c.get("placeholder") else ""
    return f"""<section class="compare">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Process")})</span><h2 class="display">{t("From model to image")}</h2></div>{note}</div>
    <div class="ba rv" style="--x:50%">
      <img class="ba-final" src="{img(p, c['final'])}"{rs(p, c['final'], '100vw')} alt="{e(p['title'])} — {t('final render')}" width="2400" height="1350" loading="lazy">
      <img class="ba-clay" src="{img(p, c['clay'])}"{rs(p, c['clay'], '100vw')} alt="{e(p['title'])} — {t('clay model')}" width="2400" height="1350" loading="lazy">
      <span class="ba-line" aria-hidden="true"><span class="ba-knob">↔</span></span>
      <span class="mono ba-l">{t("Clay")}</span><span class="mono ba-r">{t("Final")}</span>
      <input class="ba-range" type="range" min="0" max="100" value="50" aria-label="{t("Compare clay model and final render")}">
    </div>
  </div>
</section>"""


def figures():
    """Key figures: big numbers that count up when they appear, each with a short line of context."""
    def val(v):
        if v.strip().startswith("["):
            return ph(v)
        num_part = "".join(ch for ch in v if ch.isdigit())
        rest = v.replace(num_part, "", 1) if num_part else v
        return f'<span class="cnt" data-to="{num_part}" data-pad="{len(num_part)}">{num_part}</span>{e(rest)}' if num_part else e(v)
    figs = "".join(f'<div class="nf"><strong>{val(x["value"])}</strong><span class="mono">{e(x["label"])}</span>{f"<p>{e(x[chr(110)+chr(111)+chr(116)+chr(101)])}</p>" if x.get("note") else ""}</div>' for x in SITE["stats"][:4])
    return f"""<section class="numbers">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("In figures")})</span><h2 class="display">{t("The studio in figures")}</h2></div></div>
    <div class="nfs rv">{figs}</div>
  </div>
</section>"""


def pause():
    folder, name = HOME_PAUSE
    p = next((x for x in DATA if x["folder"] == folder), None)
    if not p or not (ROOT / "assets" / "projects" / folder / name).exists():
        return ""
    return f"""<a class="pause" href="{href(p)}" aria-label="{e(p['title'])}"><img src="{img(p, name)}"{rs(p, name, '100vw')} alt="{e(p['title'])}" width="2400" height="1350" loading="lazy"><span class="mono pause-cap">{e(p['title'])} · {e(p['location'])}</span></a>"""


def service_pic(n, sv):
    """Image used for a service: a render from the work that fits it."""
    pr = MAJOR[n % len(MAJOR)] if n < 3 else MAJOR[1 % len(MAJOR)]
    pic = "interior-03.jpg" if "interior" in sv["slug"] else ("exterior-03.jpg" if "animation" in sv["slug"] else ("hero.jpg" if n >= 3 else "exterior-01.jpg"))
    if not (ROOT / "assets" / "projects" / pr["folder"] / pic).exists():
        pic = "hero.jpg"
    return pr, pic


def services_strip():
    """Home: services as a typographic list; the image beside it changes to match the service you point at."""
    rows, pics = [], []
    for n, sv in enumerate(SVCS[:4]):
        pr, pic = service_pic(n, sv)
        pics.append(f'<img class="sl-img{" on" if n == 0 else ""}" data-i="{n}" src="{img(pr, pic)}"{rs(pr, pic, "(max-width:900px) 100vw, 40vw")} alt="" width="1200" height="1500" loading="lazy">')
        rows.append(f"""      <a class="sl-row{' on' if n == 0 else ''}" data-i="{n}" href="{pg('services/' + sv['slug'] + '.html')}">
        <span class="sl-t">{e(sv['short'])}</span>
        <span class="sl-d"><span>{e(sv['lead'])}</span></span>
      </a>""")
    return f"""<section class="svc-list">
  <div class="wrap">
    <div class="sl-top rv"><span class="mono label">({t("Services")})</span><a class="mono ulink" href="{pg('services.html')}">{t("All services →")}</a></div>
    <div class="sl-grid rv">
      <div class="sl-rows">
{chr(10).join(rows)}
      </div>
      <div class="sl-side" aria-hidden="true"><div class="sl-pic">{''.join(pics)}</div>
        <div class="sl-caps">{''.join(f'<p class="sl-cap{" on" if n == 0 else ""}">{e(sv["lead"])}</p>' for n, sv in enumerate(SVCS[:4]))}</div></div>
    </div>
  </div>
</section>"""


def pricing_hook():
    return f"""<section class="price-hook">
  <div class="wrap ph-row rv">
    <div><span class="mono label">({t("Process &amp; pricing")})</span>
      <p class="ph-lead">{t("A closed price and a week-by-week schedule, before we start.")}</p></div>
    <a class="btn" href="{pg('pricing.html')}">{t("See how it works")} <span class="ar">→</span></a>
  </div>
</section>"""


def index_page():
    works = "\n".join(spread(p, n) for n, p in enumerate(MAJOR[:4]))
    svc_items = '<p class="tz-list mono">' + "".join(f'<a href="{pg("services/" + x["slug"] + ".html")}">{e(x["short"])}</a>' for x in SVCS[:4]) + "</p>"
    return head(t("dsgn·dm archviz — Architectural visualization"),
                t("Architectural visualization studio in Santander, Spain. Stills, animation and sales material for architects, developers and interior designers."),
                path="index.html", ld=[org_ld()]) + header(cur="index.html") + f"""
<main id="main">
{hero()}

{statement()}

<section id="work">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Work")})</span><h2 class="display">{t("Selected<br>work")}</h2></div></div>
    <div class="fgrid fgrid-{min(len(MAJOR), 4)}">
{works}
    </div>
    <a class="all-link rv" href="{pg("projects.html")}"><span>{t("All projects")}</span><span class="mono">{num(len(DATA))}</span><span class="ar" aria-hidden="true">→</span></a>
  </div>
</section>

{compare_block()}

{figures()}


{services_strip()}

{pricing_hook()}

{contact_section()}
</main>
""" + footer()


def contact_section(base=""):
    """Slim call to action at the end of every page; the full details and form live on the contact page."""
    return f"""<section class="cta-band">
  <div class="wrap cta-row rv">
    <p class="display">{t("Have a project in <em>mind?</em>")}</p>
    <a class="btn" href="{base}{pg('contact.html')}">{t("Let’s talk")} <span class="ar">→</span></a>
  </div>
</section>"""


def contact_full(base=""):
    return f"""<section id="contact" class="contact">
  <div class="wrap">
    <span class="mono label">({t("Contact")})</span>
    <h2 class="display rv">{t("Have a project in <em>mind?</em>")}</h2>
    <div class="contact-grid rv">
      <p class="contact-lead">{t("Send plans, a location and a deadline. You will receive a closed proposal with a week-by-week schedule.")}</p>
      <div class="contact-list">
        <div class="cblock"><span class="mono">Email</span><button class="reveal" type="button" data-kind="mail" data-reveal="{b64(EMAIL)}">{t("Reveal email")}</button></div>
        <div class="cblock"><span class="mono">{t("Phone")}</span><button class="reveal" type="button" data-kind="tel" data-reveal="{b64(PHONE)}">{t("Reveal phone")}</button></div>
        <div class="cblock"><span class="mono">Portfolio</span><a class="l ulink" href="{BEHANCE}" target="_blank" rel="noopener">Behance ↗</a></div>
        <div class="cblock"><span class="mono">{t("Studio")}</span><a class="l ulink" href="{MAIN_SITE}" target="_blank" rel="noopener">dsgn·dm UX/UI ↗</a></div>
      </div>
    </div>
    {quote_form()}
  </div>
</section>"""


def contact_page():
    return head(t("Contact — dsgn·dm archviz"), t("Send plans, a location and a deadline. You will receive a closed proposal with a week-by-week schedule."),
                path="contact.html", ld=[crumbs([(t("Home"), "index.html"), (t("Contact"), "contact.html")])]) + header("", home="index.html", cur="contact.html") + f"""
<main id="main" class="contact-page">
{contact_full().replace('<h2 class="display rv">', '<h1 class="display rv">', 1).replace('</h2>', '</h1>', 1)}
</main>
""" + footer("")


# ---------------------------------------------------------------- projects index
def projects_page():
    base = ""
    types = []
    for p in DATA:
        if p["type"] not in types:
            types.append(p["type"])
    filters = '<button class="flt on" type="button" data-filter="all">{} <sup>{}</sup></button>'.format(t("All"), len(DATA)) + "".join(
        f'<button class="flt" type="button" data-filter="{e(t(ty))}">{e(t(ty))} <sup>{sum(1 for p in DATA if p["type"] == ty)}</sup></button>' for ty in types)
    cards = "\n".join(pcard(p, heading="h2") for p in DATA)
    return head(t("Projects — dsgn·dm archviz"), t("All architectural visualization projects by dsgn·dm archviz: residential, interiors, exteriors, commercial and animation."), path="projects.html",
                ld=[crumbs([(t("Home"), "index.html"), (t("Projects"), "projects.html")])]) + header("", home="index.html", cur="projects.html") + f"""
<main id="main">
<section class="p-top">
  <div class="wrap">
    <span class="mono label">({t("Projects")})</span>
    <h1 class="display">{t("All<br>projects")}</h1>
    {sorter() if len(DATA) > 6 else ""}
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap"><div class="pgrid ix-body">
{cards}
  </div></div>
</section>
{contact_section()}
</main>
""" + footer("")


# ---------------------------------------------------------------- project page
def gallery_group(p, group, title, base, start_no):
    kinds = p[group]
    if not kinds:
        return "", start_no
    items, total, no = [], 0, start_no
    for k, kind in enumerate(kinds, 1):
        kd = KINDS[kind]
        total += kd["span"]
        name = f"{group}-{k:02d}.jpg"
        items.append(
            f'      <figure class="gi s{kd["span"]} rv"><button class="zoom" type="button" data-full="{img(p, name, base)}" aria-label="{t("Open image")} {no}">'
            f'<img src="{img(p, name, base)}"{rs(p, name, f"(max-width:700px) 100vw, {round(kd["span"] / 12 * 100)}vw", base)} alt="{e(p["title"])} — {t(title).lower()} {k}" width="{kd["w"]}" height="{kd["h"]}" loading="lazy" style="aspect-ratio:{kd["w"]}/{kd["h"]}"></button></figure>')
        no += 1
    if total % 12:
        print(f"  ! {p['slug']} {group}: row spans add up to {total} (not a multiple of 12)")
    out = f"""<section class="gal" id="{group}s">
  <div class="wrap">
    <div class="gal-head rv"><span class="mono label">({t(title)})</span></div>
    <div class="ggrid">
{chr(10).join(items)}
    </div>
  </div>
</section>"""
    return out, no


YT_PARAMS = "autoplay=1&mute=1&controls=0&loop=1&playlist={id}&modestbranding=1&rel=0&playsinline=1&iv_load_policy=3&disablekb=1&fs=0"


def video_block(p, base):
    v = p.get("video")
    if v is None:
        return ""
    if v.get("ambient"):
        # Silent, looping, no controls: plays by itself when it comes into view (YouTube id or an mp4 next to the images)
        yid, src = v.get("youtube", ""), v.get("src", "")
        data = (f' data-yt="https://www.youtube-nocookie.com/embed/{yid}?{YT_PARAMS.format(id=yid)}"' if yid else "") + \
               (f' data-mp4="{ab(base)}assets/projects/{p["folder"]}/{src}"' if src else "")
        link = f'<a class="ulink vlink" href="https://youtu.be/{yid}" target="_blank" rel="noopener">{t("Watch with sound on YouTube")} ↗</a>' if yid else ""
        return f"""<section class="vid" id="video">
  <div class="wrap">
    <div class="gal-head rv"><span class="mono label">({t("Animation")})</span>{link}</div>
    <div class="vframe vamb rv"{data}>
      <img src="{img(p, 'video-poster.jpg', base)}"{rs(p, 'video-poster.jpg', '100vw', base)} alt="{e(p['title'])} — {t("video poster")}" width="1920" height="1080" loading="lazy">
    </div>
  </div>
</section>"""
    src, emb = v.get("src", ""), v.get("embed", "")
    empty = "" if (src or emb) else " data-empty"
    src_attr = f' data-src="{ab(base)}assets/projects/{p["folder"]}/{src}"' if src else ""
    emb_attr = f' data-embed="{e(emb)}"' if emb else ""
    note = '<span class="mono vnote">Placeholder — add video.mp4 or a Vimeo/YouTube link in projects.json</span>' if not (src or emb) else ""
    return f"""<section class="vid" id="video">
  <div class="wrap">
    <div class="gal-head rv"><div><span class="mono label">({t("Animation")})</span></div><span class="mono muted">Full HD · 1920 × 1080 px</span></div>
    <div class="vframe rv"{empty}{src_attr}{emb_attr}>
      {marks()}
      <img src="{img(p, 'video-poster.jpg', base)}"{rs(p, 'video-poster.jpg', '100vw', base)} alt="{e(p['title'])} — {t("video poster")}" width="1920" height="1080" loading="lazy">
      <button class="play" type="button" aria-label="{t("Play video")}"><span></span></button>
      {note}
    </div>
  </div>
</section>"""


def passes_block(p, base):
    if not p.get("passes"):
        return ""
    return f"""<section class="passes" id="passes">
  <div class="wrap">
    <div class="gal-head rv"><div><span class="mono label">({t("Render passes")})</span></div><span class="mono muted">{t("Drag: wireframe → clay → final")}</span></div>
    <div class="pass-view rv">
      {marks()}
      <img class="final" src="{img(p, 'pass-final.jpg', base)}"{rs(p, 'pass-final.jpg', '100vw', base)} alt="{t("Final render")}" width="2400" height="1350" loading="lazy">
      <img class="clay" src="{img(p, 'pass-clay.jpg', base)}"{rs(p, 'pass-clay.jpg', '100vw', base)} alt="{t("Clay render")}" width="2400" height="1350" loading="lazy">
      <img class="wire" src="{img(p, 'pass-wire.jpg', base)}"{rs(p, 'pass-wire.jpg', '100vw', base)} alt="{t("Wireframe")}" width="2400" height="1350" loading="lazy">
    </div>
    <input class="pass-range" type="range" min="0" max="100" value="0" step="1" aria-label="{t("Render passes")}">
    <div class="pass-labels mono"><span>{t("Wireframe")}</span><span>{t("Clay")}</span><span>{t("Final")}</span></div>
  </div>
</section>"""


def about_page():
    principles = [
        ("Light first", "Light decides how a space feels. I tune it early, with test renders, before polishing anything else."),
        ("Honest materials", "Finishes are modelled and lit to read as they will in reality, not as an idealised version of them."),
        ("Calm composition", "Framings follow the architect’s intent, with camera heights chosen the way people will actually see the building."),
        ("Direct contact", "One conversation from the first reference to the final delivery, with clear milestones and no surprises."),
    ]
    pr = "\n".join(f'      <div class="svc rv"><span class="mono n">{num(n + 1)}</span><h3>{t(h)}</h3><p>{t(d)}</p></div>' for n, (h, d) in enumerate(principles))
    steps = "\n".join(f'      <div class="step rv"><span class="mono n">{num(n + 1)}</span><h3>{t(h)}</h3><p>{t(d)}</p></div>' for n, (h, d) in enumerate(STEPS))
    ld = [crumbs([(t("Home"), "index.html"), (t("About"), "about.html")]),
          {"@context": "https://schema.org", "@type": "Person", "name": "Diego Moreno", "jobTitle": t("Architectural visualization artist"),
           "url": canon("about.html", LANG), "sameAs": [BEHANCE, MAIN_SITE], "worksFor": {"@type": "ProfessionalService", "name": SITE_NAME},
           "address": {"@type": "PostalAddress", "addressLocality": "Santander", "addressRegion": "Cantabria", "addressCountry": "ES"}}]
    return head(t("About — dsgn·dm archviz"), t("Meet the studio behind dsgn·dm archviz: Diego Moreno, 16+ years of architectural visualization from Santander."),
                path="about.html", ld=ld) + header("", home="index.html", cur="about.html") + f"""
<main id="main">
<section class="p-top">
  <div class="wrap">
    <span class="mono label">({t("About")})</span>
    <h1 class="display">{t("One person,<br>start to finish.")}</h1>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap studio">
    <figure class="studio-fig rv">
      {portrait()}
    </figure>
    <div class="studio-copy rv">
      <div><p class="studio-lead">{t("Drawings become images that are <em>understood, felt</em> and approved.")}</p></div>
      <p>{t("dsgn·dm archviz is the visualization studio of Diego Moreno, working independently from {link}Santander</a>. Over 16 years creating stills, animation and sales material for architects, developers and interior designers.").replace("{link}", '<a class="ulink" href="' + pg("services/3d-visualization-santander.html") + '">')}</p>
      <p>{t("Every project is handled by me personally, so the person you brief is the person who builds the images.")}</p>
      <dl class="spec mono">
        <dt>{t("Experience")}</dt><dd>16+ {t("years")}</dd>
        <dt>{t("Tools")}</dt><dd>3ds Max · Corona · D5 Render</dd>
        <dt>{t("Disciplines")}</dt><dd>{t("Exteriors")} · {t("Interiors")} · {t("Animation")} · {t("Sales material")}</dd>
        <dt>{t("Base")}</dt><dd>Santander, {t("Spain")}</dd>
      </dl>
    </div>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Principles")})</span><h2 class="display">{t("How I<br>see it")}</h2></div>
      <p style="max-width:34ch;text-align:right">{t("Four ideas that guide every image, whatever the size of the project.")}</p></div>
    <div class="services">
{pr}
    </div>
  </div>
</section>

<section>
  <div class="wrap brief-grid">
    <div class="rv"><span class="mono label">({t("Beyond archviz")})</span></div>
    <p class="brief-lead rv">{t("The same studio also designs interfaces, brands and websites.")}</p>
    <div class="brief-cols rv">
      <div><p>{t("If your project needs more than images — a promotion website, a visual identity for a development — it can all stay in one place.")}</p></div>
      <div><a class="btn" href="{MAIN_SITE}" target="_blank" rel="noopener">dsgn·dm UX/UI <span class="ar">↗</span></a></div>
    </div>
  </div>
</section>

{contact_section()}
</main>
""" + footer("")


def print_page():
    """Printable 16:9 portfolio (rendered to PDF by tools/make_pdf.py). Not linked from the site."""
    B = "../"
    def pimg(p, n):
        return f'<img src="{B}assets/projects/{p["folder"]}/{n}" alt="">'
    def existing(p, names):
        return [n for n in names if (ROOT / "assets" / "projects" / p["folder"] / n).exists()]
    foot = lambda k: f'<div class="foot"><span class="mut">{SITE_NAME}</span><span class="mut">{k}</span></div>'
    pages = [f"""<section class="pg cover">
  <div class="lbl">{t("Portfolio")}</div>
  <h1>{t("Architecture, seen <em>before</em> it’s built.")}</h1>
  <div class="tag"><a class="logo" href="#">{logo("../")}</a><p>{t("Visualization studio of Diego Moreno. Stills, animation and sales material for architects, developers and interior designers.")}</p></div>
</section>"""]
    for p in MAJOR:
        shots = existing(p, [f"exterior-{i:02d}.jpg" for i in (1, 2)] + [f"interior-{i:02d}.jpg" for i in (1, 2)])[:3]
        pages.append(f"""<section class="pg full">{pimg(p, 'hero.jpg')}
  <div class="cap"><div><div class="mut">{e(p['location'])}</div><h2>{e(p['title'])}</h2></div><span class="mut">{e(p['location'])}</span></div>
</section>""")
        if p.get("brief"):
            gallery = "".join(pimg(p, n) for n in shots)
            pages.append(f"""<section class="pg ptext">
  <div class="col"><div class="lbl">({t("Brief")})</div><p>{e(p['brief'])}</p><div class="lbl">({t("Approach")})</div><p>{e(p['approach'])}</p>
    <dl><dt>{t("Location")}</dt><dd>{e(p['location'])}</dd><dt>{t("Software")}</dt><dd>{e(p['software'])}</dd></dl></div>
  <div class="shots">{gallery}</div>{foot(e(p['title']))}
</section>""")
    cards = "".join(f'<div>{pimg(p, "index.jpg")}<div class="cap"><span>{e(p["title"])}</span><span class="mut">{e(t(p["type"]))}</span></div></div>' for p in MINOR)
    if MINOR: pages.append(f"""<section class="pg alt"><div class="lbl">({t("Archive")})</div><h2 style="margin-top:20px">{t("More<br>projects").replace("<br>", " ")}</h2><div class="agrid">{cards}</div></section>""")
    svc = "".join(f'<div><h3>{e(x["short"])}</h3><p>{e(x["lead"])}</p></div>' for x in SVCS[:4])
    pages.append(f"""<section class="pg"><div class="lbl">({t("Services")})</div><h2 style="margin-top:20px">{t("What<br>I do")}</h2><div class="svcs">{svc}</div>{foot(t("Services"))}</section>""")
    web = (SITE_URL.replace("https://", "").replace("http://", "").rstrip("/") + "/" + ("es" if LANG == "es" else "")).rstrip("/") if SITE_URL else MAIN_SITE.replace("https://", "")
    pages.append(f"""<section class="pg alt contact-pg"><div class="lbl">({t("Contact")})</div>
  <div class="big">{t("Have a project in <em>mind?</em>")}</div>
  <div class="rows"><div><span class="mut">Email</span><b>{e(EMAIL)}</b></div><div><span class="mut">{t("Phone")}</span><b>{e(PHONE)}</b></div><div><span class="mut">Web</span><b>{e(web)}</b></div></div>
</section>""")
    return f"""<!doctype html>
<html lang="{LANG}">
<head><meta charset="utf-8"><meta name="robots" content="noindex"><title>{SITE_NAME} — {t("Portfolio")}</title>
<link rel="stylesheet" href="{B}css/style.css"><link rel="stylesheet" href="{B}css/print.css"></head>
<body id="page">
{"".join(pages)}
</body>
</html>
"""


def hero_media(p, base):
    """Hero of a project page: a muted looping video if the project has "loop", otherwise the still."""
    if p.get("loop"):
        return (f'<video data-loop src="{ab(base)}assets/projects/{p["folder"]}/{p["loop"]}" poster="{img(p, "hero.jpg", base)}" '
                f'muted loop playsinline preload="metadata" aria-label="{e(p["title"])}" width="2400" height="1350"></video>')
    return f'<img src="{img(p, "hero.jpg", base)}"{rs(p, "hero.jpg", "(max-width:900px) and (orientation:portrait) 170vh, 100vw", base)} alt="{e(p["title"])}" width="2400" height="1350" fetchpriority="high">'


def story_block(p):
    """Optional case study (challenge / solution / result) for projects that have a "story" in projects.json."""
    st = p.get("story")
    if not st:
        return ""
    cols = "".join(f'<div class="factor"><h3>{t(lbl)}</h3><p>{e(st[k])}</p></div>' for k, lbl in (("challenge", "Challenge"), ("solution", "Solution"), ("result", "Result")) if st.get(k))
    return f"""<section class="story"><div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Case study")})</span></div></div>
    <div class="story-cols rv">{cols}</div>
  </div></section>"""


def quote_block(p):
    q = p.get("quote")
    if not q:
        return ""
    return f"""<section class="pquote"><div class="wrap rv"><blockquote>{e(q['text'])}</blockquote>
    <p class="mono"><span>{e(q.get('name', ''))}</span> <span class="muted">{e(q.get('role', ''))}</span></p></div></section>"""


def project_page(p):
    base = "../"
    i = DATA.index(p)
    nxt = DATA[(i + 1) % len(DATA)]
    n_ext, n_int = len(p["exterior"]), len(p["interior"])
    scope = [s for s, ok in (("Exteriors", n_ext), ("Interiors", n_int), ("Animation", p.get("video") is not None)) if ok]
    delivered = []
    if n_ext: delivered.append(f"{n_ext} " + t("exterior still" if n_ext == 1 else "exterior stills"))
    if n_int: delivered.append(f"{n_int} " + t("interior still" if n_int == 1 else "interior stills"))
    if p.get("video") is not None: delivered.append(t("1 video, Full HD"))
    meta = ([(t("Type"), t(p["type"]))] if SHOW_TYPE else []) + [
            (t("Scope"), " · ".join(t(x) for x in scope)), (t("Software"), p["software"]), (t("Client"), p["client"])]
    dl = "".join(f'<div><dt class="mono">{k}</dt><dd>{e(v)}</dd></div>' for k, v in meta)

    text = "".join(f"<p>{e(x)}</p>" for x in (p.get("brief"), p.get("approach")) if x) or f"<p>{e(p['summary'])}</p>"
    brief = f"""<section class="p-info" id="brief">
  <div class="wrap p-info-grid">
    <dl class="p-meta">{dl}</dl>
    <div class="p-text rv">{text}</div>
  </div>
</section>"""

    ext, no = gallery_group(p, "exterior", "Exteriors", base, 1)
    inter, no = gallery_group(p, "interior", "Interiors", base, no)
    # video before stills for the animation-first project
    first_video = p["type"] == "Animation"
    body = [brief, story_block(p)]
    if first_video:
        body += [video_block(p, base), ext, inter]
    else:
        body += [video_block(p, base), ext, inter]
    body += [passes_block(p, base), quote_block(p)]

    prv = DATA[(i - 1) % len(DATA)]
    return head(t("{title} — {type} visualization | dsgn·dm archviz").format(title=p["title"], type=t(p["type"]).lower() if LANG == "es" else t(p["type"])), p.get("description") or p["summary"], base, path=f"projects/{p['slug']}.html", og=f"assets/projects/{p['folder']}/hero.jpg",
                ld=[crumbs([(t("Home"), "index.html"), (t("Projects"), "projects.html"), (p["title"], f"projects/{p['slug']}.html")])]) + header(base, cur=f"projects/{p['slug']}.html") + f"""
<main id="main">
<section class="p-cover">
    <div class="p-hero on-img"><div class="ph-in">{hero_media(p, base)}</div>
      <div class="hx-shade" aria-hidden="true"></div>
      <div class="pc-title"><h1 class="display">{e(p['title'])}</h1><span class="mono">{e(p['location'])}</span></div>
    </div>
</section>
{chr(10).join(b for b in body if b)}
<section class="next-sec">
  <div class="wrap">
    <a class="p-next" href="{nxt['slug']}.html">
      <span class="frame"><img src="{img(nxt, 'hero.jpg', base)}"{rs(nxt, 'hero.jpg', '100vw', base)} alt="" width="2400" height="1350" loading="lazy"></span>
      <span class="hx-shade" aria-hidden="true"></span>
      <span class="pn-cap"><span class="mono">{t("Next project")}</span><span class="pn-t">{e(nxt['title'])} <span class="ar">→</span></span></span>
    </a>
  </div>
</section>
{contact_section(base)}
</main>
<div class="lightbox" aria-hidden="true">
  <button class="lb-close mono" type="button">{t("Close")}</button>
  <button class="lb-prev mono" type="button" aria-label="{t("Previous")}">←</button>
  <img alt="">
  <button class="lb-next mono" type="button" aria-label="{t("Next")}">→</button>
  <span class="lb-count mono"></span>
</div>
""" + footer(base)


# ---------------------------------------------------------------- extra: form, trust, pricing, services, SEO
def ph(t):
    """Text in [ brackets ] is a placeholder: render muted so it is obvious it still needs content."""
    return f'<span class="phold">{e(t)}</span>' if t.startswith("[") else e(t)


def quote_form():
    opts = lambda xs: "".join(f"<option>{e(x)}</option>" for x in xs)
    return f"""<form class="quote rv" data-to="{b64(EMAIL)}" data-endpoint="{e(FORM_ENDPOINT)}">
      <span class="mono label">({t("Send a brief")})</span>
      <div class="q-grid">
        <label><span class="mono">{t("Name")}</span><input name="name" required autocomplete="name"></label>
        <label><span class="mono">Email</span><input type="email" name="email" required autocomplete="email"></label>
        <label><span class="mono">{t("Project type")}</span><select name="type">{opts([t(x) for x in ["Exterior images", "Interior images", "Animation", "Sales material", "A bit of everything", "Not sure yet"]])}</select></label>
        <label><span class="mono">{t("Timeline")}</span><select name="timeline">{opts([t(x) for x in ["Flexible", "Within a month", "1 to 2 months", "Urgent — under 2 weeks"]])}</select></label>
        <label class="wide"><span class="mono">{t("Link to plans or references (Drive, WeTransfer…)")}</span><input type="url" name="link" placeholder="https://"></label>
        <label class="wide"><span class="mono">{t("Message")}</span><textarea name="message" rows="4" required></textarea></label>
        <input class="hp" name="company" tabindex="-1" autocomplete="off" aria-hidden="true">
      </div>
      <div class="q-foot"><button class="btn" type="submit">{t("Send brief")} <span class="ar">→</span></button><span class="q-status mono" role="status"></span></div>
    </form>"""


def trust_section():
    stats = "".join(f'<div class="fig"><strong class="display">{ph(x["value"])}</strong><span class="mono">{e(x["label"])}</span></div>' for x in SITE["stats"])
    clients = "".join(f'<div class="client mono">{ph(c)}</div>' for c in SITE["clients"])
    quotes = "".join(f'<figure class="quote-card"><blockquote>{ph(t["quote"])}</blockquote><figcaption class="mono"><span>{ph(t["name"])}</span><span class="muted">{ph(t["role"])}</span></figcaption></figure>' for t in SITE["testimonials"])
    return f"""<section id="proof">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Clients")})</span><h2 class="display">{t("Worked<br>with")}</h2></div>
      <p style="max-width:34ch;text-align:right">{t("Architects, developers and interior designers who trust me with their projects.")}</p></div>
    <div class="figs rv">{stats}</div>
    <div class="clients rv">{clients}</div>
    <div class="quotes rv">{quotes}</div>
  </div>
</section>"""


def org_ld():
    return {"@context": "https://schema.org", "@type": "ProfessionalService", "name": SITE_NAME, "url": canon("index.html", LANG),
            "image": abs_url("assets/og.jpg"), "description": t("Architectural visualization studio: stills, animation and sales material for architects, developers and interior designers."), "inLanguage": LANG,
            "founder": {"@type": "Person", "name": "Diego Moreno"},
            "address": {"@type": "PostalAddress", "addressLocality": "Santander", "addressRegion": "Cantabria", "addressCountry": "ES"},
            "areaServed": ["Cantabria", t("Spain")], "sameAs": [BEHANCE, MAIN_SITE]}


def pricing_page():
    P = SITE["pricing"]
    steps = "\n".join(f'      <div class="step rv"><span class="mono n">{num(n + 1)}</span><h3>{t(h)}</h3><p>{t(d)}</p></div>' for n, (h, d) in enumerate(STEPS))
    rows = "\n".join(f"""      <div class="prow rv"><span class="mono n">{num(n + 1)}</span>
        <div class="pname"><h3>{e(tr['name'])}</h3><p>{e(tr['desc'])}</p></div>
        <ul class="mono">{''.join(f'<li>{e(i)}</li>' for i in tr['includes'])}</ul>
        <div class="pfrom"><strong class="display">{ph(tr['from'])}</strong><span class="mono muted">{t("Typical time")} · {ph(tr['time'])}</span></div></div>""" for n, tr in enumerate(P["tiers"]))
    extras = "".join(f'<div class="xrow"><div><h3>{e(n)}</h3><p>{e(d)}</p></div><strong class="display">{ph(pr)}</strong></div>' for n, d, pr in P["extras"])
    factors = "".join(f'<div class="factor"><h3>{e(a)}</h3><p>{e(b)}</p></div>' for a, b in P["factors"])
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    faqs = "\n".join(f'        <details><summary><span class="mono n">{num(n + 1)}</span>{t(q)}</summary><p>{t(a)}</p></details>' for n, (q, a) in enumerate(FAQS))
    return head(t("Process & pricing — dsgn·dm archviz"), t("How an architectural visualization project works with dsgn·dm archviz, what is included, what affects the price and what to send to get a proposal."),
                path="pricing.html", ld=[crumbs([(t("Home"), "index.html"), (t("Process & pricing"), "pricing.html")]), faq_ld()]) + header("", home="index.html", cur="pricing.html") + f"""
<main id="main">
<section class="p-top">
  <div class="wrap">
    <span class="mono label">({t("Process &amp; pricing")})</span>
    <h1 class="display">{t("Process &amp;<br>pricing")}</h1>
    <p class="lead rv">{e(P['intro'])}</p>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Formats")})</span><h2 class="display">{t("From<br>price")}</h2></div></div>
    <div class="ptable">
{rows}
    </div>
    <p class="mono muted pnote rv">{t("Starting points, not final quotes. VAT not included.")}</p>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Add-ons")})</span><h2 class="display">{t("Optional<br>extras")}</h2></div></div>
    <div class="xlist rv">{extras}</div>
  </div>
</section>

<section class="workflow">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Process")})</span><h2 class="display">{t("How we<br>work")}</h2></div></div>
    <div class="timeline">
{steps}
    </div>
  </div>
</section>

<section>
  <div class="wrap brief-grid">
    <div class="rv"><span class="mono label">({t("Included")})</span></div>
    <div class="brief-cols rv">
      <div><p class="brief-lead" style="margin-bottom:28px">{t("Every project includes")}</p><ul class="mono">{li(P['included'])}</ul></div>
      <div><span class="mono label">({t("What I need from you")})</span><ul class="mono">{li(P['needs'])}</ul></div>
    </div>
  </div>
</section>

<section style="padding-top:0">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Price factors")})</span><h2 class="display">{t("What changes<br>the price")}</h2></div></div>
    <div class="factors rv">{factors}</div>
  </div>
</section>

<section id="faq" style="padding-top:0">
  <div class="wrap faq">
    <div class="faq-aside rv"><span class="mono label">(FAQ)</span><h2 class="display">{t("Good<br>questions")}</h2></div>
    <div class="faq-list rv">
{faqs}
    </div>
  </div>
</section>

{contact_section()}
</main>
""" + footer("")


def services_page():
    """Overview of the services: one large row per service, each with an image from the work, linking to its page."""
    rows = []
    for n, sv in enumerate(SVCS[:4]):
        pr, pic = service_pic(n, sv)
        inc = "".join(f"<li>{e(x)}</li>" for x in sv["includes"][:4])
        rows.append(f"""    <a class="svrow rv{' flip' if n % 2 else ''}" href="{pg('services/' + sv['slug'] + '.html')}">
      <span class="frame"><img src="{img(pr, pic)}"{rs(pr, pic, '(max-width:900px) 100vw, 50vw')} alt="" width="1800" height="1200" loading="lazy"></span>
      <span class="sv-body"><span class="sv-top"><span class="sv-t">{e(sv['short'])}</span><span class="sv-lead">{e(sv['lead'])}</span></span>
        <span class="sv-bot"><ul class="mono">{inc}</ul><span class="mono sv-go">{t("Learn more")} <span class="ar">→</span></span></span></span>
    </a>""")
    local = SVCS[4] if len(SVCS) > 4 else None
    loc_line = f"""<section class="teaser"><div class="wrap tz rv"><span class="mono label">(Santander)</span><div class="tz-body"><p class="tz-lead">{e(local['lead'])}</p><a class="mono ulink" href="{pg('services/' + local['slug'] + '.html')}">{e(local['short'])} →</a></div></div></section>""" if local else ""
    return head(t("Services — dsgn·dm archviz"), t("Architectural visualization services: exterior and interior renders, animation and sales material for developments, from Santander, Spain."),
                path="services.html", ld=[crumbs([(t("Home"), "index.html"), (t("Services"), "services.html")])]) + header("", home="index.html", cur="services.html") + f"""
<main id="main">
<section class="p-top">
  <div class="wrap">
    <span class="mono label">({t("Services")})</span>
    <h1 class="display">{t("What<br>I do")}</h1>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap svlist">
{chr(10).join(rows)}
  </div>
</section>
{loc_line}
{contact_section()}
</main>
""" + footer("")


def service_page(sv):
    base = "../"
    li = lambda xs: "".join(f"<li>{e(x)}</li>" for x in xs)
    rel = [p for p in DATA if p["type"] in sv["types"]][:3]
    cards = "\n".join(pcard(p, base) for p in rel)
    faqs = "\n".join(f'        <details><summary><span class="mono n">{num(n + 1)}</span>{e(q)}</summary><p>{e(a)}</p></details>' for n, (q, a) in enumerate(sv["faqs"]))
    path = f"services/{sv['slug']}.html"
    ld = [crumbs([(t("Home"), "index.html"), (t("Services"), "index.html#services"), (sv["short"], path)]),
          {"@context": "https://schema.org", "@type": "Service", "name": sv["title"], "description": sv["meta"], "areaServed": ["Cantabria", t("Spain")], "inLanguage": LANG,
           "provider": {"@type": "ProfessionalService", "name": SITE_NAME, "url": canon("index.html", LANG)}}]
    others = "".join(f'<a href="{posixpath.basename(pg("services/" + x["slug"] + ".html"))}">{e(x["short"])}</a>' for x in SVCS if x["slug"] != sv["slug"])
    return head(f"{sv['title']} | dsgn·dm archviz", sv["meta"], base, path=path, ld=ld) + header(base, cur=path) + f"""
<main id="main">
<section class="p-top">
  <div class="wrap">
    <a class="back mono ulink" href="{base}index.html#services">{t("← Services")}</a>
    <h1 class="display">{e(sv['title'])}</h1>
  </div>
</section>
<section class="brief">
  <div class="wrap brief-grid">
    <div class="rv"><span class="mono label">({t("Overview")})</span></div>
    <p class="brief-lead rv">{e(sv['lead'])}</p>
    <div class="brief-cols rv">
      <div><span class="mono label">({t("What you get")})</span><ul class="mono">{li(sv['includes'])}</ul></div>
      <div><span class="mono label">({t("Useful for")})</span><ul class="mono">{li(sv['usefulFor'])}</ul></div>
    </div>
  </div>
</section>
{"" if not rel else f'''<section style="padding-top:0">
  <div class="wrap">
    <div class="sec-head rv"><div><span class="mono label">({t("Related work")})</span><h2 class="display">{t("Selected<br>projects")}</h2></div>
      <a class="mono ulink" href="{base}{pg("projects.html")}">{t("All projects →")}</a></div>
    <div class="pgrid">
{cards}
    </div>
  </div>
</section>'''}
<section class="cta-mini">
  <div class="wrap cta-row rv">
    <p class="display">{t("What would it cost?")}</p>
    <a class="btn" href="{base}{pg("pricing.html")}">{t("Process &amp; pricing")} <span class="ar">→</span></a>
  </div>
</section>
<section id="faq">
  <div class="wrap faq">
    <div class="faq-aside rv"><span class="mono label">(FAQ)</span><h2 class="display">{t("Good<br>questions")}</h2>
      <p class="svc-others mono">{t("Also:")} {others}</p></div>
    <div class="faq-list rv">
{faqs}
    </div>
  </div>
</section>
{contact_section(base)}
</main>
""" + footer(base)


def seo_files():
    if not SITE_URL:
        print("  ! SITE_URL is empty: canonical URLs, hreflang, social previews, structured data and sitemap.xml are skipped. Set it in build.py.")
        return
    set_lang("en")
    logical = ["index.html", "projects.html", "services.html", "about.html", "pricing.html", "contact.html"] + [f"services/{x['slug']}.html" for x in SVCS] + [f"projects/{p['slug']}.html" for p in DATA]
    ent = []
    for pth in logical:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{canon(pth, l)}"/>' for l in ("en", "es"))
        ent += [f"  <url><loc>{canon(pth, l)}</loc>{alts}</url>" for l in ("en", "es")]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(ent) + "\n</urlset>\n", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {abs_url('sitemap.xml')}\n", encoding="utf-8")


def main():
    for lang in ("en", "es"):
        set_lang(lang)
        out = ROOT / "es" if lang == "es" else ROOT
        (ROOT / "print").mkdir(exist_ok=True)
        for d in ("projects", "services") if lang == "en" else ("proyectos", "servicios"):
            (out / d).mkdir(parents=True, exist_ok=True)
        files = {loc("index.html", lang): index_page(), loc("projects.html", lang): projects_page(), loc("pricing.html", lang): pricing_page(),
                 loc("about.html", lang): about_page(), loc("services.html", lang): services_page(), loc("contact.html", lang): contact_page()}
        for sv in SVCS:
            files[loc(f"services/{sv['slug']}.html", lang)] = service_page(sv)
        for p in DATA:
            files[loc(f"projects/{p['slug']}.html", lang)] = project_page(p)
        files[f"print/{lang}.html"] = print_page()
        for f, content in files.items():
            # section headings on one line: the <br> in "What<br>I do" becomes a space (they still wrap on small screens)
            content = re.sub(r'(<h[12][^>]*class="[^"]*display[^"]*"[^>]*>)(.*?)(</h[12]>)', lambda m: m.group(1) + m.group(2).replace("<br>", " ") + m.group(3), content, flags=re.S)
            (ROOT / f).write_text(content, encoding="utf-8")
        print(f"OK [{lang}]: {len(files)} pages")
    seo_files()
    if MISSING:
        print(f"  ! {len(MISSING)} strings without Spanish translation (data/ui.es.json):")
        for m in sorted(MISSING):
            print("    -", m[:110])


if __name__ == "__main__":
    main()
