"""Scan OpenAgenda à grande échelle.

Pour chaque venue NA (priorité aux SMAC/festivals), on essaye de trouver son
agenda OpenAgenda via search par nom, puis on récupère les events qui
contiennent 'tremplin' / 'appel' / 'concours' / 'candidature' / 'scène ouverte'.

Chaque event devient un candidat tremplin qu'on classifie ensuite avec Sonnet.
"""
from __future__ import annotations

import logging
import os
import sys
import time
import unicodedata
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.classifier import llm_verify  # noqa: E402
from tremplins.db import select, upsert  # noqa: E402

log = logging.getLogger(__name__)
OPENAGENDA_KEY = os.getenv("OPENAGENDA_KEY")
BASE = "https://api.openagenda.com/v2"
KEYWORDS = ["tremplin", "candidature", "appel à candidatures", "concours", "sélection"]

DEPT_LABELS = {
    "16": "Charente", "17": "Charente-Maritime", "19": "Corrèze", "23": "Creuse",
    "24": "Dordogne", "33": "Gironde", "40": "Landes", "47": "Lot-et-Garonne",
    "64": "Pyrénées-Atlantiques", "79": "Deux-Sèvres", "86": "Vienne", "87": "Haute-Vienne",
}


def _slugify(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return "".join(c if c.isalnum() else "-" for c in s).strip("-")


def find_agenda_for_venue(client: httpx.Client, name: str, city: str) -> int | None:
    """Cherche l'agenda OpenAgenda d'une venue. Heuristique : le slug
    contient le slug normalisé du nom de la venue."""
    target_slug = _slugify(name)
    if len(target_slug) < 4:  # noms trop courts → faux positifs
        return None
    r = client.get(
        f"{BASE}/agendas",
        params={"key": OPENAGENDA_KEY, "search": name, "size": 10},
        timeout=20.0,
    )
    if r.status_code != 200:
        return None
    for ag in r.json().get("agendas", []):
        slug = ag.get("slug", "")
        # Match si slug exact ou contient le slug cible
        if target_slug == slug or target_slug in slug or slug in target_slug:
            return ag["uid"]
    return None


def fetch_events(client: httpx.Client, agenda_uid: int, keyword: str) -> list[dict]:
    """Events upcoming + récents (1 an en arrière) pour un keyword donné."""
    out = []
    after = None
    for _ in range(5):  # pagination max 5 pages × 20 = 100 events
        params = {
            "key": OPENAGENDA_KEY,
            "search": keyword,
            "size": 20,
        }
        if after:
            params["after"] = ",".join(map(str, after))
        r = client.get(f"{BASE}/agendas/{agenda_uid}/events", params=params, timeout=20.0)
        if r.status_code != 200:
            break
        data = r.json()
        events = data.get("events", [])
        out.extend(events)
        if len(events) < 20:
            break
        after = data.get("after")
        if not after:
            break
        time.sleep(0.3)
    return out


def main(limit_venues: int | None = None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    if not OPENAGENDA_KEY:
        log.error("OPENAGENDA_KEY manquant dans .env")
        sys.exit(1)

    # On cible : SMACs et autres venues crawlables avec category prometteuse
    rows = select(
        "venues",
        select="id,name,city,dept,category",
        crawlable="eq.true",
        category="in.(lieu-de-diffusion,festival,festival-min-culture,reseau-agence,culture-gouv-arts-spectacle)",
    )
    if limit_venues:
        rows = rows[:limit_venues]

    log.info("scanning %d venues against OpenAgenda", len(rows))
    found_agendas = 0
    candidate_events: list[dict] = []
    seen_venues: set[str] = set()

    with httpx.Client(headers={"User-Agent": "tremplinthomas/0.1"}) as client:
        for v in rows:
            # Évite de re-chercher si même slug que déjà vu
            slug_key = _slugify(v["name"])
            if slug_key in seen_venues:
                continue
            seen_venues.add(slug_key)

            try:
                agenda_uid = find_agenda_for_venue(client, v["name"], v["city"])
            except Exception as e:
                log.warning("  agenda lookup failed for %s: %s", v["name"], e)
                continue
            time.sleep(0.2)  # respect rate limit
            if not agenda_uid:
                continue
            found_agendas += 1
            log.info("→ %s (%s) — agenda %d", v["name"], v["city"], agenda_uid)

            # Fetch events for each keyword
            agenda_events: dict[str, dict] = {}  # uid → event
            for kw in KEYWORDS:
                events = fetch_events(client, agenda_uid, kw)
                for e in events:
                    agenda_events[e["uid"]] = e
                time.sleep(0.2)

            for e in agenda_events.values():
                e["_venue"] = v
                candidate_events.append(e)
            log.info("   %d events potentiels", len(agenda_events))

    log.info("\n=== Bilan scan ===")
    log.info("Agendas trouvés : %d / %d venues testées", found_agendas, len(rows))
    log.info("Events candidats : %d", len(candidate_events))

    # Classification + upsert tremplins
    classified = 0
    kept = {"open": 0, "closed": 0, "unknown": 0}
    for e in candidate_events:
        title = e.get("title", {})
        if isinstance(title, dict):
            title = title.get("fr") or title.get("en") or ""
        desc = e.get("description", {})
        if isinstance(desc, dict):
            desc = desc.get("fr") or desc.get("en") or ""
        long_desc = e.get("longDescription", {})
        if isinstance(long_desc, dict):
            long_desc = long_desc.get("fr") or long_desc.get("en") or ""

        # URL : permalink OpenAgenda ou origineUrl si disponible
        slug = e.get("slug", "")
        agenda_slug = e.get("agenda", {}).get("slug", "")
        url = (
            e.get("originAgenda", {}).get("url")
            or (f"https://openagenda.com/{agenda_slug}/events/{slug}" if agenda_slug and slug else None)
            or f"https://openagenda.com/events/{e['uid']}"
        )

        text_for_llm = f"{title}\n\n{desc}\n\n{long_desc}".strip()
        if len(text_for_llm) < 50:
            continue

        venue = e["_venue"]
        context = f"{venue['name']}, {venue['city']}, dept {venue.get('dept')}, source: OpenAgenda"
        try:
            verdict = llm_verify(url, title, text_for_llm, source_context=context)
        except Exception as exc:
            log.warning("LLM failed for %s: %s", url, exc)
            continue
        classified += 1
        if not verdict.is_tremplin or verdict.confidence < 0.5:
            continue
        body = {
            "url": url, "venue_id": venue["id"], "dept": venue.get("dept"),
            "title": verdict.title or title, "summary": verdict.summary,
            "deadline": verdict.deadline, "edition_year": verdict.edition_year,
            "location": verdict.location, "confidence": verdict.confidence,
            "status": verdict.status, "reasoning": verdict.reasoning,
        }
        body = {k: val for k, val in body.items() if val is not None}
        from datetime import datetime, timezone
        body["last_seen"] = datetime.now(timezone.utc).isoformat()
        upsert("tremplins", [body], on_conflict="url")
        kept[verdict.status] = kept.get(verdict.status, 0) + 1
        tag = {"open": "✓", "closed": "✗", "unknown": "?"}.get(verdict.status, "·")
        log.info("  %s [%s] %s", tag, verdict.status, verdict.title or title)

    log.info("\nClassifiés : %d | open=%d closed=%d unknown=%d",
             classified, kept["open"], kept["closed"], kept["unknown"])


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, help="limite le nombre de venues (debug)")
    args = p.parse_args()
    main(limit_venues=args.limit)
