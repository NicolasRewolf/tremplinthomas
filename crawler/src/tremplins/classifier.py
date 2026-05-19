import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from anthropic import Anthropic

from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, load_keywords

log = logging.getLogger(__name__)


_FENCE_RE = re.compile(r"```(?:json)?\s*(.+?)\s*```", re.DOTALL | re.IGNORECASE)


def _parse_json_lenient(raw: str) -> dict | None:
    """Parse une réponse LLM même si elle est enveloppée dans des fences
    markdown ou précédée de texte. Strict d'abord, puis tolérant."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = _FENCE_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _norm(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c)
    )


def keyword_prefilter(text: str) -> bool:
    """Cheap filter — returns True if the text is worth showing to the LLM."""
    kw = load_keywords()
    n = _norm(text)
    if any(_norm(x) in n for x in kw.get("exclude", [])):
        return False
    if any(_norm(x) in n for x in kw.get("strong", [])):
        return True
    has_medium = any(_norm(x) in n for x in kw.get("medium", []))
    has_context = any(_norm(x) in n for x in kw.get("context", []))
    return has_medium and has_context


@dataclass
class Verdict:
    is_tremplin: bool
    confidence: float
    status: str = "unknown"           # 'open' | 'closed' | 'unknown'
    title: str | None = None
    summary: str | None = None
    deadline: str | None = None       # AAAA-MM-JJ idéalement
    edition_year: int | None = None
    location: str | None = None
    reasoning: str | None = None      # pourquoi cette classification (debug)


SYSTEM_TEMPLATE = """Tu es un classifieur très précis pour une veille de tremplins musicaux en Nouvelle-Aquitaine (France).

Date du jour : {today}.

DÉFINITION d'un tremplin musical : un APPEL À CANDIDATURES (concours, sélection, scène ouverte sélective) destiné à des artistes/groupes/musiciens, débouchant sur des concerts, un accompagnement, un prix ou une diffusion. Il a généralement une période d'inscription, une deadline, des critères d'éligibilité.

NE SONT PAS DES TREMPLINS :
- Un concert programmé (pas d'appel à candidatures)
- Une formation/résidence/atelier sans sélection compétitive
- Un appel à projets pour des structures (pas pour des artistes individuels)
- Un tremplin non-musical (sport, emploi, numérique, cinéma, etc.)
- Une page institutionnelle qui mentionne un tremplin passé sans appel actif
- Une simple actualité ou article de presse sur un tremplin

DÉTERMINATION DU STATUT :
- "open"    : la deadline d'inscription est future OU non précisée ET la page parle d'une édition à venir (année courante ou suivante)
- "closed"  : la deadline est passée, OU la page mentionne explicitement que les candidatures sont closes, OU la page parle uniquement d'éditions passées (résultats, palmarès)
- "unknown" : impossible de trancher avec certitude

Lis la page ATTENTIVEMENT. Si tu vois "Tremplin XXXX" sans année plus récente, vérifie : XXXX est-il passé ?

Réponds UNIQUEMENT par un objet JSON brut, sans texte avant/après, sans fences markdown :
{{
  "is_tremplin": bool,
  "confidence": float entre 0 et 1,
  "status": "open" | "closed" | "unknown",
  "title": string court (nom officiel du tremplin) ou null,
  "summary": 1-2 phrases factuelles en français (quoi, qui, pour qui) ou null,
  "deadline": "AAAA-MM-JJ" (privilégié) ou texte court ou null,
  "edition_year": entier (année de l'édition) ou null,
  "location": ville et/ou département si précisé sinon null,
  "reasoning": 1 phrase qui justifie le statut (pour audit)
}}

Si is_tremplin=false → confidence basse, autres champs à null.
En cas de doute sur status, choisis "unknown" plutôt que "open" : on préfère ne pas afficher qu'afficher un truc périmé."""


def _build_user_prompt(url: str, title: str, snippet: str, source_context: str | None) -> str:
    parts = [f"URL : {url}"]
    if title:
        parts.append(f"Titre HTML : {title}")
    if source_context:
        parts.append(f"Source surveillée : {source_context}")
    parts.append("\n--- CONTENU DE LA PAGE ---\n")
    parts.append(snippet)
    return "\n".join(parts)


def llm_verify(
    url: str,
    title: str,
    text: str,
    source_context: str | None = None,
) -> Verdict:
    """Classifie une page avec Claude. Le source_context (ex. 'Le Krakatoa,
    Mérignac, smac, dept 33') aide le LLM à ancrer géographiquement."""
    if not ANTHROPIC_API_KEY:
        log.warning("ANTHROPIC_API_KEY missing — skipping LLM verification")
        return Verdict(is_tremplin=True, confidence=0.4, title=title or url)

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    # Sonnet 4.6 gère facilement 12k chars dans le contexte. On donne au LLM
    # plus de matière pour repérer les éditions passées planquées en bas de page.
    snippet = text[:12000]
    system = SYSTEM_TEMPLATE.format(today=date.today().isoformat())
    user_msg = _build_user_prompt(url, title, snippet, source_context)

    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = msg.content[0].text.strip()
    data = _parse_json_lenient(raw)
    if data is None:
        log.warning("LLM returned non-JSON for %s: %r", url, raw[:200])
        return Verdict(is_tremplin=False, confidence=0.0)

    status_raw = (data.get("status") or "unknown").lower().strip()
    if status_raw not in ("open", "closed", "unknown"):
        status_raw = "unknown"

    return Verdict(
        is_tremplin=bool(data.get("is_tremplin")),
        confidence=float(data.get("confidence") or 0.0),
        status=status_raw,
        title=data.get("title") or title,
        summary=data.get("summary"),
        deadline=data.get("deadline"),
        edition_year=data.get("edition_year"),
        location=data.get("location"),
        reasoning=data.get("reasoning"),
    )
