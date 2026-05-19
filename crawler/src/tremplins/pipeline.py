import argparse
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

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
            "city": None,
            "category": s.get("type"),
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
            "city": v["city"],
            "category": v["category"],
        }
        for v in rows
    ]


def _normalize_url(url: str) -> str:
    """Pour dédupe : retire trailing slash, scheme http vs https, www."""
    p = urlparse(url.lower())
    netloc = p.netloc.lstrip("www.")
    path = p.path.rstrip("/")
    return f"{netloc}{path}"


def _dedupe_by_url(targets: list[dict]) -> list[dict]:
    """Évite de crawler 3× la même URL (cas ADIE qui a 3 antennes avec
    www.adie.org). On garde le premier target, en notant les "alias" pour
    info dans les logs."""
    seen: dict[str, dict] = {}
    aliases: dict[str, list[str]] = {}
    for t in targets:
        if not t["url"]:
            continue
        key = _normalize_url(t["url"])
        if key in seen:
            aliases.setdefault(key, []).append(t["name"])
            continue
        seen[key] = t
    for key, alist in aliases.items():
        log.info("dedupe %s : %d alias (%s)", key, len(alist), ", ".join(alist[:3]))
    return list(seen.values())


def _build_targets(include_venues: bool, only: str | None) -> list[dict]:
    targets = _yaml_sources_as_targets()
    if include_venues:
        targets += _venue_targets()
    if only:
        targets = [t for t in targets if t["key"] == only or t["venue_id"] == only]
        if not targets:
            raise SystemExit(f"target {only!r} not found")
    return _dedupe_by_url(targets)


def _source_context(target: dict) -> str:
    parts = [target["name"]]
    if target.get("city"):
        parts.append(target["city"])
    if target.get("dept"):
        parts.append(f"dept {target['dept']}")
    if target.get("category"):
        parts.append(target["category"])
    return ", ".join(parts)


def run(only: str | None = None, skip_llm: bool = False, include_venues: bool = False):
    targets = _build_targets(include_venues, only)
    log.info("crawling %d unique target(s) — include_venues=%s", len(targets), include_venues)

    stats = {"open": 0, "closed": 0, "unknown": 0}
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
                    "is_tremplin": True, "confidence": 0.5, "status": "unknown",
                    "title": title, "summary": None, "deadline": None,
                    "edition_year": None, "location": None, "reasoning": None,
                })()
            else:
                verdict = llm_verify(
                    page["url"], title, text, source_context=_source_context(target)
                )

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
                edition_year=verdict.edition_year,
                location=verdict.location,
                confidence=verdict.confidence,
                status=verdict.status,
                reasoning=verdict.reasoning,
                content_hash=page["content_hash"],
            )
            stats[verdict.status] = stats.get(verdict.status, 0) + 1
            tag = {"open": "✓", "closed": "✗", "unknown": "?"}.get(verdict.status, "·")
            log.info("  %s [%s] %s", tag, verdict.status, verdict.title)

    log.info(
        "done — open=%d closed=%d unknown=%d",
        stats["open"], stats["closed"], stats["unknown"],
    )


def _upsert_tremplin(**row):
    """UPSERT via PostgREST. On omet first_seen et les colonnes None pour
    préserver l'existant. last_seen est rafraîchi à chaque passage."""
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
        help="mode exhaustif : crawl aussi les venues crawlable=true",
    )
    args = p.parse_args()
    run(only=args.only, skip_llm=args.skip_llm, include_venues=args.include_venues)


if __name__ == "__main__":
    main()
