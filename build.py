"""Wrap index.html (the Artifact source, no <html> shell) into full pages.

Writes "Waggle Story.html" (opens by double-click) and docs/index.html (served by GitHub Pages).
"""
from pathlib import Path

here = Path(__file__).parent
body = (here / "index.html").read_text(encoding="utf-8")
desc = "What Waggle is, why it is being built, how it works and what makes it different from a chatbot."
shell = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    f'<meta name="description" content="{desc}">\n'
    '<meta property="og:title" content="What Is Waggle?">\n'
    f'<meta property="og:description" content="{desc}">\n'
    '<meta name="theme-color" content="#0c0406">\n'
    "<style>body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
    "</head>\n<body>\n" + body + "\n</body>\n</html>\n"
)
(here / "docs").mkdir(exist_ok=True)
for out in (here / "Waggle Story.html", here / "docs" / "index.html"):
    out.write_text(shell, encoding="utf-8", newline="\n")
    print("wrote", out, len(shell), "bytes")
