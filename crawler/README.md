# Crawler — Tremplins NA

Python ETL : `fetch → extract → keyword filter → Claude Haiku → upsert tremplins` dans Supabase Postgres.

## Pourquoi la découverte des sources est dure — et comment on s'y prend

Le vrai problème n'est pas le scraping, c'est la **découverte exhaustive des sources**. Personne ne maintient une liste consolidée des structures qui peuvent proposer un tremplin musical en Nouvelle-Aquitaine. Stratégie en trois couches :

1. **Sources consolidatrices** — Le RIM (Réseau des Indépendants de la Musique en NA), FEDELIMA, Région, DRAC. Ces hubs relaient déjà les tremplins des structures plus petites.
2. **SMAC + grandes scènes** (~30 lieux) — seedées à la main dans `config/sources.yaml`.
3. **Découverte continue** — `python -m tremplins.discovery` extrait les domaines tiers cités par les sources connues. À filtrer manuellement.

Plus une base de **70 salles** de Nouvelle-Aquitaine extraites de Wikipédia dans la table `venues` (via `scripts/seed_venues.py`).

## Setup

```bash
cd crawler
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env       # renseigne ANTHROPIC_API_KEY et SUPABASE_DB_URL
```

Récupère `SUPABASE_DB_URL` dans Supabase Dashboard → Project Settings → Database → *Connection string* (préfère le Transaction pooler, port 6543).

## Commandes

| Commande | Rôle |
|---|---|
| `python -m tremplins.db` | sanity check connexion Postgres |
| `python scripts/seed_sources.py` | sync `config/sources.yaml` → table `sources` |
| `python scripts/seed_venues.py` | sync `config/sources_discovered.yaml` (Wikipédia) → `venues` |
| `python scripts/ingest_acna.py` | **ingère les 12 .ods de l'Agence Culturelle NA → `venues`** (~4800 structures) |
| `python -m tremplins.pipeline` | crawl des sources curées (sources.yaml) |
| `python -m tremplins.pipeline --include-venues` | **mode exhaustif : crawl aussi les venues crawlables (~4100 URLs)** |
| `python -m tremplins.pipeline --only le-rim` | crawl d'une seule source |
| `python -m tremplins.pipeline --skip-llm` | dev — bypass de la vérification LLM |
| `python -m tremplins.discovery` | propose des sources candidates |
| `python scripts/parse_wiki_na.py` | régénère `sources_discovered.yaml` depuis le dump Wikipédia |

## Couverture des sources (objectif : ne rien rater)

Trois strates qui se complètent :

1. **Sources curées** (`config/sources.yaml`, ~15 entrées) — Le RIM, SMAC, institutions. Crawlées à chaque run.
2. **Catalogue Agence Culturelle NA** (table `venues`, ~4800 structures, ~4100 avec URL) — exhaustif. Ingéré une fois par an depuis les exports .ods officiels.
3. **Découverte continue** (`discovery.py`) — propose des candidats hors catalogue.

Le flag `--include-venues` du pipeline parcourt aussi (2). Compte budget LLM ~€1-2 par run complet sur l'ensemble du catalogue.

## Édition des sources

Tout est dans [`config/sources.yaml`](config/sources.yaml). Champs :
```yaml
- id: rock-school-barbey
  name: Rock School Barbey
  url: https://www.rockschool-barbey.com/
  dept: "33"                         # code département ou "NA" si régional
  type: smac                          # network | institution | smac | venue | platform | media
  paths: ["/agenda/"]                 # optionnel — pages additionnelles à crawler
```

Le YAML est la source de vérité. `seed_sources.py` synchronise vers Postgres.

## Appliquer le schéma à Supabase

Une seule fois par environnement. Trois méthodes (équivalentes) :

1. **SQL Editor** : copier-coller [`db/migration.sql`](db/migration.sql) dans Supabase Dashboard → SQL Editor → Run.
2. **Management API + PAT** :
   ```bash
   PAT='sbp_...'  REF='uxmblaaadtwoggbknpze'
   curl -X POST "https://api.supabase.com/v1/projects/$REF/database/query" \
     -H "Authorization: Bearer $PAT" \
     -H "Content-Type: application/json" \
     -H "User-Agent: Mozilla/5.0" \
     --data-binary @<(jq -Rs '{query: .}' db/migration.sql)
   ```
3. **MCP Supabase** : `apply_migration` une fois le MCP relié au bon compte.

La migration est idempotente.

## Limites

- Facebook / Instagram non scrapés (anti-bot, ToS). Beaucoup de petites structures n'ont que ça — trou assumé.
- HelloAsso pas d'API publique stable ; on cible des pages connues.
- LLM ~0,001 € par page vérifiée avec Haiku, négligeable à cette échelle.
