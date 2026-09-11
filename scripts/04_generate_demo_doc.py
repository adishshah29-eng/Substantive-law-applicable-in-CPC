"""
Converts data/demo/rajesh_sharma_v_priya_enterprises.md to PDF via
weasyprint, saving to data/demo/rajesh_sharma_v_priya_enterprises.pdf.
"""
from __future__ import annotations

from pathlib import Path

import markdown
from weasyprint import HTML

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "data" / "demo"
SOURCE_MD = DEMO_DIR / "rajesh_sharma_v_priya_enterprises.md"
OUTPUT_PDF = DEMO_DIR / "rajesh_sharma_v_priya_enterprises.pdf"

CSS = """
@page { size: A4; margin: 2.5cm; }
body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt; line-height: 1.5; }
h1 { font-size: 16pt; }
h2 { font-size: 13pt; margin-top: 1.5em; }
h3 { font-size: 11.5pt; font-style: italic; }
"""


def main() -> None:
    md_text = SOURCE_MD.read_text()
    body_html = markdown.markdown(md_text, extensions=["extra"])
    html = f"<html><head><style>{CSS}</style></head><body>{body_html}</body></html>"
    HTML(string=html).write_pdf(str(OUTPUT_PDF))
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
