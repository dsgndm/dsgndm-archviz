#!/usr/bin/env python3
"""Renders the printable portfolio (print/en.html, print/es.html) to PDF with Chrome via Playwright.
    python3 build.py && python3 tools/make_pdf.py
Output: portfolio-dsgndm-en.pdf and portfolio-dsgndm-es.pdf in the project folder (16:9 pages, 1920 x 1080 px).
Needs: pip install playwright (Chromium or system Chrome). Use --chrome /path/to/chrome to pick a browser."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
chrome = sys.argv[sys.argv.index("--chrome") + 1] if "--chrome" in sys.argv else None


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch(args=["--no-sandbox"])
        for lang in ("en", "es"):
            pg = b.new_page()
            pg.goto((ROOT / "print" / f"{lang}.html").as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_function("[...document.images].every(i => i.complete)")
            out = ROOT / f"portfolio-dsgndm-{lang}.pdf"
            pg.pdf(path=str(out), width="1920px", height="1080px", print_background=True, prefer_css_page_size=True)
            print(f"{out.name}: {out.stat().st_size / 1e6:.1f} MB")
        b.close()


if __name__ == "__main__":
    main()
