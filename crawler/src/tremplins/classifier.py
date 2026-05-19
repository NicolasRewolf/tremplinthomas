import json
import logging
import re
import unicodedata
from dataclasses import dataclass

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
    # Fence markdown ```json ... ```
    m = _FENCE_RE.search(raw)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Premier objet JSON apparent
    m = re.search(r"\{[^{}]*\}", raw, re.DOTALL)
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
    title: str | None = None
    summary: str | None = None
    deadline: str | None = None
    location: str | None = None


SYSTEM = """Tu es un classifieur pour une veille de tremplins musicaux en Nouvelle-Aquitaine (France).
Un "tremplin musical" est un appel à candidatures pour des artistes/groupes (concours, sélection, scène ouverte sélective) qui débouche sur des concerts, un accompagnement ou un prix.

Réponds UNIQUEMENT par un objet JSON brut, sans aucun texte avant ou après, sans fences markdown (PAS de ```), avec ces champs :
{
  "is_tremplin": bool,
  "confidence": float entre 0 et 1,
  "title": string court ou null,
  "summary": 1 à 2 phrases en français ou null,
  "deadline": "AAAA-MM-JJ" ou texte court ou null,
  "location": ville et/ou département si trouvé, sinon null
}

Règles :
- is_tremplin=true UNIQUEMENT si la page décrit un appel à candidatures musical OUVERT (pas un compte-rendu d'édition passée sans nouvelle session annoncée).
- is_tremplin=false si la page concerne un autre type de tremplin (sport, emploi, etc.) ou si elle est hors Nouvelle-Aquitaine sans lien régional.
- En cas de doute, mets is_tremplin=false avec une confidence basse."""


def llm_verify(url: str, title: str, text: str) -> Verdict:
    if not ANTHROPIC_API_KEY:
        log.warning("ANTHROPIC_API_KEY missing — skipping LLM verification, defaulting to pass-through")
        return Verdict(is_tremplin=True, confidence=0.4, title=title or url)

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    snippet = text[:6000]
    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=400,
        system=SYSTEM,
        messages=[
            {"role": "user", "content": f"URL: {url}\nTitre: {title}\n\n---\n{snippet}"},
            # Pré-remplit la réponse — force le modèle à commencer par "{"
            # et donc à produire du JSON brut sans fences markdown.
            {"role": "assistant", "content": "{"},
        ],
    )
    raw = "{" + msg.content[0].text.strip()
    data = _parse_json_lenient(raw)
    if data is None:
        log.warning("LLM returned non-JSON for %s: %r", url, raw[:200])
        return Verdict(is_tremplin=False, confidence=0.0)

    return Verdict(
        is_tremplin=bool(data.get("is_tremplin")),
        confidence=float(data.get("confidence") or 0.0),
        title=data.get("title") or title,
        summary=data.get("summary"),
        deadline=data.get("deadline"),
        location=data.get("location"),
    )
