import argparse
import logging
from datetime import datetime, timezone

from .classifier import keyword_prefilter, llm_verify
from .config import load_sources
from .db import select, upsert
from .extractor import extract
from .fetcher import fetch_source

log = logging.getLogger(__name__)


def _yaml_sources_as_targets() -> list[dict]:
    """Charge config/sources.yaml en format unifié 'crawl target'."""
    return [
        {
            "kind": "source",
            "key": s["id"],
            "venue_id": None,
            "name": s["name"],
            "url": s["url"],
            "paths": s.get("paths"),
            "dept": s.get("dept"),
        }
        for s in load_sources()
    ]


def _venue_targets() -> list[dict]:
    """Charge les venues crawlable=true depuis Supabase."""
    rows = select(
        "venues",
        select="id,name,url,dept,category,city",
        crawlable="eq.true",
        url="not.is.null",
    )
    return [
        {
            "kind": "venue",
            "key": None,
            "venue_id": v["id"],
            "name": v["name"],
            "url": v["url"],
            "paths": None,
            "dept": v["dept"],
        }
        for v in rows
    ]


def _build_targets(include_venues: bool, only: str | None) -> list[dict]:
    targets = _yaml_sources_as_targets()
    if include_venues:
        targets += _venue_targets()
    if only:
        targets = [t for t in targets if t["key"] == only or t["venue_id"] == only]
        if not targets:
            raise SystemExit(f"target {only!r} not found")
    return targets


def run(only: str | None = None, skip_llm: bool = False, include_venues: bool = False):
    targets = _build_targets(include_venues, only)
    log.info("crawling %d target(s) — include_venues=%s", len(targets), include_venues)

    n_kept = 0
    for target in targets:
        log.info("target=%s (%s)", target["name"], target["kind"])
        try:
            pages = fetch_source({"url": target["url"], "paths": target.get("paths")})
        except Exception as e:
            log.error("fetch failed: %s", e)
            continue

        for page in pages:
            title, text = extract(page["html"])
            if not text or not keyword_prefilter(title + "\n" + text):
                continue

            if skip_llm:
                verdict = type("V", (), {
                    "is_tremplin": True, "confidence": 0.5,
                    "title": title, "summary": None, "deadline": None, "location": None,
                })()
            else:
                verdict = llm_verify(page["url"], title, text)

            if not verdict.is_tremplin or verdict.confidence < 0.5:
                continue

            _upsert_tremplin(
                url=page["url"],
                source_id=target["key"],
                venue_id=target["venue_id"],
                dept=target.get("dept"),
                title=verdict.title or title or page["url"],
                summary=verdict.summary,
                deadline=verdict.deadline,
                location=verdict.location,
                confidence=verdict.confidence,
                content_hash=page["content_hash"],
            )
            n_kept += 1
            log.info("  ✓ %s", verdict.title)

    log.info("done — %d tremplins kept", n_kept)


def _upsert_tremplin(**row):
    """UPSERT via PostgREST. On omet first_seen (DEFAULT now() à l'insert,
    intouché à l'update) et les colonnes None pour préserver l'existant.
    """
    row["last_seen"] = datetime.now(timezone.utc).isoformat()
    body = {k: v for k, v in row.items() if v is not None}
    upsert("tremplins", [body], on_conflict="url")


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--only", help="ne crawl qu'une source/venue (id YAML ou uuid)")
    p.add_argument("--skip-llm", action="store_true", help="dev — bypass LLM")
    p.add_argument(
        "--include-venues", action="store_true",
        help="mode exhaustif : crawl aussi les venues crawlable=true (~4100 URLs)",
    )
    args = p.parse_args()
    run(only=args.only, skip_llm=args.skip_llm, include_venues=args.include_venues)


if __name__ == "__main__":
    main()
