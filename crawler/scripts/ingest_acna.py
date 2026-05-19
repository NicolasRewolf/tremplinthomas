"""Ingère tous les exports .ods de l'Agence Culturelle Nouvelle-Aquitaine
dans la table public.venues.

Pour chaque ligne :
  - extraction des champs standardisés (name, city, dept, url, email, ...)
  - mapping du nom de département FR (GIRONDE) → code INSEE (33)
  - flag crawlable=true si une URL est présente — l'idée : ne rien rater,
    le keyword prefilter + LLM gèrent les faux positifs au crawl.

Idempotent — upsert sur (name, city, category).
"""
from __future__ import annotations

import logging
import re
import sys
import unicodedata
from pathlib import Path

# Permet d'exécuter depuis crawler/ via `python scripts/ingest_acna.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.db import connect  # noqa: E402
from tremplins.ods import read_ods  # noqa: E402

log = logging.getLogger(__name__)

INPUT_DIR = Path(__file__).resolve().parents[1] / "input"

# Nom du département FR → code INSEE
DEPT_NAME_TO_CODE = {
    "CHARENTE": "16",
    "CHARENTE-MARITIME": "17",
    "CORREZE": "19",
    "CORRÈZE": "19",
    "CREUSE": "23",
    "DORDOGNE": "24",
    "GIRONDE": "33",
    "LANDES": "40",
    "LOT-ET-GARONNE": "47",
    "PYRENEES-ATLANTIQUES": "64",
    "PYRÉNÉES-ATLANTIQUES": "64",
    "DEUX-SEVRES": "79",
    "DEUX-SÈVRES": "79",
    "VIENNE": "86",
    "HAUTE-VIENNE": "87",
}

# Suffixe commun des fichiers — sert à dériver la catégorie
SUFFIX = "-Agence-Culturelle-Nouvelle-Aquitaine-04-2026.ods"


def category_from_filename(path: Path) -> str:
    return path.name.removesuffix(SUFFIX).lower()


def normalize_dept(raw: str | None) -> str | None:
    if not raw:
        return None
    key = raw.strip().upper()
    return DEPT_NAME_TO_CODE.get(key)


def clean_url(raw: str | None) -> str | None:
    if not raw:
        return None
    url = raw.strip()
    if not url:
        return None
    # Quelques URLs sont "facebook.com/xxx" sans protocole
    if not re.match(r"^https?://", url, re.IGNORECASE):
        if "." in url and " " not in url:
            url = "https://" + url
        else:
            return None
    return url


# Colonnes standards observées (cf. inspection .ods Lieu-de-diffusion)
HEADER_ALIASES = {
    "name": ["Nom de l'activité", "Nom de l’activité"],
    "address": ["Adresse de l'activité", "Adresse de l’activité"],
    "city": ["Commune de l'activité", "Commune de l’activité"],
    "postal_code": ["Code postal de l'activité", "Code postal de l’activité"],
    "epci": ["EPCI de l'activité", "EPCI de l’activité"],
    "dept_name": ["Département de l'activité", "Département de l’activité"],
    "discipline": ["Discipline principale de l'activité", "Discipline principale de l’activité"],
    "email": ["Email de l'activité", "Email de l’activité"],
    "url": ["Site web de l'activité", "Site web de l’activité"],
}


def pick(row: dict[str, str], key: str) -> str | None:
    for alias in HEADER_ALIASES.get(key, []):
        if alias in row and row[alias]:
            return row[alias].strip() or None
    return None


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    files = sorted(INPUT_DIR.glob(f"*{SUFFIX}"))
    if not files:
        log.error("aucun .ods trouvé dans %s", INPUT_DIR)
        sys.exit(1)

    total_inserted = 0
    with connect() as conn, conn.cursor() as cur:
        for path in files:
            category = category_from_filename(path)
            log.info("→ %s", path.name)
            n = 0
            for row in read_ods(path):
                name = pick(row, "name")
                city = pick(row, "city")
                if not name or not city:
                    continue
                url = clean_url(pick(row, "url"))
                cur.execute(
                    """
                    insert into public.venues
                      (name, city, dept, postal_code, epci, discipline, email,
                       url, category, crawlable, origin)
                    values
                      (%(name)s, %(city)s, %(dept)s, %(postal_code)s, %(epci)s,
                       %(discipline)s, %(email)s, %(url)s, %(category)s,
                       %(crawlable)s, 'acna')
                    on conflict (name, city, category) do update set
                      dept        = coalesce(excluded.dept, public.venues.dept),
                      postal_code = coalesce(excluded.postal_code, public.venues.postal_code),
                      epci        = coalesce(excluded.epci, public.venues.epci),
                      discipline  = coalesce(excluded.discipline, public.venues.discipline),
                      email       = coalesce(excluded.email, public.venues.email),
                      url         = coalesce(excluded.url, public.venues.url),
                      crawlable   = excluded.crawlable or public.venues.crawlable
                    """,
                    {
                        "name": name,
                        "city": city,
                        "dept": normalize_dept(pick(row, "dept_name")),
                        "postal_code": pick(row, "postal_code"),
                        "epci": pick(row, "epci"),
                        "discipline": pick(row, "discipline"),
                        "email": pick(row, "email"),
                        "url": url,
                        "category": category,
                        # crawlable = true dès qu'on a une URL.
                        # L'idée : ne rien rater. Le filtre se fait au crawl.
                        "crawlable": bool(url),
                    },
                )
                n += 1
            log.info("   %d lignes traitées", n)
            total_inserted += n

    log.info("✅ %d structures synchronisées dans public.venues", total_inserted)


if __name__ == "__main__":
    main()
