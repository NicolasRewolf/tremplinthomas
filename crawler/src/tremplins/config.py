from pathlib import Path
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"

# ─── Anthropic ──────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# ─── Supabase / Postgres ────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")        # https://<ref>.supabase.co
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")  # postgresql://postgres:<pwd>@... (pour psycopg)
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")  # service role, jamais commit


def load_sources() -> list[dict]:
    with open(CONFIG_DIR / "sources.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def load_keywords() -> dict:
    with open(CONFIG_DIR / "keywords.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_discovered_venues() -> list[dict]:
    p = CONFIG_DIR / "sources_discovered.yaml"
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or []
