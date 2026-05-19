-- Migration 005 : la policy de lecture publique sur tremplins est élargie
-- pour exposer aussi 'closed' et 'unknown'. Le filtre par défaut "ouverts
-- uniquement" est désormais côté frontend, ce qui permet à l'utilisateur
-- d'inspecter ce que le LLM a classé comme closed/unknown (audit visuel).

drop policy if exists "public read open tremplins" on public.tremplins;
create policy "public read tremplins" on public.tremplins
  for select using (true);
