export type TremplinStatus = "open" | "closed" | "unknown" | "draft"

export type Tremplin = {
  id: number
  url: string
  source_id: string | null     // null si le tremplin vient d'une venue (catalogue ACNA)
  venue_id: string | null
  dept: string | null
  title: string
  summary: string | null
  deadline: string | null
  location: string | null
  confidence: number | null
  status: TremplinStatus
  edition_year: number | null
  reasoning: string | null
  first_seen: string
  last_seen: string
}

export const DEPT_LABELS: Record<string, string> = {
  "16": "Charente",
  "17": "Charente-Maritime",
  "19": "Corrèze",
  "23": "Creuse",
  "24": "Dordogne",
  "33": "Gironde",
  "40": "Landes",
  "47": "Lot-et-Garonne",
  "64": "Pyrénées-Atlantiques",
  "79": "Deux-Sèvres",
  "86": "Vienne",
  "87": "Haute-Vienne",
  NA: "Régional",
}
