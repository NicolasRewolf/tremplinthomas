"""Insère/met-à-jour les salles décrites dans config/sources_discovered.yaml
dans la table public.venues (via PostgREST).

Idempotent. Pour la base massive ACNA (12 .ods, ~4800 structures), utilise
plutôt `scripts/ingest_acna.py`.
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.config import load_discovered_venues  # noqa: E402
from tremplins.db import upsert  # noqa: E402

log = logging.getLogger(__name__)


def parse_capacity(raw: str | None) -> int | None:
    if not raw:
        return None
    m = re.search(r"([\d\s ]+)\s*places", raw, re.IGNORECASE)
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(1))
    return int(digits) if digits else None


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    venues = load_discovered_venues()
    if not venues:
        log.warning("aucune salle dans config/sources_discovered.yaml")
        return

    rows = []
    for v in venues:
        rows.append({
            "name": v["name"],
            "city": v["city"],
            "dept": v.get("dept"),
            "capacity_raw": v.get("capacity"),
            "capacity_int": parse_capacity(v.get("capacity")),
            "url": v.get("url"),
            "notes": v.get("notes"),
            "origin": "wikipedia",
            "category": "wikipedia",  # catégorie technique pour différencier de l'origin ACNA
            "crawlable": bool(v.get("url")),
        })
    upsert("venues", rows, on_conflict="name,city,category")
    log.info("✅ %d salles synchronisées dans public.venues", len(rows))


if __name__ == "__main__":
    main()
