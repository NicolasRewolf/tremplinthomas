"""Ingère tous les exports .ods de l'Agence Culturelle Nouvelle-Aquitaine
dans la table public.venues (via PostgREST).

Idempotent — upsert sur (name, city, category). Dédupe intra-batch obligatoire
car Postgres refuse d'affecter deux fois la même ligne dans une seule commande.
"""
from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.db import upsert  # noqa: E402
from tremplins.ods import read_ods  # noqa: E402

log = logging.getLogger(__name__)

INPUT_DIR = Path(__file__).resolve().parents[1] / "input"
SUFFIX = "-Agence-Culturelle-Nouvelle-Aquitaine-04-2026.ods"

DEPT_NAME_TO_CODE = {
    "CHARENTE": "16", "CHARENTE-MARITIME": "17",
    "CORREZE": "19", "CORRÈZE": "19",
    "CREUSE": "23", "DORDOGNE": "24", "GIRONDE": "33", "LANDES": "40",
    "LOT-ET-GARONNE": "47",
    "PYRENEES-ATLANTIQUES": "64", "PYRÉNÉES-ATLANTIQUES": "64",
    "DEUX-SEVRES": "79", "DEUX-SÈVRES": "79",
    "VIENNE": "86", "HAUTE-VIENNE": "87",
}

HEADER_ALIASES = {
    "name": ["Nom de l'activité", "Nom de l’activité"],
    "city": ["Commune de l'activité", "Commune de l’activité"],
    "postal_code": ["Code postal de l'activité", "Code postal de l’activité"],
    "epci": ["EPCI de l'activité", "EPCI de l’activité"],
    "dept_name": ["Département de l'activité", "Département de l’activité"],
    "discipline": ["Discipline principale de l'activité", "Discipline principale de l’activité"],
    "email": ["Email de l'activité", "Email de l’activité"],
    "url": ["Site web de l'activité", "Site web de l’activité"],
}


def pick(row: dict, key: str) -> str | None:
    for alias in HEADER_ALIASES.get(key, []):
        if alias in row and row[alias]:
            return row[alias].strip() or None
    return None


def clean_url(raw: str | None) -> str | None:
    if not raw:
        return None
    u = raw.strip()
    if not u:
        return None
    if not re.match(r"^https?://", u, re.IGNORECASE):
        if "." in u and " " not in u:
            u = "https://" + u
        else:
            return None
    return u


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    files = sorted(INPUT_DIR.glob(f"*{SUFFIX}"))
    if not files:
        log.error("aucun .ods trouvé dans %s", INPUT_DIR)
        sys.exit(1)

    total = 0
    for path in files:
        category = path.name.removesuffix(SUFFIX).lower()
        # Dédupe intra-fichier sur (name, city, category)
        seen: dict[tuple, dict] = {}
        for row in read_ods(path):
            name = pick(row, "name")
            city = pick(row, "city")
            if not name or not city:
                continue
            key = (name, city, category)
            if key in seen:
                continue
            url = clean_url(pick(row, "url"))
            seen[key] = {
                "name": name,
                "city": city,
                "dept": DEPT_NAME_TO_CODE.get((pick(row, "dept_name") or "").upper()),
                "postal_code": pick(row, "postal_code"),
                "epci": pick(row, "epci"),
                "discipline": pick(row, "discipline"),
                "email": pick(row, "email"),
                "url": url,
                "category": category,
                "crawlable": bool(url),
                "origin": "acna",
            }
        rows = list(seen.values())
        upsert("venues", rows, on_conflict="name,city,category")
        log.info("  %5d ← %s", len(rows), category)
        total += len(rows)

    log.info("✅ %d structures ingérées dans public.venues", total)


if __name__ == "__main__":
    main()
