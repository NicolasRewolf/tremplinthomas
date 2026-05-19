-- Migration 003 : un tremplin peut provenir soit d'une source curée (sources.yaml),
-- soit d'une venue crawlable (catalogue ACNA). On découple via deux FK optionnelles.

alter table public.tremplins
  add column if not exists venue_id uuid references public.venues(id) on delete set null;

-- source_id devient nullable (un tremplin issu d'une venue n'a pas de source curée)
alter table public.tremplins alter column source_id drop not null;

-- Contrainte : au moins l'un des deux est renseigné
do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'tremplins_origin_check'
  ) then
    alter table public.tremplins
      add constraint tremplins_origin_check
      check (source_id is not null or venue_id is not null);
  end if;
end $$;

create index if not exists idx_tremplins_venue_id on public.tremplins(venue_id);

-- Idem côté pages : permet de tracer le crawl d'une venue
alter table public.pages
  add column if not exists venue_id uuid references public.venues(id) on delete cascade;

alter table public.pages alter column source_id drop not null;

do $$
begin
  if not exists (
    select 1 from pg_constraint where conname = 'pages_origin_check'
  ) then
    alter table public.pages
      add constraint pages_origin_check
      check (source_id is not null or venue_id is not null);
  end if;
end $$;
