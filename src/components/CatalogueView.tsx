import { useVenuesStats } from "@/hooks/useVenuesStats"
import { DEPT_LABELS } from "@/types/tremplin"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChartCard } from "@/components/charts/BarChartCard"
import { VenuesList } from "@/components/VenuesList"
import { Loader2 } from "lucide-react"

const CATEGORY_LABELS: Record<string, string> = {
  "lieu-de-diffusion": "Lieux de diffusion",
  festival: "Festivals",
  "equipe-artistique": "Équipes artistiques",
  "lieu-de-travail-artistique": "Lieux de travail artistique",
  "editeur-label": "Éditeurs / labels",
  "organisateur-regulier-sans-lieu": "Organisateurs réguliers",
  "service-culturel-public": "Services culturels publics",
  "producteur-tourneur": "Producteurs / tourneurs",
  "accompagnement-conseil": "Accompagnement / conseil",
  "reseau-agence": "Réseaux / agences",
  "formation-initiale": "Formation initiale",
  autre: "Autres",
}

export function CatalogueView() {
  const state = useVenuesStats()

  if (state.status === "loading") {
    return (
      <div className="flex items-center gap-2 py-12 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        chargement du catalogue…
      </div>
    )
  }
  if (state.status === "error") {
    return (
      <Card className="border-destructive/40 bg-destructive/5">
        <CardHeader>
          <CardTitle className="text-destructive">Erreur</CardTitle>
        </CardHeader>
        <CardContent className="text-sm">{state.error}</CardContent>
      </Card>
    )
  }

  const catData = state.categories.map((c) => ({
    name: CATEGORY_LABELS[c.category] ?? c.category,
    total: c.total,
  }))

  const deptData = state.depts
    .filter((d) => d.dept !== "—")
    .map((d) => ({
      name: DEPT_LABELS[d.dept] ?? d.dept,
      total: d.total,
    }))

  return (
    <div className="space-y-8">
      <div className="grid gap-3 sm:grid-cols-3">
        <StatCard label="Structures" value={state.total} />
        <StatCard
          label="Crawlables"
          value={state.crawlable}
          hint={`${Math.round((state.crawlable / state.total) * 100)} % du catalogue`}
        />
        <StatCard label="Catégories" value={state.categories.length} />
      </div>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Toutes les structures</h2>
        <VenuesList />
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Par catégorie</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChartCard
              data={catData}
              xKey="name"
              bars={[{ key: "total", label: "Structures" }]}
              height={320}
              layout="vertical"
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Par département</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChartCard
              data={deptData}
              xKey="name"
              bars={[{ key: "total", label: "Structures" }]}
              height={320}
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Détail par catégorie</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {state.categories.map((c) => (
            <div key={c.category} className="flex items-center justify-between gap-2">
              <span>{CATEGORY_LABELS[c.category] ?? c.category}</span>
              <span className="flex items-center gap-2">
                <Badge variant="outline">{c.total}</Badge>
                <Badge variant={c.crawlable > 0 ? "default" : "secondary"}>
                  {c.crawlable} crawlables
                </Badge>
              </span>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

function StatCard({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <Card>
      <CardContent className="py-6">
        <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className="mt-1 text-3xl font-semibold tabular-nums">{value.toLocaleString("fr-FR")}</div>
        {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
      </CardContent>
    </Card>
  )
}
