var DM_ES = document.documentElement.lang === "es";
/* ===== Micro-interactions: prepare (runs first, before the reveal observer) ===== */
(function () {
  "use strict";
  var root = document.documentElement;
  window.__dm = 1;
  var animate = root.classList.contains("anim") && "IntersectionObserver" in window;
  if (!animate) { root.classList.remove("anim"); return; }

  function watch(nodes, opts) {
    var o = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); o.unobserve(e.target); } });
    }, opts);
    nodes.forEach(function (n) { o.observe(n); });
  }

  /* Headings: split into words, each rising out of a mask */
  function split(h) {
    var i = 0, walker = document.createTreeWalker(h, NodeFilter.SHOW_TEXT, null), nodes = [], n;
    while ((n = walker.nextNode())) nodes.push(n);
    nodes.forEach(function (t) {
      var frag = document.createDocumentFragment();
      t.nodeValue.split(/(\s+)/).forEach(function (s) {
        if (!s) return;
        if (/^\s+$/.test(s)) { frag.appendChild(document.createTextNode(" ")); return; }
        var w = document.createElement("span"), inner = document.createElement("span");
        w.className = "w"; inner.className = "w-i"; inner.style.setProperty("--i", i++);
        inner.textContent = s; w.appendChild(inner); frag.appendChild(w);
      });
      t.parentNode.replaceChild(frag, t);
    });
    h.classList.add("split");
  }
  var heads = [].slice.call(document.querySelectorAll("h1.display, h2.display"));
  heads.forEach(function (h) { h.classList.remove("rv"); split(h); });
  watch(heads, { threshold: 0.2 });

  /* Images: wipe open when they enter the viewport */
  var imgs = [].slice.call(document.querySelectorAll(".work .frame, .icard .frame, .gi, .p-hero, .vframe, .studio-fig .frame, .hx-frame"));
  imgs.forEach(function (el) { el.classList.remove("rv"); el.classList.add("imgrev"); });
  watch(imgs, { threshold: 0.12, rootMargin: "0px 0px -4% 0px" });

  /* Timeline line draws itself */
  var draws = [].slice.call(document.querySelectorAll(".timeline"));
  draws.forEach(function (el) { el.classList.add("draw"); });
  watch(draws, { threshold: 0.3 });
})();

