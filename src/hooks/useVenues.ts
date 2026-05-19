import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"

export type VenueRow = {
  id: string
  slug_canon: string | null
  name: string
  city: string
  dept: string | null
  postal_code: string | null
  category: string | null
  discipline: string | null
  email: string | null
  url: string | null
  crawlable: boolean
  origin: string | null
}

// Représentation fusionnée d'une venue : une "entité réelle" (par slug_canon)
// qui peut être référencée dans plusieurs sources (ACNA, Wikipedia, etc.).
export type Venue = {
  slug_canon: string
  name: string
  city: string
  dept: string | null
  postal_code: string | null
  discipline: string | null
  email: string | null
  url: string | null
  crawlable: boolean
  categories: string[]   // toutes les catégories où cette venue apparaît
  origins: string[]      // toutes les sources où elle apparaît
}

type State =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: Venue[]; error: null }
  | { status: "error"; data: null; error: string }

const PAGE = 1000

// Préférence d'URL : ACNA est la source la plus fiable côté URL (vérifiée par
// l'Agence Culturelle), puis Wikipedia, puis culture.gouv (souvent vide), puis le reste.
const URL_PRIORITY: Record<string, number> = {
  acna: 0,
  wikipedia: 1,
  manual: 2,
  discovery: 3,
  other: 4,
}

function pickUrl(rows: VenueRow[]): string | null {
  const withUrl = rows.filter((r) => r.url)
  if (!withUrl.length) return null
  withUrl.sort((a, b) => {
    const pa = URL_PRIORITY[a.origin ?? "other"] ?? 99
    const pb = URL_PRIORITY[b.origin ?? "other"] ?? 99
    return pa - pb
  })
  return withUrl[0].url
}

function firstNonNull<T>(values: (T | null | undefined)[]): T | null {
  for (const v of values) {
    if (v !== null && v !== undefined && v !== "") return v as T
  }
  return null
}

function mergeRows(rows: VenueRow[]): Venue {
  // On garde le nom le plus long (le plus descriptif en général) — sauf si
  // un nom court vient d'ACNA, qui est la source canonique du nom officiel.
  const acnaRow = rows.find((r) => r.origin === "acna")
  const name = acnaRow?.name ?? rows.reduce((a, b) => (a.name.length >= b.name.length ? a : b)).name
  const city = acnaRow?.city ?? rows[0].city

  const categories = Array.from(new Set(rows.map((r) => r.category).filter(Boolean))) as string[]
  const origins = Array.from(new Set(rows.map((r) => r.origin).filter(Boolean))) as string[]

  return {
    slug_canon: rows[0].slug_canon ?? "",
    name,
    city,
    dept: firstNonNull(rows.map((r) => r.dept)),
    postal_code: firstNonNull(rows.map((r) => r.postal_code)),
    discipline: firstNonNull(rows.map((r) => r.discipline)),
    email: firstNonNull(rows.map((r) => r.email)),
    url: pickUrl(rows),
    crawlable: rows.some((r) => r.crawlable),
    categories: categories.sort(),
    origins,
  }
}

export function useVenues() {
  const [state, setState] = useState<State>({ status: "loading", data: null, error: null })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const all: VenueRow[] = []
      let from = 0
      for (let i = 0; i < 50; i++) {
        const { data, error } = await supabase
          .from("venues")
          .select(
            "id,slug_canon,name,city,dept,postal_code,category,discipline,email,url,crawlable,origin"
          )
          .order("name")
          .range(from, from + PAGE - 1)

        if (cancelled) return
        if (error) {
          setState({ status: "error", data: null, error: error.message })
          return
        }
        const batch = (data ?? []) as VenueRow[]
        all.push(...batch)
        if (batch.length < PAGE) break
        from += PAGE
      }

      // Group by slug_canon
      const groups = new Map<string, VenueRow[]>()
      for (const r of all) {
        const key = r.slug_canon ?? `${r.name}::${r.city}`
        const arr = groups.get(key) ?? []
        arr.push(r)
        groups.set(key, arr)
      }
      const merged = Array.from(groups.values())
        .map(mergeRows)
        .sort((a, b) => a.name.localeCompare(b.name, "fr"))

      if (!cancelled) {
        setState({ status: "ready", data: merged, error: null })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return state
}
