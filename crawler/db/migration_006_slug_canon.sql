-- Migration 006 : slug_canon pour la fusion canonique des venues.
-- Une même structure peut apparaître dans 4 sources (ACNA, Wikipedia,
-- culture-gouv, panorama-festivals) avec des category différentes ; on
-- veut une clé de regroupement stable pour les afficher en un seul item
-- côté frontend.
--
-- slug_canon = normalize(name) + "::" + normalize(city)
-- (normalize = lower, strip accents, replace non-alphanum par '-')
--
-- Idempotente.

create extension if not exists unaccent;

-- Fonction de normalisation : retire accents, lowercase, ne garde que [a-z0-9]
create or replace function public.normalize_slug(s text)
returns text language sql immutable as $$
  select trim(both '-' from
           regexp_replace(
             lower(unaccent(coalesce(s, ''))),
             '[^a-z0-9]+', '-', 'g'
           )
         );
$$;

-- Colonne calculée (materialized) maintenue par trigger pour rester indexable
-- et rapide à grouper côté frontend.
alter table public.venues
  add column if not exists slug_canon text;

-- Backfill + trigger
update public.venues
   set slug_canon = public.normalize_slug(name) || '::' || public.normalize_slug(city)
 where slug_canon is null;

create or replace function public.venues_set_slug_canon()
returns trigger language plpgsql as $$
begin
  new.slug_canon := public.normalize_slug(new.name) || '::' || public.normalize_slug(new.city);
  return new;
end;
$$;

drop trigger if exists trg_venues_slug_canon on public.venues;
create trigger trg_venues_slug_canon
  before insert or update of name, city on public.venues
  for each row execute function public.venues_set_slug_canon();

create index if not exists idx_venues_slug_canon on public.venues(slug_canon);
