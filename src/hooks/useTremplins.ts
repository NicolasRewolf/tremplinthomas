import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"
import type { Tremplin } from "@/types/tremplin"

type State =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: Tremplin[]; error: null }
  | { status: "error"; data: null; error: string }

export function useTremplins() {
  const [state, setState] = useState<State>({ status: "loading", data: null, error: null })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const { data, error } = await supabase
        .from("tremplins")
        .select("*")
        .eq("status", "open")
        .order("deadline", { ascending: true, nullsFirst: false })
        .order("last_seen", { ascending: false })

      if (cancelled) return
      if (error) {
        setState({ status: "error", data: null, error: error.message })
      } else {
        setState({ status: "ready", data: (data ?? []) as Tremplin[], error: null })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return state
}
