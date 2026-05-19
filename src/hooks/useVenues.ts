import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"

export type Venue = {
  id: string
  name: string
  city: string
  dept: string | null
  postal_code: string | null
  category: string | null
  discipline: string | null
  email: string | null
  url: string | null
  crawlable: boolean
}

type State =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: Venue[]; error: null }
  | { status: "error"; data: null; error: string }

const PAGE = 1000  // limite stricte de PostgREST côté serveur (rôle anon)

export function useVenues() {
  const [state, setState] = useState<State>({ status: "loading", data: null, error: null })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const all: Venue[] = []
      let from = 0
      // Pagine tant qu'on reçoit une page pleine. Sûr : on s'arrête au plus tard
      // à 50000 lignes (50 itérations) pour éviter une boucle infinie.
      for (let i = 0; i < 50; i++) {
        const { data, error } = await supabase
          .from("venues")
          .select("id,name,city,dept,postal_code,category,discipline,email,url,crawlable")
          .order("name")
          .range(from, from + PAGE - 1)

        if (cancelled) return
        if (error) {
          setState({ status: "error", data: null, error: error.message })
          return
        }
        const batch = (data ?? []) as Venue[]
        all.push(...batch)
        if (batch.length < PAGE) break
        from += PAGE
      }

      if (!cancelled) {
        setState({ status: "ready", data: all, error: null })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return state
}
