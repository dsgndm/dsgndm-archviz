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
  var imgs = [].slice.call(document.querySelectorAll(".work .frame, .pcard .frame, .spread .frame, .gi, .vframe, .studio-fig .frame, .hx-frame"));
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
  var imgZones = [].slice.call(document.querySelectorAll(".on-img"));
  function onScroll() {
    header.classList.toggle("scrolled", window.scrollY > 24);
    /* light header while it sits over a full-bleed image */
    var mid = header.offsetHeight / 2, over = false;
    imgZones.forEach(function (z) { var r = z.getBoundingClientRect(); if (r.top <= mid && r.bottom >= mid) over = true; });
    header.classList.toggle("over-img", over && !document.querySelector(".mobile-menu.open"));
  }
  onScroll(); window.addEventListener("scroll", onScroll, { passive: true });

  /* Mobile menu */
  var btn = document.querySelector(".menu-btn"), menu = document.querySelector(".mobile-menu");
  if (btn) btn.addEventListener("click", function () { setTimeout(onScroll, 0); });
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
      imgs.forEach(function (im, k) {
        var on = k === i;
        if (on && !im.classList.contains("on")) { im.style.animation = "none"; void im.offsetWidth; im.style.animation = ""; } /* restart the mobile pan */
        im.classList.toggle("on", on);
      });
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

  /* Project index: sort by number, name or location (FLIP so rows glide to their new place) */
  var ixb = document.querySelector(".ix-body");
  if (ixb) {
    var sorts = [].slice.call(document.querySelectorAll(".ix-sort"));
    sorts.forEach(function (bt) {
      bt.addEventListener("click", function () {
        var k = bt.dataset.sort, rows = [].slice.call(ixb.children);
        var first = rows.map(function (r) { return r.getBoundingClientRect().top; });
        rows.slice().sort(function (a, b) {
          return k === "n" ? a.dataset.n - b.dataset.n : a.dataset[k].localeCompare(b.dataset[k], document.documentElement.lang) || a.dataset.n - b.dataset.n;
        }).forEach(function (r) { ixb.appendChild(r); });
        if (!reduce) rows.forEach(function (r, i) {
          var dy = first[i] - r.getBoundingClientRect().top;
          if (!dy) return;
          r.classList.remove("moving"); r.style.transform = "translateY(" + dy + "px)";
          requestAnimationFrame(function () { r.classList.add("moving"); r.style.transform = ""; });
        });
        sorts.forEach(function (o) { o.classList.toggle("on", o === bt); o.setAttribute("aria-pressed", o === bt); });
      });
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
    var cards = document.querySelectorAll(".pcard");
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
    /* Browsers with cross-document view transitions: the clicked image becomes the next page's cover */
    if ("onpagereveal" in window) return; /* the browser crossfades the pages itself */
    e.preventDefault();
    document.body.classList.add("leaving");
    setTimeout(function () { location.href = u.href; }, 300);
  });
  window.addEventListener("pageshow", function (e) {
    if (e.persisted) document.body.classList.remove("leaving");
    [].forEach.call(document.querySelectorAll("[style*=view-transition-name]"), function (el) { el.style.viewTransitionName = ""; });
  });
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



/* ===== Studio portrait made of particles (raw WebGL, no library), as on dsgndm.com =====
   Particles sit in place and fade in when the section arrives; the centre is dense, the rim disperses;
   some particles fade out and back in; the pointer pushes them very softly.
   No WebGL -> the still drawing stays. Reduced motion -> one static frame. */
(function () {
  "use strict";
  var figs = [].slice.call(document.querySelectorAll(".pp"));
  if (!figs.length || !("IntersectionObserver" in window)) return;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var COLOR_VAR = "--ink"; /* "--blue" for the blue version */

  function rgb(c) {
    c = (c || "#11152A").trim().replace("#", "");
    if (c.length === 3) c = c.replace(/(.)/g, "$1$1");
    var n = parseInt(c, 16);
    return [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255];
  }

  var VS = "attribute vec2 aUv;attribute vec4 aR;uniform vec2 uK,uMouse;uniform float uPush,uTime,uPR,uAsp,uFade;varying float vA;" +
    "void main(){vec2 p=vec2(aUv.x*2.-1.,-(aUv.y*2.-1.))*uK;float edge=aR.w;" +
    "p+=vec2(sin(uTime*(.35+aR.y*.5)+aR.x*6.283),cos(uTime*(.3+aR.z*.5)+aR.y*6.283))*(.0022+.018*edge);" +
    "vec2 dm=(p-uMouse)*vec2(uAsp,1.);float r=length(dm);float f=smoothstep(.5,0.,r);" +
    "p+=normalize(dm+vec2(1e-4))/vec2(uAsp,1.)*f*f*(.025+.035*aR.y)*uPush;" +
    "float tw=step(.62,aR.z);float ph=.5+.5*sin(uTime*(.4+aR.x*.9)+aR.y*40.);" +
    "vA=(.8+.2*aR.x)*mix(1.,smoothstep(.15,.85,ph),tw)*(1.-.4*edge)*uFade;" +
    "gl_Position=vec4(p,0.,1.);gl_PointSize=(1.5+aR.y*1.4)*uPR;}";
  var FS = "precision mediump float;uniform vec3 uColor;varying float vA;" +
    "void main(){float r=length(gl_PointCoord-.5);if(r>.5)discard;gl_FragColor=vec4(uColor,vA*smoothstep(.5,.15,r));}";

  function build(fig) {
    var cv = fig.querySelector("canvas"), still = fig.querySelector(".pp-still"), gl = null;
    try { gl = cv.getContext("webgl", { alpha: true, antialias: false, premultipliedAlpha: false }); } catch (e) {}
    if (!gl) return;
    var img = new Image();
    img.onload = function () {
      var W = 360, H = Math.round(W * img.height / img.width), iA = img.width / img.height;
      var oc = document.createElement("canvas"); oc.width = W; oc.height = H;
      var cx = oc.getContext("2d"); cx.drawImage(img, 0, 0, W, H);
      var d; try { d = cx.getImageData(0, 0, W, H).data; } catch (e) { return; }
      var pts = [];
      for (var y = 0; y < H; y++) for (var x = 0; x < W; x++) if (d[(y * W + x) * 4 + 3] > 60) pts.push(x, y);
      var max = innerWidth < 700 ? 9000 : 18000, total = pts.length / 2;
      if (!total) return;
      var step = Math.max(1, total / max), n = Math.floor(total / step);
      var uv = new Float32Array(n * 2), rr = new Float32Array(n * 4);
      for (var i = 0; i < n; i++) {
        var k = Math.floor(i * step) * 2, u = (pts[k] + Math.random() - .5) / W, v = (pts[k + 1] + Math.random() - .5) / H;
        var dx = (u - .5) * 2, dy = (v - .5) * 2, dist = Math.sqrt(dx * dx + dy * dy);
        var edge = Math.max(0, Math.min(1, (dist - .5) / .45));           /* 0 in the face, 1 at the circle */
        var j = (.0015 + .03 * edge * edge) * (Math.random() - .5) * 2, ang = Math.random() * 6.283;
        uv[i * 2] = u + Math.cos(ang) * j; uv[i * 2 + 1] = v + Math.sin(ang) * j * iA;
        rr[i * 4] = Math.random(); rr[i * 4 + 1] = Math.random(); rr[i * 4 + 2] = Math.random(); rr[i * 4 + 3] = edge;
      }
      function sh(t, src) { var o = gl.createShader(t); gl.shaderSource(o, src); gl.compileShader(o); return o; }
      var pr = gl.createProgram();
      gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) return;
      gl.useProgram(pr);
      function attr(name, data, size) {
        var b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
        var l = gl.getAttribLocation(pr, name); gl.enableVertexAttribArray(l); gl.vertexAttribPointer(l, size, gl.FLOAT, false, 0, 0);
      }
      attr("aUv", uv, 2); attr("aR", rr, 4);
      var U = {}; ["uK", "uMouse", "uPush", "uTime", "uPR", "uAsp", "uFade", "uColor"].forEach(function (nm) { U[nm] = gl.getUniformLocation(pr, nm); });
      gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      function setCol() { var col = rgb(getComputedStyle(document.documentElement).getPropertyValue(COLOR_VAR)); gl.useProgram(pr); gl.uniform3f(U.uColor, col[0], col[1], col[2]); }
      setCol();
      window.addEventListener("dm-theme", function () { setCol(); if (!raf) draw(performance.now()); });

      var mouse = [9, 9], tm = [9, 9], push = 0, target = 0, fade = reduce ? 1 : 0, fadeTo = reduce ? 1 : 0, visible = false, raf = 0;
      function draw(now) {
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
        gl.uniform1f(U.uTime, reduce ? 0 : now / 1000); gl.uniform2f(U.uMouse, mouse[0], mouse[1]);
        gl.uniform1f(U.uPush, push); gl.uniform1f(U.uFade, fade);
        gl.drawArrays(gl.POINTS, 0, n);
      }
      function size() {
        var w = fig.clientWidth, h = fig.clientHeight, dpr = Math.min(window.devicePixelRatio || 1, 2);
        cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); gl.viewport(0, 0, cv.width, cv.height);
        var cA = w / h, pad = .9, kx, ky;
        if (iA > cA) { kx = pad; ky = pad * cA / iA; } else { ky = pad; kx = pad * iA / cA; }
        gl.uniform2f(U.uK, kx, ky); gl.uniform1f(U.uAsp, cA); gl.uniform1f(U.uPR, dpr * Math.max(.75, w / 520));
        if (!raf) draw(performance.now());
      }
      function loop(now) {
        raf = visible ? requestAnimationFrame(loop) : 0;
        mouse[0] += (tm[0] - mouse[0]) * .1; mouse[1] += (tm[1] - mouse[1]) * .1;
        push += (target - push) * .04; fade += (fadeTo - fade) * .045;
        draw(now);
      }
      size(); new ResizeObserver(size).observe(fig);
      if (still) still.style.opacity = "0";
      fig.classList.add("pp-on");
      if (reduce) return;
      new IntersectionObserver(function (es) {
        es.forEach(function (e) {
          visible = e.isIntersecting;
          if (visible) { fadeTo = 1; if (!raf) raf = requestAnimationFrame(loop); }
        });
      }, { threshold: .2 }).observe(fig);
      function move(ev) {
        var r = fig.getBoundingClientRect();
        tm[0] = ((ev.clientX - r.left) / r.width) * 2 - 1; tm[1] = -(((ev.clientY - r.top) / r.height) * 2 - 1);
        if (push < .01) { mouse[0] = tm[0]; mouse[1] = tm[1]; }
        target = 1;
      }
      fig.addEventListener("pointermove", move); fig.addEventListener("pointerdown", move);
      fig.addEventListener("pointerleave", function () { target = 0; });
    };
    img.src = fig.getAttribute("data-src");
  }

  var lazy = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { lazy.unobserve(e.target); build(e.target); } });
  }, { rootMargin: "300px 0px" });
  figs.forEach(function (f) { lazy.observe(f); });
})();


