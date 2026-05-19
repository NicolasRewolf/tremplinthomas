import argparse
import logging
from datetime import datetime, timezone

from .classifier import keyword_prefilter, llm_verify
from .config import load_sources
from .db import connect
from .extractor import extract
from .fetcher import fetch_source
from .site import render

log = logging.getLogger(__name__)


def run(only: str | None = None, skip_llm: bool = False):
    sources = load_sources()
    if only:
        sources = [s for s in sources if s["id"] == only]
        if not sources:
            raise SystemExit(f"source {only!r} not found in config/sources.yaml")

    n_kept = 0

    for source in sources:
        log.info("source=%s", source["id"])
        try:
            pages = fetch_source(source)
        except Exception as e:
            log.error("fetch failed for %s: %s", source["id"], e)
            continue

        for page in pages:
            title, text = extract(page["html"])
            if not text:
                continue
            if not keyword_prefilter(title + "\n" + text):
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
                source_id=source["id"],
                dept=source.get("dept"),
                title=verdict.title or title or page["url"],
                summary=verdict.summary,
                deadline=verdict.deadline,
                location=verdict.location,
                confidence=verdict.confidence,
                content_hash=page["content_hash"],
            )
            n_kept += 1
            log.info("  kept: %s", verdict.title)

    log.info("done — %d tremplins kept this run", n_kept)
    render()


def _upsert_tremplin(**row):
    """Upsert via ON CONFLICT — préserve first_seen, met à jour last_seen."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            insert into public.tremplins
              (url, source_id, dept, title, summary, deadline, location,
               confidence, content_hash, first_seen, last_seen)
            values
              (%(url)s, %(source_id)s, %(dept)s, %(title)s, %(summary)s,
               %(deadline)s, %(location)s, %(confidence)s, %(content_hash)s,
               now(), now())
            on conflict (url) do update set
              title        = excluded.title,
              summary      = excluded.summary,
              deadline     = excluded.deadline,
              location     = excluded.location,
              confidence   = excluded.confidence,
              content_hash = excluded.content_hash,
              last_seen    = now()
            """,
            row,
        )


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--only", help="run a single source by id")
    p.add_argument("--skip-llm", action="store_true", help="dev mode — bypass LLM verification")
    args = p.parse_args()
    run(only=args.only, skip_llm=args.skip_llm)


if __name__ == "__main__":
    main()
