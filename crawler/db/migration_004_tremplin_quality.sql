-- Migration 004 : enrichissement tremplins (status="unknown", edition_year, reasoning)
-- + dedupe friendly. Idempotente.

-- Permet 'unknown' dans status (en plus de open/closed/draft)
do $$
begin
  alter table public.tremplins drop constraint if exists tremplins_status_check;
  alter table public.tremplins add constraint tremplins_status_check
    check (status in ('open','closed','draft','unknown'));
end $$;

alter table public.tremplins
  add column if not exists edition_year integer,
  add column if not exists reasoning    text;

-- La policy publique ne montrait que status='open' — on garde, donc 'unknown'
-- et 'closed' ne s'affichent pas côté frontend par défaut (ce qui est ce
-- qu'on veut : le doute n'est pas affiché à Thomas).