/* ===== Theme switch: light / dark, remembered; the new theme opens in a circle from the switch ===== */
(function () {
  "use strict";
  var root = document.documentElement, sws = [].slice.call(document.querySelectorAll(".theme-sw"));
  if (!sws.length) return;
  function sync() {
    var dark = root.getAttribute("data-theme") === "dark";
    sws.forEach(function (b) { b.setAttribute("aria-checked", dark ? "true" : "false"); });
  }
  function apply(theme) {
    root.setAttribute("data-theme", theme);
    try { localStorage.setItem("dm-theme", theme); } catch (e) {}
    sync();
    window.dispatchEvent(new CustomEvent("dm-theme", { detail: theme }));
  }
  sws.forEach(function (b) {
    b.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!document.startViewTransition || reduce) { apply(next); return; }
      var r = b.getBoundingClientRect();
      root.style.setProperty("--tx", (r.left + r.width / 2) + "px");
      root.style.setProperty("--ty", (r.top + r.height / 2) + "px");
      root.classList.add("theme-anim");
      var vt = document.startViewTransition(function () { apply(next); });
      vt.finished.then(function () { root.classList.remove("theme-anim"); }, function () { root.classList.remove("theme-anim"); });
    });
  });
  /* follow the system while the visitor has not chosen */
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
    var saved = null; try { saved = localStorage.getItem("dm-theme"); } catch (x) {}
    if (!saved) { root.setAttribute("data-theme", e.matches ? "dark" : "light"); sync(); window.dispatchEvent(new CustomEvent("dm-theme")); }
  });
  sync();
})();