/* dsgn·dm archviz — behaviour (vanilla JS) */
(function () {
  "use strict";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Header: solid on scroll */
  var header = document.querySelector(".site-header");
  function onScroll() { header.classList.toggle("scrolled", window.scrollY > 24); }
  onScroll(); window.addEventListener("scroll", onScroll, { passive: true });

  /* Mobile menu */
  var btn = document.querySelector(".menu-btn"), menu = document.querySelector(".mobile-menu");
  if (btn && menu) {
    btn.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      btn.textContent = open ? (DM_ES ? "Cerrar" : "Close") : (DM_ES ? "Menú" : "Menu");
      document.body.style.overflow = open ? "hidden" : "";
    });
    menu.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        menu.classList.remove("open"); btn.textContent = DM_ES ? "Menú" : "Menu"; document.body.style.overflow = "";
      });
    });
  }

  /* Hero: project index drives the image */
  var stage = document.querySelector(".hx-stage");
  if (stage) {
    var imgs = [].slice.call(stage.querySelectorAll(".hx-img"));
    var items = [].slice.call(document.querySelectorAll(".hx-item"));
    var capN = stage.querySelector(".hx-n"), capT = stage.querySelector(".hx-t"),
        capD = stage.querySelector(".hx-d"), capL = stage.querySelector(".hx-l");
    var i = 0, timer = null, DUR = 6000;
    function show(n) {
      i = (n + imgs.length) % imgs.length;
      imgs.forEach(function (im, k) { im.classList.toggle("on", k === i); });
      items.forEach(function (it, k) {
        it.classList.remove("on");
        if (k === i) { void it.offsetWidth; it.classList.add("on"); }
      });
      var it = items[i];
      capN.textContent = "Fig. " + String(i + 1).padStart(2, "0");
      capT.textContent = it.dataset.title;
      capD.textContent = it.dataset.dims;
      capL.href = it.dataset.href;
    }
    function start() { stop(); if (!reduce) timer = setInterval(function () { show(i + 1); }, DUR); }
    function stop() { if (timer) clearInterval(timer); }
    items.forEach(function (it, k) {
      it.addEventListener("click", function () { show(k); start(); });
      it.addEventListener("mouseenter", function () { if (window.matchMedia("(hover:hover)").matches) { show(k); start(); } });
    });
    document.addEventListener("visibilitychange", function () { document.hidden ? stop() : start(); });
    show(0); start();
  }

  /* Reveal on scroll */
  var rv = document.querySelectorAll(".rv");
  if ("IntersectionObserver" in window && !reduce) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { threshold: 0.1, rootMargin: "0px 0px -6% 0px" });
    rv.forEach(function (el) { io.observe(el); });
  } else { rv.forEach(function (el) { el.classList.add("in"); }); }

  /* Archive: cursor-following preview */
  var prev = document.querySelector(".preview");
  if (prev && window.matchMedia("(hover: hover)").matches) {
    var pimg = prev.querySelector("img"), x = 0, y = 0, cx = 0, cy = 0, raf = null;
    function loop() { cx += (x - cx) * 0.16; cy += (y - cy) * 0.16; prev.style.left = cx + "px"; prev.style.top = cy + "px"; raf = requestAnimationFrame(loop); }
    document.querySelectorAll(".row[data-img]").forEach(function (row) {
      row.addEventListener("mouseenter", function (e) { pimg.src = row.dataset.img; x = cx = e.clientX + 40; y = cy = e.clientY; prev.classList.add("on"); if (!raf) loop(); });
      row.addEventListener("mousemove", function (e) { x = e.clientX + 40; y = e.clientY; });
      row.addEventListener("mouseleave", function () { prev.classList.remove("on"); cancelAnimationFrame(raf); raf = null; });
    });
  }

  /* Click-to-reveal contact */
  document.querySelectorAll("[data-reveal]").forEach(function (b) {
    b.addEventListener("click", function () {
      var v = atob(b.dataset.reveal);
      if (b.dataset.kind === "mail") b.outerHTML = '<a class="l ulink" href="mailto:' + v + '">' + v + "</a>";
      else b.outerHTML = '<a class="l ulink" href="tel:+34' + v + '">' + v.replace(/(\d{3})(\d{2})(\d{2})(\d{2})/, "$1 $2 $3 $4") + "</a>";
    });
  });
})();

