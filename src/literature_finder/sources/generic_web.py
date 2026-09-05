"""Optional browser-search handoff helpers.

This module intentionally does not scrape search engines or publisher pages.
It creates lawful landing-page queries for an Agent/browser integration.
"""

from __future__ import annotations

import urllib.parse


class GenericWebAdapter:
    name = "Generic web"

    @staticmethod
    def search_urls(query: str) -> dict[str, str]:
        encoded = urllib.parse.quote_plus(query)
        return {
            "Crossref": f"https://search.crossref.org/?q={encoded}",
            "OpenAlex": f"https://openalex.org/works?search={encoded}",
            "Semantic Scholar": f"https://www.semanticscholar.org/search?q={encoded}",
            "Google Scholar": f"https://scholar.google.com/scholar?q={encoded}",
        }

