import hashlib
import logging
from urllib.parse import urljoin, urlparse
import httpx
from selectolax.parser import HTMLParser
from tenacity import retry, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)
UA = "tremplins-na/0.1 (+veille musicale Nouvelle-Aquitaine)"
TIMEOUT = 20.0


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _get(client: httpx.Client, url: str) -> httpx.Response:
    r = client.get(url, follow_redirects=True, timeout=TIMEOUT)
    r.raise_for_status()
    return r


def fetch_source(source: dict) -> list[dict]:
    """Fetch a source's home + extra paths. Returns [{url, html, content_hash}, ...]."""
    base = source["url"]
    paths = source.get("paths") or []
    targets = [base] + [urljoin(base, p) for p in paths]

    out = []
    with httpx.Client(headers={"User-Agent": UA}) as client:
        for url in targets:
            try:
                r = _get(client, url)
            except Exception as e:
                log.warning("fetch failed %s: %s", url, e)
                continue
            html = r.text
            h = hashlib.sha256(html.encode("utf-8", "ignore")).hexdigest()
            out.append({"url": str(r.url), "html": html, "content_hash": h})

            # opportunistic: surface internal links that look promising
            for extra in _candidate_links(html, str(r.url)):
                if extra in {p["url"] for p in out}:
                    continue
                try:
                    r2 = _get(client, extra)
                except Exception:
                    continue
                out.append({
                    "url": str(r2.url),
                    "html": r2.text,
                    "content_hash": hashlib.sha256(r2.text.encode("utf-8", "ignore")).hexdigest(),
                })
    return out


LINK_HINTS = ("tremplin", "candidature", "appel", "concours", "selection", "sélection")


def _candidate_links(html: str, base: str, limit: int = 5) -> list[str]:
    tree = HTMLParser(html)
    base_netloc = urlparse(base).netloc
    seen: list[str] = []
    for a in tree.css("a[href]"):
        href = a.attributes.get("href") or ""
        text = (a.text() or "").lower()
        url = urljoin(base, href)
        if urlparse(url).netloc != base_netloc:
            continue
        haystack = (href + " " + text).lower()
        if any(k in haystack for k in LINK_HINTS) and url not in seen:
            seen.append(url)
            if len(seen) >= limit:
                break
    return seen