/* ===== Featured cards: each frame cycles its images with a horizontal wipe, staggered, only while visible ===== */
(function () {
  "use strict";
  var cards = [].slice.call(document.querySelectorAll(".fcard"));
  if (!cards.length || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  cards.forEach(function (c, n) {
    var imgs = [].slice.call(c.querySelectorAll(".fc-img")), dots = [].slice.call(c.querySelectorAll(".fc-dots i"));
    if (imgs.length < 2) return;
    var i = 0, vis = false, timer = null;
    imgs.forEach(function (im) { im.loading = "eager"; });
    function next() {
      var cur = imgs[i]; i = (i + 1) % imgs.length; var nx = imgs[i];
      imgs.forEach(function (im) { if (im !== cur) im.classList.remove("prev"); });
      cur.classList.remove("on"); cur.classList.add("prev");
      nx.classList.remove("prev"); nx.style.animation = "none"; void nx.offsetWidth; nx.style.animation = ""; nx.classList.add("on");
      dots.forEach(function (d, k) { d.classList.toggle("on", k === i); });
    }
    function run() { stop(); if (vis && !document.hidden) timer = setTimeout(function tick() { next(); timer = setTimeout(tick, 4200); }, 2600 + n * 1300); }
    function stop() { if (timer) clearTimeout(timer); timer = null; }
    new IntersectionObserver(function (es) { vis = es[0].isIntersecting; vis ? run() : stop(); }, { threshold: .35 }).observe(c);
    document.addEventListener("visibilitychange", function () { document.hidden ? stop() : run(); });
  });
})();


/* ===== Before / after: drag (or use the arrow keys) to compare; a small hint the first time it appears ===== */
(function () {
  "use strict";
  [].forEach.call(document.querySelectorAll(".ba"), function (box) {
    var r = box.querySelector(".ba-range");
    function set(v) { box.style.setProperty("--x", v + "%"); }
    r.addEventListener("input", function () { set(r.value); });
    if (matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return;
      io.disconnect();
      var t0 = performance.now();
      (function hint(now) {
        var k = Math.min(1, (now - t0) / 1800), e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
        var v = 50 + Math.sin(e * Math.PI) * 22;
        set(v); r.value = v;
        if (k < 1) requestAnimationFrame(hint);
      })(t0);
    }, { threshold: .6 });
    io.observe(box);
  });
})();


/* ===== Home services list: the row you point at (or focus) opens and swaps the image beside it ===== */
(function () {
  "use strict";
  var rows = [].slice.call(document.querySelectorAll(".sl-row")), imgs = [].slice.call(document.querySelectorAll(".sl-img"));
  var caps = [].slice.call(document.querySelectorAll(".sl-cap"));
  if (!rows.length) return;
  var cur = 0;
  imgs.forEach(function (im) { im.loading = "eager"; });
  function show(i) {
    if (i === cur) return;
    rows.forEach(function (r, k) { r.classList.toggle("on", k === i); });
    caps.forEach(function (c, k) { c.classList.toggle("on", k === i); });
    imgs.forEach(function (im, k) { im.classList.remove("prev"); if (k === cur) { im.classList.remove("on"); im.classList.add("prev"); } });
    var nx = imgs[i]; nx.style.animation = "none"; void nx.offsetWidth; nx.style.animation = ""; nx.classList.add("on");
    cur = i;
  }
  rows.forEach(function (r, k) {
    r.addEventListener("mouseenter", function () { show(k); });
    r.addEventListener("focus", function () { show(k); });
  });
})();
