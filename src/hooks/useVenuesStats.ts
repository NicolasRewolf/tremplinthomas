import { useEffect, useState } from "react"
import { supabase } from "@/lib/supabase"

export type CategoryCount = { category: string; total: number; crawlable: number }
export type DeptCount = { dept: string; total: number; crawlable: number }

type State =
  | { status: "loading"; categories: null; depts: null; total: 0; crawlable: 0; error: null }
  | {
      status: "ready"
      categories: CategoryCount[]
      depts: DeptCount[]
      total: number
      crawlable: number
      error: null
    }
  | { status: "error"; categories: null; depts: null; total: 0; crawlable: 0; error: string }

const initial: State = {
  status: "loading",
  categories: null,
  depts: null,
  total: 0,
  crawlable: 0,
  error: null,
}

const PAGE = 1000

export function useVenuesStats() {
  const [state, setState] = useState<State>(initial)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      // PostgREST cap le rôle anon à 1000 rows/requête → on pagine.
      const all: { category: string; dept: string | null; crawlable: boolean }[] = []
      let from = 0
      for (let i = 0; i < 50; i++) {
        const { data, error } = await supabase
          .from("venues")
          .select("category,dept,crawlable")
          .range(from, from + PAGE - 1)

        if (cancelled) return
        if (error) {
          setState({
            status: "error",
            categories: null,
            depts: null,
            total: 0,
            crawlable: 0,
            error: error.message,
          })
          return
        }
        const batch = data ?? []
        all.push(...(batch as typeof all))
        if (batch.length < PAGE) break
        from += PAGE
      }

      const cats = new Map<string, CategoryCount>()
      const depts = new Map<string, DeptCount>()
      let crawlable = 0
      for (const r of all) {
        if (r.crawlable) crawlable++
        const cat = r.category ?? "—"
        const c = cats.get(cat) ?? { category: cat, total: 0, crawlable: 0 }
        c.total++
        if (r.crawlable) c.crawlable++
        cats.set(cat, c)

        const dept = r.dept ?? "—"
        const d = depts.get(dept) ?? { dept, total: 0, crawlable: 0 }
        d.total++
        if (r.crawlable) d.crawlable++
        depts.set(dept, d)
      }
      const catList = Array.from(cats.values()).sort((a, b) => b.total - a.total)
      const deptList = Array.from(depts.values()).sort((a, b) => b.total - a.total)
      if (!cancelled) {
        setState({
          status: "ready",
          categories: catList,
          depts: deptList,
          total: all.length,
          crawlable,
          error: null,
        })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return state
}
