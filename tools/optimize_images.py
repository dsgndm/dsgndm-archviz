#!/usr/bin/env python3
"""Creates WebP versions of every JPG/PNG in assets/ at several widths, next to the originals:
    hero.jpg  ->  hero-480.webp  hero-960.webp  hero-1600.webp  hero-2400.webp
The originals are never touched. python3 build.py then serves them automatically with srcset
(browsers pick the lightest file that still looks sharp); the JPG stays as fallback and in the lightbox.
Run it whenever you drop in new renders.
Usage: python3 tools/optimize_images.py [--quality 80] [--force]"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WIDTHS = [480, 960, 1600, 2400]
quality = int(sys.argv[sys.argv.index("--quality") + 1]) if "--quality" in sys.argv else 80
force = "--force" in sys.argv


def main():
    made = saved = 0
    for src in sorted((ROOT / "assets").rglob("*")):
        if src.suffix.lower() not in (".jpg", ".jpeg", ".png") or src.parent.name == "fonts" or src.name == "og.jpg":
            continue
        im = Image.open(src)
        im = im.convert("RGB") if im.mode not in ("RGB", "L") else im
        ws = sorted({w for w in WIDTHS if w < im.width} | {im.width if im.width <= max(WIDTHS) else max(WIDTHS)})
        for old in src.parent.glob(f"{src.stem}-*.webp"):  # drop variants from a previous, differently sized original
            tail = old.stem.rsplit("-", 1)[1]
            if tail.isdigit() and int(tail) not in ws:
                old.unlink()
        for w in ws:
            out = src.with_name(f"{src.stem}-{w}.webp")
            if out.exists() and not force and out.stat().st_mtime >= src.stat().st_mtime:
                continue
            r = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
            r.save(out, "WEBP", quality=quality, method=6)
            made += 1
        biggest = src.with_name(f"{src.stem}-{ws[-1]}.webp")
        saved += max(0, src.stat().st_size - biggest.stat().st_size)
    print(f"{made} WebP files written. Approx. saving on the largest variants: {saved / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