/* ===== Project pages ===== */
(function () {
  "use strict";

  /* Projects index: filter */
  var flts = document.querySelectorAll(".flt");
  if (flts.length) {
    var cards = document.querySelectorAll(".icard");
    flts.forEach(function (b) {
      b.addEventListener("click", function () {
        flts.forEach(function (x) { x.classList.toggle("on", x === b); });
        var f = b.dataset.filter;
        cards.forEach(function (c) { c.hidden = !(f === "all" || c.dataset.type === f); });
      });
    });
  }

  /* Video: load real source on click (mp4 or embed) */
  document.querySelectorAll(".vframe").forEach(function (v) {
    var btn = v.querySelector(".play");
    btn.addEventListener("click", function () {
      var src = v.dataset.src, emb = v.dataset.embed, el;
      if (src) {
        el = document.createElement("video");
        el.src = src; el.controls = true; el.autoplay = true; el.playsInline = true;
        el.poster = v.querySelector("img").src;
      } else if (emb) {
        el = document.createElement("iframe");
        el.src = emb + (emb.indexOf("?") > -1 ? "&" : "?") + "autoplay=1";
        el.allow = "autoplay; fullscreen; picture-in-picture"; el.allowFullscreen = true;
      } else { return; }
      v.appendChild(el); btn.remove();
    });
  });

  /* Lightbox */
  var lb = document.querySelector(".lightbox");
  if (lb) {
    var zooms = [].slice.call(document.querySelectorAll(".zoom")), cur = 0;
    var lbimg = lb.querySelector("img"), count = lb.querySelector(".lb-count");
    function open(n) {
      cur = (n + zooms.length) % zooms.length;
      lbimg.src = zooms[cur].dataset.full;
      count.textContent = String(cur + 1).padStart(2, "0") + " / " + String(zooms.length).padStart(2, "0");
      lb.classList.add("open"); lb.setAttribute("aria-hidden", "false"); document.body.style.overflow = "hidden";
    }
    function close() { lb.classList.remove("open"); lb.setAttribute("aria-hidden", "true"); document.body.style.overflow = ""; }
    zooms.forEach(function (z, k) { z.addEventListener("click", function () { open(k); }); });
    lb.querySelector(".lb-close").addEventListener("click", close);
    lb.querySelector(".lb-prev").addEventListener("click", function () { open(cur - 1); });
    lb.querySelector(".lb-next").addEventListener("click", function () { open(cur + 1); });
    lb.addEventListener("click", function (e) { if (e.target === lb) close(); });
    document.addEventListener("keydown", function (e) {
      if (!lb.classList.contains("open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") open(cur - 1);
      if (e.key === "ArrowRight") open(cur + 1);
    });
  }

  /* Render passes: wireframe → clay → final */
  var pv = document.querySelector(".pass-view");
  if (pv) {
    var range = document.querySelector(".pass-range"), wire = pv.querySelector(".wire"), clay = pv.querySelector(".clay");
    function setPass() {
      var v = parseFloat(range.value);
      var w = Math.max(0, Math.min(1, v / 50)), c = Math.max(0, Math.min(1, (v - 50) / 50));
      wire.style.clipPath = "inset(0 " + (w * 100) + "% 0 0)";
      clay.style.clipPath = v < 50 ? "inset(0 0 0 0)" : "inset(0 " + (c * 100) + "% 0 0)";
      wire.style.display = v >= 50 ? "none" : "block";
    }
    range.addEventListener("input", setPass); setPass();
  }
})();


/* ===== Micro-interactions: progress, parallax, cursor, page transitions ===== */
(function () {
  "use strict";
  var root = document.documentElement, animate = root.classList.contains("anim");
  var header = document.querySelector(".site-header"), bar = null;
  if (header) { bar = document.createElement("div"); bar.className = "sprog"; header.appendChild(bar); }

  /* Scroll progress + hero parallax (one rAF-throttled handler) */
  var hero = document.querySelector(".p-hero"), heroImg = hero && hero.querySelector("img, video"), ticking = false;
  function frame() {
    ticking = false;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (bar) bar.style.setProperty("--p", max > 0 ? Math.min(1, window.scrollY / max).toFixed(4) : 0);
    if (animate && heroImg) {
      var r = hero.getBoundingClientRect(), vh = window.innerHeight;
      if (r.bottom > -100 && r.top < vh + 100) {
        var p = (r.top + r.height / 2 - vh / 2) / (vh / 2 + r.height / 2);
        p = Math.max(-1, Math.min(1, p));
        heroImg.style.setProperty("--py", (-p * 4).toFixed(2) + "%");
      }
    }
  }
  window.addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(frame); } }, { passive: true });
  window.addEventListener("resize", frame);
  frame();

  if (!animate) return;

  /* Cursor label: "View" on project cards, "Expand" on gallery images */
  if (window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    document.querySelectorAll(".work, .icard").forEach(function (el) { el.dataset.cursor = DM_ES ? "Ver" : "View"; });
    document.querySelectorAll(".gi .zoom").forEach(function (el) { el.dataset.cursor = DM_ES ? "Ampliar" : "Expand"; });
    var cur = document.createElement("div"); cur.className = "cur"; cur.setAttribute("aria-hidden", "true");
    var lab = document.createElement("span"); cur.appendChild(lab); document.body.appendChild(cur);
    var tx = 0, ty = 0, cx = 0, cy = 0, raf = null, active = false;
    function tick() {
      cx += (tx - cx) * 0.2; cy += (ty - cy) * 0.2;
      var ox = cx + 88 > window.innerWidth ? -88 : 20;
      cur.style.transform = "translate3d(" + (cx + ox) + "px," + (cy + 20) + "px,0)";
      raf = active ? requestAnimationFrame(tick) : null;
    }
    document.addEventListener("mousemove", function (e) {
      tx = e.clientX; ty = e.clientY;
      if (active && !raf) raf = requestAnimationFrame(tick);
    });
    document.addEventListener("mouseover", function (e) {
      var t = e.target.closest && e.target.closest("[data-cursor]");
      if (!t) return;
      lab.textContent = t.dataset.cursor;
      if (!active) { cx = tx = e.clientX; cy = ty = e.clientY; active = true; tick(); }
      cur.classList.add("on");
    });
    document.addEventListener("mouseout", function (e) {
      var from = e.target.closest && e.target.closest("[data-cursor]");
      if (!from) return;
      var to = e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest("[data-cursor]");
      if (to === from) return;
      if (!to) { active = false; cur.classList.remove("on"); }
    });
  }

  /* Page transitions: fade out before following an internal link */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if ((a.target && a.target !== "_self") || a.hasAttribute("download")) return;
    var u = new URL(a.href, location.href);
    if (u.protocol !== location.protocol || (u.protocol !== "file:" && u.origin !== location.origin)) return;
    if (u.pathname === location.pathname && u.search === location.search) return;
    e.preventDefault();
    document.body.classList.add("leaving");
    setTimeout(function () { location.href = u.href; }, 300);
  });
  window.addEventListener("pageshow", function (e) { if (e.persisted) document.body.classList.remove("leaving"); });
})();


