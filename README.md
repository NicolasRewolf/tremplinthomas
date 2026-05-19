# Tremplins NA — veille tremplins musicaux Nouvelle-Aquitaine

Monorepo. Frontend basé sur le starter UI/dataviz **REWOLF** (Bordeaux).

```
.
├── src/                  React 19 + Vite + shadcn/ui — le frontend
├── crawler/              Python — crawler + classifier LLM, écrit dans Supabase
├── .github/workflows/    crawl hebdo
└── ...                   config Vite, tsconfig, package.json
```

## Architecture

```
┌─────────────┐   write    ┌──────────────┐   read     ┌──────────────┐
│   crawler   │ ─────────► │   Supabase   │ ─────────► │  React app   │
│  (Python)   │  service   │  (Postgres   │  anon key  │  (Vite/      │
│             │   role     │   + RLS)     │  + RLS     │   shadcn)    │
└─────────────┘            └──────────────┘            └──────────────┘
   crawler/                  4 tables :                 src/
   pipeline.py               sources, venues,           components/
                             pages, tremplins           TremplinsView.tsx
```

- **Crawler Python** : fetch → extract → keyword filter → Claude Haiku → upsert `tremplins`.
- **Supabase** : 4 tables, RLS activée. Lecture publique sur `tremplins WHERE status='open'`.
- **Frontend React** : `@supabase/supabase-js` + publishable key, filtre par département.

## Setup — frontend

```bash
npm install
cp .env.example .env.local   # renseigne VITE_SUPABASE_URL + VITE_SUPABASE_ANON_KEY
npm run dev
```

Déploiement : connecter le repo à Vercel/Netlify/Cloudflare Pages — variables d'env à recopier.

## Setup — crawler

Voir [`crawler/README.md`](crawler/README.md). En résumé :

```bash
cd crawler
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env

python scripts/seed_sources.py        # YAML → table sources
python scripts/seed_venues.py         # YAML Wikipédia → table venues (70 salles NA)
python -m tremplins.pipeline          # un cycle complet
```

## Migration de schéma Supabase

Source unique : [`crawler/db/migration.sql`](crawler/db/migration.sql) (déjà appliquée).
Pour la rejouer : SQL Editor de Supabase, ou Management API via PAT, ou MCP.

## Sécurité

- **Frontend** : seulement `VITE_SUPABASE_ANON_KEY` (publishable). RLS contrôle l'accès.
- **Crawler** : `SUPABASE_DB_URL` (Postgres) — bypass RLS via le rôle `postgres`.
- **Jamais** committer `.env` ou `.env.local` ; le `.gitignore` les couvre.

---

*UI bricks : REWOLF Studio — Bordeaux*
