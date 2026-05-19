import "./styles/globals.css"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { TremplinsView } from "@/components/TremplinsView"
import { CatalogueView } from "@/components/CatalogueView"
import { FestivalsView } from "@/components/FestivalsView"

export default function App() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto w-full max-w-5xl px-6 py-10">
        <header className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight">Tremplins NA</h1>
          <p className="text-sm text-muted-foreground">
            Veille des tremplins musicaux et festivals en Nouvelle-Aquitaine
          </p>
        </header>

        <Tabs defaultValue="tremplins" className="space-y-6">
          <TabsList>
            <TabsTrigger value="tremplins">Tremplins</TabsTrigger>
            <TabsTrigger value="festivals">Festivals</TabsTrigger>
            <TabsTrigger value="catalogue">Catalogue</TabsTrigger>
          </TabsList>
          <TabsContent value="tremplins">
            <TremplinsView />
          </TabsContent>
          <TabsContent value="festivals">
            <FestivalsView />
          </TabsContent>
          <TabsContent value="catalogue">
            <CatalogueView />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}
