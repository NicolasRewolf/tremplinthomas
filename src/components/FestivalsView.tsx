import { useMemo, useState } from "react"
import { useVenues, type Venue } from "@/hooks/useVenues"
import { DEPT_LABELS } from "@/types/tremplin"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Loader2, Search, Music } from "lucide-react"

const PAGE_SIZE = 50

const MUSIC_KEYWORDS = /musi|chans|jazz|rock|hip[- ]?hop|rap|electro|électro|classique|world|pop|metal|folk|reggae|techno|blues/i

function normalize(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
}

function isFestival(v: Venue): boolean {
  return v.categories.includes("festival") || v.categories.includes("festival-min-culture")
}

function isMusicFestival(v: Venue): boolean {
  if (!isFestival(v)) return false
  const txt = `${v.name} ${v.discipline ?? ""}`
  return MUSIC_KEYWORDS.test(txt)
}

export function FestivalsView() {
  const state = useVenues()
  const [search, setSearch] = useState("")
  const [dept, setDept] = useState<string>("all")
  const [musicOnly, setMusicOnly] = useState(true)
  const [visible, setVisible] = useState(PAGE_SIZE)

  const all = state.status === "ready" ? state.data : []

  const festivals = useMemo(
    () => all.filter((v) => (musicOnly ? isMusicFestival(v) : isFestival(v))),
    [all, musicOnly]
  )

  const departments = useMemo(() => {
    const s = new Set<string>()
    for (const v of festivals) if (v.dept) s.add(v.dept)
    return Array.from(s).sort()
  }, [festivals])

  const filtered = useMemo(() => {
    const q = normalize(search.trim())
    return festivals.filter((v) => {
      if (dept !== "all" && (v.dept ?? "") !== dept) return false
      if (q && !normalize(`${v.name} ${v.city}`).includes(q)) return false
      return true
    })
  }, [festivals, search, dept])

  useMemo(() => setVisible(PAGE_SIZE), [search, dept, musicOnly])

  if (state.status === "loading") {
    return (
      <div className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        chargement des festivals…
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
      <div className="flex flex-wrap gap-2">
        <Button
          variant={musicOnly ? "default" : "outline"}
          size="sm"
          className="rounded-full gap-1.5"
          onClick={() => setMusicOnly(true)}
        >
          <Music className="h-3.5 w-3.5" />
          Musique uniquement ({all.filter(isMusicFestival).length})
        </Button>
        <Button
          variant={!musicOnly ? "default" : "outline"}
          size="sm"
          className="rounded-full"
          onClick={() => setMusicOnly(false)}
        >
          Tous les festivals ({all.filter(isFestival).length})
        </Button>
      </div>

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
      </div>

      <div className="text-xs text-muted-foreground">
        {filtered.length.toLocaleString("fr-FR")} festival(s)
        {musicOnly ? " musical(aux)" : ""} en Nouvelle-Aquitaine
      </div>

      <ul className="grid gap-3 sm:grid-cols-2">
        {filtered.slice(0, visible).map((v) => (
          <li key={v.slug_canon}>
            <FestivalCard venue={v} />
          </li>
        ))}
        {filtered.length === 0 && (
          <li className="col-span-full">
            <Card>
              <CardContent className="py-8 text-center text-sm text-muted-foreground">
                Aucun festival ne correspond aux filtres.
              </CardContent>
            </Card>
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

function FestivalCard({ venue }: { venue: Venue }) {
  return (
    <Card className="h-full transition-colors hover:border-foreground/30">
      <CardContent className="space-y-2 py-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="truncate font-medium leading-snug">
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
            <div className="mt-0.5 text-xs text-muted-foreground">
              {venue.city}
              {venue.dept ? ` · ${DEPT_LABELS[venue.dept] ?? venue.dept}` : ""}
            </div>
          </div>
        </div>
        {venue.discipline && (
          <Badge variant="secondary" className="text-[11px]">
            {venue.discipline}
          </Badge>
        )}
      </CardContent>
    </Card>
  )
}
