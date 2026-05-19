import { useMemo, useState } from "react"
import { useTremplins } from "@/hooks/useTremplins"
import { DEPT_LABELS, type Tremplin, type TremplinStatus } from "@/types/tremplin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CalendarClock, MapPin, ExternalLink, Loader2, HelpCircle, XCircle, CheckCircle2 } from "lucide-react"

type StatusFilter = "open" | "all" | "closed" | "unknown"

export function TremplinsView() {
  const state = useTremplins()
  const [dept, setDept] = useState<string>("all")
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("open")

  const all = state.status === "ready" ? state.data : []
  const counts = useMemo(() => {
    const c = { open: 0, closed: 0, unknown: 0, draft: 0 }
    for (const t of all) c[t.status] = (c[t.status] ?? 0) + 1
    return c
  }, [all])

  const filtered = useMemo(() => {
    return all.filter((t) => {
      if (statusFilter !== "all" && t.status !== statusFilter) return false
      if (dept !== "all" && (t.dept ?? "NA") !== dept) return false
      return true
    })
  }, [all, statusFilter, dept])

  const departments = useMemo(() => {
    const s = new Set<string>()
    for (const t of all) {
      if (statusFilter === "all" || t.status === statusFilter) s.add(t.dept ?? "NA")
    }
    return Array.from(s).sort()
  }, [all, statusFilter])

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <StatusToggle
          value="open"
          current={statusFilter}
          onClick={setStatusFilter}
          icon={<CheckCircle2 className="h-3.5 w-3.5" />}
          count={counts.open}
        >
          Ouverts
        </StatusToggle>
        <StatusToggle
          value="closed"
          current={statusFilter}
          onClick={setStatusFilter}
          icon={<XCircle className="h-3.5 w-3.5" />}
          count={counts.closed}
        >
          Clos
        </StatusToggle>
        <StatusToggle
          value="unknown"
          current={statusFilter}
          onClick={setStatusFilter}
          icon={<HelpCircle className="h-3.5 w-3.5" />}
          count={counts.unknown}
        >
          À vérifier
        </StatusToggle>
        <StatusToggle
          value="all"
          current={statusFilter}
          onClick={setStatusFilter}
          icon={null}
          count={counts.open + counts.closed + counts.unknown + counts.draft}
        >
          Tous
        </StatusToggle>
        <span className="ml-auto text-sm text-muted-foreground">
          {state.status === "loading" && (
            <span className="inline-flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              chargement…
            </span>
          )}
        </span>
      </div>

      {state.status === "error" && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardHeader>
            <CardTitle className="text-destructive">Erreur de chargement</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">{state.error}</CardContent>
        </Card>
      )}

      {state.status === "ready" && filtered.length === 0 && all.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center text-muted-foreground">
            Aucun tremplin détecté pour l'instant.
            <br />
            Lance le crawler : <code>cd crawler && python -m tremplins.pipeline --include-venues</code>
          </CardContent>
        </Card>
      )}

      {state.status === "ready" && filtered.length === 0 && all.length > 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            Aucun tremplin {statusToLabel(statusFilter)} pour ce filtre.
          </CardContent>
        </Card>
      )}

      {state.status === "ready" && filtered.length > 0 && (
        <>
          <div className="flex flex-wrap gap-2">
            <FilterChip active={dept === "all"} onClick={() => setDept("all")}>
              Tous départements
            </FilterChip>
            {departments.map((code) => {
              const count = filtered.filter((t) => (t.dept ?? "NA") === code).length
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
                <TremplinCard tremplin={t} />
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

function TremplinCard({ tremplin: t }: { tremplin: Tremplin }) {
  const dimmed = t.status !== "open"
  return (
    <Card className={`transition-colors hover:border-foreground/30 ${dimmed ? "opacity-70" : ""}`}>
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0 pb-3">
        <div className="min-w-0">
          <div className="mb-1 flex items-center gap-2">
            <StatusBadge status={t.status} />
            {t.edition_year && (
              <Badge variant="outline" className="text-[11px]">
                édition {t.edition_year}
              </Badge>
            )}
          </div>
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
          {t.summary && <p className="mt-1 text-sm text-muted-foreground">{t.summary}</p>}
          {t.reasoning && t.status !== "open" && (
            <p className="mt-1 text-xs italic text-muted-foreground/80">
              Raison : {t.reasoning}
            </p>
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
        <span className="ml-auto text-muted-foreground">
          source · {t.source_id ?? "venue"}
        </span>
      </CardContent>
    </Card>
  )
}

function StatusBadge({ status }: { status: TremplinStatus }) {
  switch (status) {
    case "open":
      return (
        <Badge className="gap-1 bg-emerald-600 hover:bg-emerald-600 text-white">
          <CheckCircle2 className="h-3 w-3" /> ouvert
        </Badge>
      )
    case "closed":
      return (
        <Badge variant="secondary" className="gap-1">
          <XCircle className="h-3 w-3" /> clos
        </Badge>
      )
    case "unknown":
      return (
        <Badge variant="outline" className="gap-1">
          <HelpCircle className="h-3 w-3" /> à vérifier
        </Badge>
      )
    case "draft":
      return <Badge variant="outline">brouillon</Badge>
  }
}

function StatusToggle({
  value,
  current,
  onClick,
  icon,
  count,
  children,
}: {
  value: StatusFilter
  current: StatusFilter
  onClick: (v: StatusFilter) => void
  icon: React.ReactNode
  count: number
  children: React.ReactNode
}) {
  const active = current === value
  return (
    <Button
      size="sm"
      variant={active ? "default" : "outline"}
      className="gap-1.5 rounded-full"
      onClick={() => onClick(value)}
    >
      {icon}
      {children} <span className="opacity-60">({count})</span>
    </Button>
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

function statusToLabel(s: StatusFilter): string {
  return s === "open" ? "ouvert" : s === "closed" ? "clos" : s === "unknown" ? "à vérifier" : ""
}