/* ===== Quote form: POST to an endpoint if configured, otherwise open the visitor's email app ===== */
(function () {
  "use strict";
  var f = document.querySelector("form.quote");
  if (!f) return;
  var st = f.querySelector(".q-status");
  f.addEventListener("submit", function (e) {
    e.preventDefault();
    var d = new FormData(f);
    if (d.get("company")) return; /* honeypot */
    var ep = f.dataset.endpoint;
    if (ep) {
      st.textContent = DM_ES ? "Enviando…" : "Sending…";
      fetch(ep, { method: "POST", body: d, headers: { Accept: "application/json" } })
        .then(function (r) { if (!r.ok) throw 0; f.reset(); st.textContent = DM_ES ? "Gracias — te responderé en breve." : "Thank you — I will get back to you soon."; })
        .catch(function () { st.textContent = DM_ES ? "Algo ha fallado. Inténtalo de nuevo o usa el email de arriba." : "Something went wrong. Please try again or use the email above."; });
      return;
    }
    var L = DM_ES ? ["Nombre", "Email", "Proyecto", "Plazo", "Archivos", "Consulta de proyecto"] : ["Name", "Email", "Project", "Timeline", "Files", "Project enquiry"];
    var body = [L[0] + ": " + d.get("name"), L[1] + ": " + d.get("email"), L[2] + ": " + d.get("type"), L[3] + ": " + d.get("timeline"),
      L[4] + ": " + (d.get("link") || "—"), "", d.get("message")].join("\n");
    location.href = "mailto:" + atob(f.dataset.to) + "?subject=" + encodeURIComponent(L[5] + " — " + d.get("type")) + "&body=" + encodeURIComponent(body);
    st.textContent = DM_ES ? "Se abrirá tu app de correo con el briefing listo para enviar." : "Your email app should open with the brief ready to send.";
  });
})();


/* ===== Looping hero videos (play only when visible and active; never with reduced motion) ===== */
(function () {
  "use strict";
  var vids = [].slice.call(document.querySelectorAll("video[data-loop]"));
  if (!vids.length || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  function sync(v) {
    var active = !v.classList.contains("hx-img") || v.classList.contains("on");
    if (v._vis && active) { var p = v.play(); if (p && p.catch) p.catch(function () {}); } else v.pause();
  }
  vids.forEach(function (v) {
    v._vis = false;
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (es) { v._vis = es[0].isIntersecting; sync(v); }, { threshold: 0.01 }).observe(v);
    } else { v._vis = true; sync(v); }
    new MutationObserver(function () { sync(v); }).observe(v, { attributes: true, attributeFilter: ["class"] });
  });
})();

/* ===== Sticky contact button on small screens: shown after scrolling, hidden while the contact section is visible ===== */
(function () {
  "use strict";
  var b = document.querySelector(".sticky-cta");
  if (!b) return;
  var contact = document.getElementById("contact"), inContact = false;
  function update() { b.classList.toggle("show", window.scrollY > 500 && !inContact); }
  if (contact && "IntersectionObserver" in window) {
    new IntersectionObserver(function (es) { inContact = es[0].isIntersecting; update(); }).observe(contact);
  }
  window.addEventListener("scroll", update, { passive: true });
  update();
})();
