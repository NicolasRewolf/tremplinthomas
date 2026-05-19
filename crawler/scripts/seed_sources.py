"""Synchronise config/sources.yaml → public.sources dans Supabase.

Le YAML reste la source de vérité (versionnée dans git). Cette table est un
miroir lisible côté Postgres pour requêtes/jointures (ex. join tremplins
→ sources pour afficher le nom de la structure côté frontend).

Idempotent : upsert sur l'id. Sources supprimées du YAML → marquées active=false
plutôt que delete (préserve l'historique des tremplins).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tremplins.config import load_sources  # noqa: E402
from tremplins.db import connect  # noqa: E402

log = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    sources = load_sources()
    yaml_ids = {s["id"] for s in sources}

    with connect() as conn, conn.cursor() as cur:
        for s in sources:
            cur.execute(
                """
                insert into public.sources (id, name, url, dept, type, paths, active)
                values (%(id)s, %(name)s, %(url)s, %(dept)s, %(type)s, %(paths)s, true)
                on conflict (id) do update set
                  name   = excluded.name,
                  url    = excluded.url,
                  dept   = excluded.dept,
                  type   = excluded.type,
                  paths  = excluded.paths,
                  active = true
                """,
                {
                    "id": s["id"],
                    "name": s["name"],
                    "url": s["url"],
                    "dept": s.get("dept"),
                    "type": s["type"],
                    "paths": s.get("paths") or [],
                },
            )

        # Sources retirées du YAML → désactivées (pas delete pour préserver FK)
        cur.execute("select id from public.sources where active = true")
        db_ids = {r["id"] for r in cur.fetchall()}
        deactivate = db_ids - yaml_ids
        if deactivate:
            cur.execute(
                "update public.sources set active = false where id = any(%s)",
                (list(deactivate),),
            )
            log.info("désactivées (absentes du YAML) : %s", ", ".join(sorted(deactivate)))

    log.info("✅ %d sources synchronisées dans public.sources", len(sources))


if __name__ == "__main__":
    main()
