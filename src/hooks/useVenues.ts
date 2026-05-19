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

export function useVenues() {
  const [state, setState] = useState<State>({ status: "loading", data: null, error: null })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const { data, error } = await supabase
        .from("venues")
        .select("id,name,city,dept,postal_code,category,discipline,email,url,crawlable")
        .order("name")
        .limit(10000)

      if (cancelled) return
      if (error) {
        setState({ status: "error", data: null, error: error.message })
      } else {
        setState({ status: "ready", data: (data ?? []) as Venue[], error: null })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return state
}
