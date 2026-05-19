"""Synchronise config/sources.yaml → public.sources (via PostgREST).

Le YAML reste la source de vérité (versionnée dans git). Cette table est un
miroir lisible côté Postgres pour requêtes/jointures (ex. tremplins join
sources pour afficher le nom de la structure côté frontend).

Sources retirées du YAML → active=false (préserve l'historique des tremplins).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.config import load_sources  # noqa: E402
from tremplins.db import patch, select, upsert  # noqa: E402

log = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sources = load_sources()
    yaml_ids = {s["id"] for s in sources}

    rows = [
        {
            "id": s["id"],
            "name": s["name"],
            "url": s["url"],
            "dept": s.get("dept"),
            "type": s["type"],
            "paths": s.get("paths") or [],
            "active": True,
        }
        for s in sources
    ]
    upsert("sources", rows, on_conflict="id")

    # Sources retirées du YAML → désactivées
    db_rows = select("sources", select="id", active="eq.true")
    db_ids = {r["id"] for r in db_rows}
    deactivate = db_ids - yaml_ids
    if deactivate:
        patch("sources", body={"active": False}, id=f"in.({','.join(deactivate)})")
        log.info("désactivées (absentes du YAML) : %s", ", ".join(sorted(deactivate)))

    log.info("✅ %d sources synchronisées", len(sources))


if __name__ == "__main__":
    main()
