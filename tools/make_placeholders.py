#!/usr/bin/env python3
"""Generates dimension-labelled placeholders at the exact pixel size each slot expects.
Existing files are never overwritten (use --force to regenerate).
Replace any file with the real render keeping the same name and proportions.
Usage: python3 tools/make_placeholders.py [--force]"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FORCE = "--force" in sys.argv
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
TINTS = [(226, 231, 241), (222, 229, 240), (230, 233, 241), (219, 227, 239), (228, 231, 238)]
LINE = (178, 189, 211)
INK = (46, 58, 98)
BLUE = (30, 51, 255)


def ph(w, h, ratio, role, name, tint, play=False):
    img = Image.new("RGB", (w, h), tint)
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / h
        c = tuple(int(tint[i] + (255 - tint[i]) * 0.35 * (1 - k)) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    lw = max(1, w // 1600)
    d.line([(0, 0), (w, h)], fill=LINE, width=lw)
    d.line([(0, h), (w, 0)], fill=LINE, width=lw)
    s = max(11, int(min(w, h * 1.4) / 26))
    big = ImageFont.truetype(MONO, int(s * 1.9))
    mid = ImageFont.truetype(MONO, s)
    lines = [(f"{w} × {h} px", big, BLUE), (f"{ratio}  ·  {role}", mid, INK), (name, mid, INK)]
    widths = [d.textlength(t, font=f) for t, f, _ in lines]
    pw, ph_ = max(widths) + s * 2.4, int(s * 1.9) + s * 2 + s * 3.4
    x0, y0 = (w - pw) / 2, (h - ph_) / 2
    d.rectangle([x0, y0, x0 + pw, y0 + ph_], fill=tint)
    y = y0 + s * 1.2
    for (t, f, col), tw in zip(lines, widths):
        d.text(((w - tw) / 2, y), t, font=f, fill=col)
        y += f.size + s * 0.8
    return img


def save(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not FORCE:
        return 0
    img.save(path, "JPEG", quality=84, optimize=True, progressive=True)
    return 1


def main():
    cfg = json.loads((ROOT / "data" / "projects.json").read_text(encoding="utf-8"))
    kinds, data = cfg["kinds"], cfg["projects"]
    n = 0
    for i, p in enumerate(data):
        t = TINTS[i % len(TINTS)]
        base = ROOT / "assets" / "projects" / p["folder"]
        f = p["folder"]
        n += save(ph(2400, 1350, "16:9", "Hero", f"{f}/hero.jpg", t), base / "hero.jpg")
        n += save(ph(1200, 800, "3:2", "Index card", f"{f}/index.jpg", t), base / "index.jpg")
        n += save(ph(480, 320, "3:2", "Thumb", f"{f}/thumb.jpg", t), base / "thumb.jpg")
        if p["tier"] == "major":
            c = p["card"]
            n += save(ph(c["w"], c["h"], c["ratio"], "Home card", f"{f}/card.jpg", t), base / "card.jpg")
        for group in ("exterior", "interior"):
            for k, kind in enumerate(p[group], 1):
                kd = kinds[kind]
                name = f"{group}-{k:02d}.jpg"
                n += save(ph(kd["w"], kd["h"], kd["ratio"], f"{group.capitalize()} · {kind}", f"{f}/{name}", t), base / name)
        if p.get("video") is not None:
            n += save(ph(1920, 1080, "16:9", "Video poster · Full HD", f"{f}/video-poster.jpg", t), base / "video-poster.jpg")
        if p.get("passes"):
            for label, fname in (("Wireframe", "pass-wire.jpg"), ("Clay", "pass-clay.jpg"), ("Final", "pass-final.jpg")):
                n += save(ph(2400, 1350, "16:9", f"Render pass · {label}", f"{f}/{fname}", t), base / fname)
    n += save(ph(1200, 1500, "4:5", "Studio portrait", "brand/studio.jpg", TINTS[1]), ROOT / "assets" / "brand" / "studio.jpg")
    print(f"{n} placeholders generated")


if __name__ == "__main__":
    main()
