"""Re-fetch et re-classifie un tremplin par URL avec le classifier actuel.

Utile quand le crawler ne revisite plus une page (par ex. parce qu'elle est
archivée et plus liée depuis la home), ou quand on a amélioré le classifier
et qu'on veut rejouer sur des rows legacy.

Usage :
    python scripts/reclassify_url.py https://le-rim.org/mewem-2023-candidatures-ouvertes/
    python scripts/reclassify_url.py --all-stale     # toutes les rows legacy
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.classifier import keyword_prefilter, llm_verify  # noqa: E402
from tremplins.db import select, upsert  # noqa: E402
from tremplins.extractor import extract  # noqa: E402
from tremplins.fetcher import _get  # noqa: E402
import httpx  # noqa: E402

log = logging.getLogger(__name__)


def reclassify_one(url: str) -> None:
    log.info("reclassify %s", url)
    with httpx.Client(headers={"User-Agent": "tremplins-na/0.1"}, timeout=30.0) as client:
        try:
            r = _get(client, url)
        except Exception as e:
            log.error("  fetch failed: %s", e)
            return
        html = r.text

    title, text = extract(html)
    if not text:
        log.warning("  extraction failed (no text)")
        return
    if not keyword_prefilter(title + "\n" + text):
        log.info("  keyword prefilter rejected — keeping row untouched")
        return

    verdict = llm_verify(url, title, text)
    if not verdict.is_tremplin:
        log.info("  LLM says not a tremplin — skipping")
        return

    row = {
        "url": url,
        "title": verdict.title or title or url,
        "summary": verdict.summary,
        "deadline": verdict.deadline,
        "edition_year": verdict.edition_year,
        "location": verdict.location,
        "confidence": verdict.confidence,
        "status": verdict.status,
        "reasoning": verdict.reasoning,
        "last_seen": datetime.now(timezone.utc).isoformat(),
    }
    body = {k: v for k, v in row.items() if v is not None}
    upsert("tremplins", [body], on_conflict="url")
    tag = {"open": "✓", "closed": "✗", "unknown": "?"}.get(verdict.status, "·")
    log.info("  %s [%s] %s", tag, verdict.status, verdict.title)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("url", nargs="?", help="URL d'un tremplin à reclasser")
    p.add_argument(
        "--all-stale", action="store_true",
        help="rejoue sur toutes les rows sans edition_year ni reasoning (legacy Haiku)",
    )
    args = p.parse_args()

    if args.all_stale:
        rows = select("tremplins", select="url", edition_year="is.null", reasoning="is.null")
        log.info("found %d legacy rows", len(rows))
        for r in rows:
            reclassify_one(r["url"])
    elif args.url:
        reclassify_one(args.url)
    else:
        p.error("fournis une URL ou --all-stale")


if __name__ == "__main__":
    main()
