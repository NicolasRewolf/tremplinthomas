"""Client Supabase via PostgREST + service_role key (pas de password Postgres).

PostgREST est l'API HTTP que Supabase expose au-dessus de Postgres. Avec la
`service_role` key, on a un accès complet et on bypasse RLS. Avantage : pas
besoin de chaîne `postgresql://` ni de password — la même credential sert
depuis n'importe où (local, GitHub Actions, edge function).

Usage :
    from .db import select, upsert
    rows = select("venues", crawlable="eq.true", select="id,name,url,dept")
    upsert("tremplins", [{...}, ...], on_conflict="url")
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .config import SUPABASE_SECRET_KEY, SUPABASE_URL

log = logging.getLogger(__name__)


class SupabaseConfigError(RuntimeError):
    pass


def _base() -> str:
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise SupabaseConfigError(
            "SUPABASE_URL et SUPABASE_SECRET_KEY doivent être renseignés dans crawler/.env"
        )
    return SUPABASE_URL.rstrip("/") + "/rest/v1"


def _headers(prefer: str | None = None) -> dict[str, str]:
    h = {
        "apikey": SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def select(table: str, *, select: str = "*", **filters: str) -> list[dict]:
    """SELECT via PostgREST.

    `select` est la liste de colonnes séparée par virgules.
    Les `filters` suivent la syntaxe PostgREST : `column="op.value"`.
        select("venues", select="id,name", crawlable="eq.true", dept="eq.33")
    """
    params: dict[str, str] = {"select": select, **filters}
    with httpx.Client(timeout=30.0) as client:
        r = client.get(f"{_base()}/{table}", params=params, headers=_headers())
        r.raise_for_status()
        return r.json()


def upsert(
    table: str,
    rows: list[dict],
    *,
    on_conflict: str,
    chunk_size: int = 500,
) -> None:
    """UPSERT via PostgREST (Prefer: resolution=merge-duplicates).

    `on_conflict` est la liste de colonnes UNIQUE séparées par virgules, qui
    déclenche le MERGE. Postgres ne sait pas affecter la même ligne deux fois
    dans un même INSERT — l'appelant doit donc déduper en amont.
    """
    if not rows:
        return
    url = f"{_base()}/{table}?on_conflict={on_conflict}"
    headers = _headers("resolution=merge-duplicates,return=minimal")
    with httpx.Client(timeout=60.0) as client:
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            r = client.post(url, content=json.dumps(chunk), headers=headers)
            if r.status_code >= 400:
                log.error("upsert %s failed: %s %s", table, r.status_code, r.text[:300])
                r.raise_for_status()


def patch(table: str, *, body: dict, **filters: str) -> None:
    """PATCH (update) avec filtres PostgREST."""
    with httpx.Client(timeout=30.0) as client:
        r = client.patch(
            f"{_base()}/{table}",
            params=filters,
            content=json.dumps(body),
            headers=_headers("return=minimal"),
        )
        if r.status_code >= 400:
            log.error("patch %s failed: %s %s", table, r.status_code, r.text[:300])
            r.raise_for_status()


def ping() -> dict[str, Any]:
    """Sanity check — utilisé par `python -m tremplins.db`."""
    return {"ok": True, "sources_count": len(select("sources", select="id"))}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(ping())
