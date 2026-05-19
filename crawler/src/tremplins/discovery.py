"""Découverte de nouvelles sources candidates.

Stratégie : on ne tente PAS d'énumérer toutes les structures de NA. À la place, on
extrait les domaines tiers cités par les sources déjà connues (Le RIM, SMAC...)
et on les propose pour validation manuelle avant ajout à config/sources.yaml.

Usage :
    python -m tremplins.discovery
    python -m tremplins.discovery --add-googling
"""
import argparse
import logging
from collections import Counter
from urllib.parse import urlparse

import httpx
from selectolax.parser import HTMLParser

from .config import load_sources
from .fetcher import UA, TIMEOUT

log = logging.getLogger(__name__)

# Domaines qu'on ne propose pas comme sources candidates
BLACKLIST_DOMAINS = {
    "facebook.com", "www.facebook.com", "m.facebook.com",
    "instagram.com", "www.instagram.com",
    "twitter.com", "x.com", "www.twitter.com",
    "youtube.com", "www.youtube.com", "youtu.be",
    "linkedin.com", "www.linkedin.com",
    "spotify.com", "open.spotify.com",
    "google.com", "www.google.com", "maps.google.com",
}


def crawl_outlinks() -> Counter:
    """Compte les domaines externes cités par les sources connues."""
    known = load_sources()
    known_domains = {urlparse(s["url"]).netloc for s in known}
    counter: Counter = Counter()

    with httpx.Client(headers={"User-Agent": UA}, timeout=TIMEOUT) as client:
        for source in known:
            try:
                r = client.get(source["url"], follow_redirects=True)
                r.raise_for_status()
            except Exception as e:
                log.warning("skip %s: %s", source["id"], e)
                continue

            tree = HTMLParser(r.text)
            for a in tree.css("a[href]"):
                href = a.attributes.get("href") or ""
                if not href.startswith(("http://", "https://")):
                    continue
                netloc = urlparse(href).netloc.lower()
                if not netloc or netloc in known_domains or netloc in BLACKLIST_DOMAINS:
                    continue
                if netloc.endswith((".gouv.fr",)):  # bruit institutionnel
                    continue
                counter[netloc] += 1
    return counter


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser()
    p.add_argument("--top", type=int, default=30)
    args = p.parse_args()

    counter = crawl_outlinks()
    print("\nCandidats à ajouter à config/sources.yaml (les plus cités par tes sources actuelles) :")
    print("─" * 70)
    for domain, n in counter.most_common(args.top):
        print(f"  {n:>3}×  https://{domain}/")
    print("─" * 70)
    print("→ inspecte chaque domaine, garde uniquement les structures musicales NA,")
    print("  puis ajoute-les à config/sources.yaml avec le bon code département.")


if __name__ == "__main__":
    main()
