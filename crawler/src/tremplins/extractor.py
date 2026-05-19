import trafilatura
from selectolax.parser import HTMLParser


def extract(html: str) -> tuple[str, str]:
    """Return (title, plain_text). Falls back gracefully if trafilatura yields nothing."""
    title = ""
    tree = HTMLParser(html)
    t = tree.css_first("title")
    if t:
        title = (t.text() or "").strip()

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_recall=True,
    ) or ""
    if not text:
        body = tree.body
        text = (body.text(separator="\n") if body else "").strip()
    return title, text
