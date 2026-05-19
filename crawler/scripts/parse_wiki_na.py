"""Parse la section Nouvelle-Aquitaine du dump Wikipédia 'Liste des salles
de spectacle en France' (input/page-*.md) et produit un YAML candidat à
fusionner dans config/sources.yaml.

Sortie : config/sources_discovered.yaml (URL=null à compléter manuellement
                                          puisque Wikipédia ne donne que des
                                          liens internes vers la page de chaque salle).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input" / "page-2026-05-19-12-05-24.md"
OUT = ROOT / "config" / "sources_discovered.yaml"

# Ville → code département. Liste construite à partir du dump observé.
# Les villes absentes seront loggées et le champ dept sera laissé à null.
CITY_TO_DEPT: dict[str, str] = {
    # Gironde (33)
    "Bordeaux": "33", "Mérignac": "33", "Pessac": "33", "Talence": "33",
    "Cenon": "33", "Floirac": "33", "Bègles": "33", "Bruges": "33",
    "Le Haillan": "33", "Villenave d'Ornon": "33", "Eysines": "33",
    "Saint-Médard-en-Jalles": "33", "Ambarès-et-Lagrave": "33", "Ambès": "33",
    "Saint-Loubès": "33", "Saint-Denis-de-Pile": "33", "Saint-Jean-d'Illac": "33",
    "Tresses": "33", "Fargues-Saint-Hilaire": "33", "Gradignan": "33",
    "Saucats": "33", "Créon": "33", "Langon": "33", "Gujan-Mestras": "33",
    "Arcachon": "33", "Le Teich": "33", "Andernos-les-Bains": "33",
    "Biganos": "33", "Marcheprime": "33",
    # Charente (16)
    "L'Isle-d'Espagnac": "16", "Angoulême": "16",
    # Charente-Maritime (17)
    "La Rochelle": "17", "Saujon": "17",
    # Dordogne (24)
    "Boulazac Isle Manoire": "24", "Boulazac": "24", "Périgueux": "24",
    "Bergerac": "24",
    # Corrèze (19)
    "Brive-la-Gaillarde": "19", "Tulle": "19",
    # Creuse (23)
    "Guéret": "23",
    # Haute-Vienne (87)
    "Limoges": "87",
    # Deux-Sèvres (79)
    "Niort": "79", "Bressuire": "79",
    # Vienne (86)
    "Poitiers": "86", "Chasseneuil-du-Poitou": "86", "Châtellerault": "86",
    "Buxerolles": "86", "Saint-Benoit": "86", "Saint-Benoît": "86",
    "Nouaillé-Maupertuis": "86",
    # Pyrénées-Atlantiques (64)
    "Pau": "64", "Lons": "64", "Bayonne": "64", "Biarritz": "64",
    "Anglet": "64", "Boucau": "64",
    # Landes (40)
    "Dax": "40", "Seignosse": "40", "Luxey": "40",
    # Lot-et-Garonne (47)
    "Agen": "47",
}

# Patterns
SECTION_START = re.compile(r"^###\s+Nouvelle-Aquitaine\s*$")
SECTION_END = re.compile(r"^###\s+")  # toute autre section
# Une ligne "ville" : [Ville](/wiki/...) éventuellement avec parenthèses dans le titre du lien
LINK_LINE = re.compile(r"^\[([^\]]+)\]\(/wiki/[^)]+\)\s*$")
# Capacité : "X places", "X 000 places", "1 200 places", éventuellement suivi de notes
CAPACITY_LINE = re.compile(r"^[\d\s ]+places", re.IGNORECASE)


def slugify(s: str) -> str:
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "venue"


def extract_section(text: str) -> list[str]:
    lines = text.splitlines()
    out, in_section = [], False
    for line in lines:
        if SECTION_START.match(line):
            in_section = True
            continue
        if in_section and SECTION_END.match(line):
            break
        if in_section:
            out.append(line)
    return out


def parse(lines: list[str]) -> list[dict]:
    """Triplets (ville, salle, capacité) séparés par lignes vides.

    Structure observée :
        [Ville](lien)
        <blank>
        [Salle](lien)   ou bien   "Nom de la salle"
        <blank>
        "X places ..."
    """
    # Compacte : enlève les vides pour itérer 3 par 3
    nonblank = [ln.strip() for ln in lines if ln.strip()]
    venues = []
    i = 0
    n = len(nonblank)
    while i < n:
        city_match = LINK_LINE.match(nonblank[i])
        if not city_match:
            i += 1
            continue
        # On a une ville. Il faut une salle puis une capacité ensuite.
        if i + 2 >= n:
            break
        city = city_match.group(1).strip()
        venue_raw = nonblank[i + 1]
        cap_raw = nonblank[i + 2]
        if not CAPACITY_LINE.match(cap_raw):
            # Pas le pattern attendu, on saute juste cette ligne et on continue
            i += 1
            continue
        venue_name = _clean_venue(venue_raw)
        venues.append({
            "city": city,
            "name": venue_name,
            "capacity": cap_raw,
        })
        i += 3
    return venues


def _clean_venue(s: str) -> str:
    """Retire les liens markdown pour ne garder que le texte affiché.

    Wikipédia produit des URLs avec parenthèses échappées \\( \\) et un titre
    entre guillemets, donc on doit gérer les chars échappés dans la regex.
    """
    # Forme Wikipedia avec titre : [N](url "title")  — gère parens échappées dans url
    s = re.sub(r'\[([^\]]+)\]\([^"]*"[^"]*"\)', r"\1", s)
    # Forme markdown standard : [N](url)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return s.strip()


def to_yaml(venues: list[dict]) -> str:
    out_lines = [
        "# Sources candidates extraites automatiquement de la section Nouvelle-Aquitaine",
        "# de la page Wikipédia 'Liste de salles de spectacle en France' (dump du 2026-05-19).",
        "#",
        "# IMPORTANT : URL=null par défaut. Avant fusion dans sources.yaml :",
        "#   1. recherche le site officiel de chaque salle",
        "#   2. vérifie qu'elle organise effectivement (ou pourrait organiser) un tremplin",
        "#   3. retire celles qui ne pertinent pas (grandes arènes type Arkéa, stades...)",
        "#",
    ]
    for v in venues:
        dept = CITY_TO_DEPT.get(v["city"])
        id_ = slugify(v["name"])
        if dept:
            id_ = f"{id_}-{dept}"
        out_lines.append("")
        out_lines.append(f"- id: {id_}")
        out_lines.append(f"  name: {_yaml_str(v['name'])}")
        out_lines.append(f"  city: {_yaml_str(v['city'])}")
        out_lines.append(f"  capacity: {_yaml_str(v['capacity'])}")
        out_lines.append(f"  dept: {dept or 'null'}")
        out_lines.append(f"  url: null  # à compléter manuellement")
        out_lines.append(f"  type: venue")
    return "\n".join(out_lines) + "\n"


def _yaml_str(s: str) -> str:
    if any(c in s for c in ":#'\""):
        escaped = s.replace('"', '\\"')
        return f'"{escaped}"'
    return s


def main():
    if not INPUT.exists():
        sys.exit(f"input manquant : {INPUT}")
    text = INPUT.read_text(encoding="utf-8")
    section = extract_section(text)
    venues = parse(section)

    unknown_cities = sorted({v["city"] for v in venues if v["city"] not in CITY_TO_DEPT})
    OUT.write_text(to_yaml(venues), encoding="utf-8")

    print(f"✅ {len(venues)} salles extraites → {OUT.relative_to(ROOT)}")
    with_dept = sum(1 for v in venues if v["city"] in CITY_TO_DEPT)
    print(f"   dont {with_dept} avec département mappé, {len(venues) - with_dept} sans")
    if unknown_cities:
        print("\n⚠️  Villes non mappées (probablement hors NA ou à ajouter au dict) :")
        for c in unknown_cities:
            print(f"     - {c}")


if __name__ == "__main__":
    main()
