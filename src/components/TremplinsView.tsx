import { useMemo, useState } from "react"
import { useTremplins } from "@/hooks/useTremplins"
import { DEPT_LABELS } from "@/types/tremplin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CalendarClock, MapPin, ExternalLink, Loader2 } from "lucide-react"

export function TremplinsView() {
  const state = useTremplins()
  const [dept, setDept] = useState<string>("all")

  const tremplins = state.status === "ready" ? state.data : []
  const departments = useMemo(() => {
    const present = new Set<string>()
    for (const t of tremplins) present.add(t.dept ?? "NA")
    return Array.from(present).sort()
  }, [tremplins])

  const filtered = useMemo(
    () => (dept === "all" ? tremplins : tremplins.filter((t) => (t.dept ?? "NA") === dept)),
    [tremplins, dept]
  )

  return (
    <div className="mx-auto w-full max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-baseline justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Tremplins musicaux</h1>
          <p className="text-sm text-muted-foreground">Nouvelle-Aquitaine — veille automatique</p>
        </div>
        <div className="text-right text-sm text-muted-foreground">
          {state.status === "loading" && (
            <span className="inline-flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              chargement…
            </span>
          )}
          {state.status === "ready" && <span>{tremplins.length} ouvert(s)</span>}
        </div>
      </header>

      {state.status === "error" && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Erreur de chargement</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            {state.error}
            <br />
            <span className="text-muted-foreground">
              Vérifie <code>.env.local</code> (VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY) et les
              policies RLS sur la table <code>tremplins</code>.
            </span>
          </CardContent>
        </Card>
      )}

      {state.status === "ready" && tremplins.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center text-muted-foreground">
            Aucun tremplin détecté pour l'instant.
            <br />
            Lance le crawler : <code>cd crawler && python -m tremplins.pipeline</code>
          </CardContent>
        </Card>
      )}

      {state.status === "ready" && tremplins.length > 0 && (
        <>
          <div className="mb-6 flex flex-wrap gap-2">
            <FilterChip active={dept === "all"} onClick={() => setDept("all")}>
              Tous ({tremplins.length})
            </FilterChip>
            {departments.map((code) => {
              const count = tremplins.filter((t) => (t.dept ?? "NA") === code).length
              return (
                <FilterChip key={code} active={dept === code} onClick={() => setDept(code)}>
                  {DEPT_LABELS[code] ?? code} <span className="opacity-60">({count})</span>
                </FilterChip>
              )
            })}
          </div>

          <ul className="space-y-3">
            {filtered.map((t) => (
              <li key={t.id}>
                <Card className="transition-colors hover:border-foreground/30">
                  <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0 pb-3">
                    <div className="min-w-0">
                      <CardTitle className="text-base leading-snug">
                        <a
                          href={t.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:underline"
                        >
                          {t.title}
                        </a>
                      </CardTitle>
                      {t.summary && (
                        <p className="mt-1 text-sm text-muted-foreground">{t.summary}</p>
                      )}
                    </div>
                    <Button asChild variant="ghost" size="icon" className="shrink-0">
                      <a href={t.url} target="_blank" rel="noopener noreferrer" aria-label="Ouvrir">
                        <ExternalLink />
                      </a>
                    </Button>
                  </CardHeader>
                  <CardContent className="flex flex-wrap items-center gap-2 pt-0 text-xs">
                    <Badge variant="secondary" className="gap-1">
                      <MapPin className="h-3 w-3" />
                      {DEPT_LABELS[t.dept ?? "NA"] ?? t.dept}
                    </Badge>
                    {t.deadline && (
                      <Badge className="gap-1">
                        <CalendarClock className="h-3 w-3" />
                        {t.deadline}
                      </Badge>
                    )}
                    {t.location && <Badge variant="outline">{t.location}</Badge>}
                    <span className="ml-auto text-muted-foreground">source · {t.source_id}</span>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <Button
      variant={active ? "default" : "outline"}
      size="sm"
      className="rounded-full"
      onClick={onClick}
    >
      {children}
    </Button>
  )
}
