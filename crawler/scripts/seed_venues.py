"""Insère/met-à-jour les salles décrites dans config/sources_discovered.yaml
dans la table public.venues de Supabase.

Idempotent : upsert sur (name, city). Re-run sans danger après édition du YAML.
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

# Permet d'exécuter le script via `python scripts/seed_venues.py` depuis crawler/
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.config import load_discovered_venues  # noqa: E402
from tremplins.db import connect  # noqa: E402

log = logging.getLogger(__name__)


def parse_capacity(raw: str | None) -> int | None:
    if not raw:
        return None
    # Première séquence chiffres+espaces avant "places"
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

    inserted = 0
    with connect() as conn, conn.cursor() as cur:
        for v in venues:
            cap_int = parse_capacity(v.get("capacity"))
            cur.execute(
                """
                insert into public.venues
                  (name, city, dept, capacity_raw, capacity_int, url, notes, origin)
                values
                  (%(name)s, %(city)s, %(dept)s, %(capacity_raw)s, %(capacity_int)s,
                   %(url)s, %(notes)s, 'wikipedia')
                on conflict (name, city) do update set
                  dept         = excluded.dept,
                  capacity_raw = excluded.capacity_raw,
                  capacity_int = excluded.capacity_int,
                  url          = coalesce(excluded.url, public.venues.url),
                  notes        = excluded.notes
                """,
                {
                    "name": v["name"],
                    "city": v["city"],
                    "dept": v.get("dept"),
                    "capacity_raw": v.get("capacity"),
                    "capacity_int": cap_int,
                    "url": v.get("url"),
                    "notes": v.get("notes"),
                },
            )
            inserted += 1
    log.info("✅ %d salles synchronisées dans public.venues", inserted)


if __name__ == "__main__":
    main()
