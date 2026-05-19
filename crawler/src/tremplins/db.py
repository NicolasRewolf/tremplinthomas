"""Connexion Postgres (Supabase) via psycopg.

Connexion via SUPABASE_DB_URL (chaîne `postgresql://...`). Pour Supabase :
- en local / GitHub Actions : utilise la chaîne *direct connection* (port 5432)
  ou *transaction pooler* (port 6543, recommandé pour les jobs courts).
- côté code : connexion ouverte par appel, fermée à la sortie du contexte.

Le schéma n'est PAS créé ici — il vit dans db/migration.sql, appliqué une
seule fois via le SQL Editor ou supabase CLI. Code et schéma sont découplés.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from .config import SUPABASE_DB_URL


class MissingDatabaseURL(RuntimeError):
    pass


def _dsn() -> str:
    if not SUPABASE_DB_URL:
        raise MissingDatabaseURL(
            "SUPABASE_DB_URL absent du .env — copie .env.example vers .env "
            "et renseigne la chaîne de connexion (Dashboard → Project Settings "
            "→ Database → Connection string)."
        )
    return SUPABASE_DB_URL


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    """Connexion Postgres avec rows en dict, commit auto à la sortie sans erreur."""
    conn = psycopg.connect(_dsn(), row_factory=dict_row, autocommit=False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ping() -> str:
    """Sanity check — utilisé par `python -m tremplins.db`."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("select version();")
            row = cur.fetchone()
            return row["version"] if row else "unknown"


if __name__ == "__main__":
    print(ping())
