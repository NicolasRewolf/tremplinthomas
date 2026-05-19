"""Parser .ods minimaliste — pas de dépendance externe.

Un .ods est un zip contenant content.xml en OpenDocument format. On y lit
les `<table:table-row>` et `<table:table-cell>` (avec leur attribut
`number-columns-repeated` pour les cellules vides étendues).

Usage :
    rows = read_ods(path)
    # rows est un Iterator[dict[str, str]] — la première ligne sert d'en-tête
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Iterator

NS = {
    "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
}
T = f"{{{NS['table']}}}"
TX = f"{{{NS['text']}}}"


def _cell_text(cell: ET.Element) -> str:
    """Concatène tous les <text:p> d'une cellule, séparés par espace."""
    parts = []
    for p in cell.iter(f"{TX}p"):
        if p.text:
            parts.append(p.text)
    return " ".join(parts).strip()


def _expand_row(row: ET.Element) -> list[str]:
    """Liste de valeurs en respectant number-columns-repeated."""
    out: list[str] = []
    for cell in row.findall(f"{T}table-cell"):
        rep = int(cell.get(f"{T}number-columns-repeated", "1"))
        # Bornage : certaines lignes ont une cellule "vide" répétée plusieurs
        # milliers de fois (padding). On limite à 200 pour éviter d'exploser.
        rep = min(rep, 200)
        value = _cell_text(cell)
        for _ in range(rep):
            out.append(value)
    while out and not out[-1]:
        out.pop()
    return out


def read_ods(path: Path | str) -> Iterator[dict[str, str]]:
    """Itère les lignes du premier sheet sous forme de dict[header → cell]."""
    with zipfile.ZipFile(path) as z, z.open("content.xml") as f:
        tree = ET.parse(f)
    header: list[str] = []
    for row in tree.getroot().iter(f"{T}table-row"):
        cells = _expand_row(row)
        if not cells:
            continue
        if not header:
            header = cells
            continue
        # Pad/trim pour aligner sur l'en-tête
        padded = cells + [""] * (len(header) - len(cells))
        yield {k: v for k, v in zip(header, padded[: len(header)])}
