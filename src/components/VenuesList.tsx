import { useMemo, useState } from "react"
import { useVenues, type Venue } from "@/hooks/useVenues"
import { DEPT_LABELS } from "@/types/tremplin"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Loader2, Search } from "lucide-react"

const PAGE_SIZE = 50

const CATEGORY_LABELS: Record<string, string> = {
  "lieu-de-diffusion": "Lieu de diffusion",
  festival: "Festival",
  "equipe-artistique": "Équipe artistique",
  "lieu-de-travail-artistique": "Lieu de travail artistique",
  "editeur-label": "Éditeur / label",
  "organisateur-regulier-sans-lieu": "Organisateur régulier",
  "service-culturel-public": "Service culturel public",
  "producteur-tourneur": "Producteur / tourneur",
  "accompagnement-conseil": "Accompagnement / conseil",
  "reseau-agence": "Réseau / agence",
  "formation-initiale": "Formation initiale",
  autre: "Autre",
  wikipedia: "Wikipédia",
}

function normalize(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
}

export function VenuesList() {
  const state = useVenues()
  const [search, setSearch] = useState("")
  const [dept, setDept] = useState<string>("all")
  const [category, setCategory] = useState<string>("all")
  const [visible, setVisible] = useState(PAGE_SIZE)

  const all = state.status === "ready" ? state.data : []

  const departments = useMemo(() => {
    const s = new Set<string>()
    for (const v of all) if (v.dept) s.add(v.dept)
    return Array.from(s).sort()
  }, [all])

  const categories = useMemo(() => {
    const s = new Set<string>()
    for (const v of all) if (v.category) s.add(v.category)
    return Array.from(s).sort()
  }, [all])

  const filtered = useMemo(() => {
    const q = normalize(search.trim())
    return all.filter((v) => {
      if (dept !== "all" && (v.dept ?? "") !== dept) return false
      if (category !== "all" && (v.category ?? "") !== category) return false
      if (q && !normalize(`${v.name} ${v.city}`).includes(q)) return false
      return true
    })
  }, [all, search, dept, category])

  // Reset pagination quand un filtre change
  useMemo(() => setVisible(PAGE_SIZE), [search, dept, category])

  if (state.status === "loading") {
    return (
      <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        chargement des structures…
      </div>
    )
  }
  if (state.status === "error") {
    return (
      <Card className="border-destructive/40 bg-destructive/5">
        <CardContent className="py-4 text-sm">{state.error}</CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Recherche par nom ou ville…"
            className="w-full rounded-md border bg-background px-9 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <select
          value={dept}
          onChange={(e) => setDept(e.target.value)}
          className="rounded-md border bg-background px-3 py-2 text-sm"
        >
          <option value="all">Tous départements</option>
          {departments.map((d) => (
            <option key={d} value={d}>
              {DEPT_LABELS[d] ?? d} ({d})
            </option>
          ))}
        </select>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="rounded-md border bg-background px-3 py-2 text-sm"
        >
          <option value="all">Toutes catégories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {CATEGORY_LABELS[c] ?? c}
            </option>
          ))}
        </select>
      </div>

      <div className="text-xs text-muted-foreground">
        {filtered.length.toLocaleString("fr-FR")} structure(s) sur {all.length.toLocaleString("fr-FR")}
      </div>

      <ul className="divide-y divide-border rounded-lg border bg-card">
        {filtered.slice(0, visible).map((v) => (
          <li key={v.id}>
            <VenueRow venue={v} />
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="px-4 py-6 text-center text-sm text-muted-foreground">
            Aucune structure ne correspond aux filtres.
          </li>
        )}
      </ul>

      {visible < filtered.length && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => setVisible((n) => n + PAGE_SIZE)}>
            Voir {Math.min(PAGE_SIZE, filtered.length - visible)} de plus
          </Button>
        </div>
      )}
    </div>
  )
}

function VenueRow({ venue }: { venue: Venue }) {
  return (
    <div className="flex flex-wrap items-center gap-2 px-4 py-3 text-sm">
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium">
          {venue.url ? (
            <a
              href={venue.url}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:underline"
            >
              {venue.name}
              <ExternalLink className="ml-1 inline h-3 w-3 align-middle opacity-60" />
            </a>
          ) : (
            venue.name
          )}
        </div>
        <div className="text-xs text-muted-foreground">
          {venue.city}
          {venue.postal_code ? ` · ${venue.postal_code}` : ""}
          {venue.discipline ? ` · ${venue.discipline}` : ""}
        </div>
      </div>
      {venue.dept && (
        <Badge variant="secondary" className="shrink-0">
          {DEPT_LABELS[venue.dept] ?? venue.dept}
        </Badge>
      )}
      {venue.category && (
        <Badge variant="outline" className="shrink-0 text-[11px]">
          {CATEGORY_LABELS[venue.category] ?? venue.category}
        </Badge>
      )}
    </div>
  )
}
