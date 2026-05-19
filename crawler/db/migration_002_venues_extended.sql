-- Migration 002 : étend venues pour absorber le catalogue Agence Culturelle NA.
-- Idempotente.

alter table public.venues
  add column if not exists category     text,
  add column if not exists crawlable    boolean not null default false,
  add column if not exists email        text,
  add column if not exists postal_code  text,
  add column if not exists discipline   text,
  add column if not exists epci         text;

-- Index sur category (filtres frontend, jointures)
create index if not exists idx_venues_category on public.venues(category);
create index if not exists idx_venues_crawlable on public.venues(crawlable) where crawlable = true;

-- Mise à jour de la contrainte origin pour autoriser 'acna' (Agence Culturelle NA)
-- Postgres ne permet pas d'ajouter une valeur à un CHECK existant sans le reconstruire.
do $$
begin
  alter table public.venues drop constraint if exists venues_origin_check;
  alter table public.venues add constraint venues_origin_check
    check (origin in ('wikipedia','manual','discovery','acna','other'));
end $$;

-- Unicité élargie : une même structure (nom + ville) peut apparaître dans
-- plusieurs catégories (ex. "Le Krakatoa" comme lieu ET comme producteur).
-- On garde donc (name, city, category) plutôt que (name, city).
alter table public.venues drop constraint if exists venues_name_city_key;
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'venues_name_city_category_unique'
  ) then
    alter table public.venues
      add constraint venues_name_city_category_unique unique (name, city, category);
  end if;
end $$;
