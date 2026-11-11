#!/usr/bin/env python3
"""Fetch my publication list from NASA ADS and write _data/publications.json.

The Jekyll pages (index.html, publications.html) render that file, so the
publication list never needs editing by hand.

Usage:
    ADS_TOKEN=xxxx python3 scripts/update_publications.py

Get a token at https://ui.adsabs.harvard.edu/user/settings/token. In GitHub
Actions it comes from the repository secret ADS_TOKEN.

If the request fails, the script exits non-zero and leaves the existing data
file untouched, so the site keeps the last good list.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ORCID = "0000-0002-0461-3029"
SURNAME = "Daley-Yates"

# ORCID catches every paper claimed in ADS; the author search catches any
# that haven't been claimed yet.
QUERY = f'orcid:{ORCID} OR author:"{SURNAME}, S"'

# ADS document types to list. Conference abstracts, software records,
# errata, proposals, etc. are left out.
INCLUDE_DOCTYPES = {
    "article",
    "eprint",
    "inproceedings",
    "inbook",
    "book",
    "phdthesis",
    "mastersthesis",
}

# Long author lists are shortened: up to MAX_AUTHORS are shown in full,
# beyond that the first SHOWN_WHEN_TRUNCATED followed by "et al.".
MAX_AUTHORS = 5
SHOWN_WHEN_TRUNCATED = 3

API_URL = "https://api.adsabs.harvard.edu/v1/search/query"
FIELDS = [
    "bibcode",
    "title",
    "author",
    "year",
    "pubdate",
    "pub",
    "volume",
    "page",
    "doi",
    "identifier",
    "citation_count",
    "property",
    "doctype",
]
PAGE_SIZE = 200

OUT_FILE = Path(__file__).resolve().parent.parent / "_data" / "publications.json"

ALLOWED_TITLE_TAGS = re.compile(r"&lt;(/?)(sub|sup|i|em|b)&gt;", re.IGNORECASE)


def fetch(token: str) -> list[dict]:
    docs: list[dict] = []
    start = 0
    while True:
        params = urllib.parse.urlencode(
            {
                "q": QUERY,
                "fl": ",".join(FIELDS),
                "rows": PAGE_SIZE,
                "start": start,
                "sort": "date desc, bibcode desc",
            }
        )
        req = urllib.request.Request(
            f"{API_URL}?{params}",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "sddyates.github.io publication updater",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        batch = body["response"]["docs"]
        docs.extend(batch)
        start += len(batch)
        if not batch or start >= body["response"]["numFound"]:
            return docs


def format_author(name: str) -> str:
    """'Stevens, Ian R.' -> 'Stevens I. R.'; collaboration names pass through."""
    if "," not in name:
        return name.strip()
    surname, given = (part.strip() for part in name.split(",", 1))
    initials = []
    for part in given.replace(".", " ").split():
        pieces = [p for p in part.split("-") if p]
        initials.append("-".join(p[0] + "." for p in pieces))
    return " ".join([surname, *initials]).strip()


def is_me(name: str) -> bool:
    return name.split(",")[0].strip().lower() == SURNAME.lower()


def authors_html(authors: list[str]) -> str:
    def render(name: str) -> str:
        text = html.escape(format_author(name))
        return f"<strong>{text}</strong>" if is_me(name) else text

    if len(authors) <= MAX_AUTHORS:
        return ", ".join(render(a) for a in authors)

    shown = authors[:SHOWN_WHEN_TRUNCATED]
    out = ", ".join(render(a) for a in shown) + ", et al."
    if not any(is_me(a) for a in shown):
        me = next((a for a in authors if is_me(a)), None)
        if me:
            out += f" (incl. {render(me)})"
    return out


def clean_title(raw: str) -> str:
    # Escape everything, then restore simple formatting tags such as <SUB>.
    escaped = html.escape(html.unescape(raw), quote=False)
    return ALLOWED_TITLE_TAGS.sub(lambda m: f"<{m.group(1)}{m.group(2).lower()}>", escaped)


def arxiv_id(doc: dict) -> str | None:
    for ident in doc.get("identifier", []):
        if ident.lower().startswith("arxiv:"):
            return ident.split(":", 1)[1]
    return None


def convert(doc: dict) -> dict:
    authors = doc.get("author", [])
    doi = (doc.get("doi") or [None])[0]
    arxiv = arxiv_id(doc)
    page = (doc.get("page") or [None])[0]
    return {
        "bibcode": doc["bibcode"],
        "title": clean_title((doc.get("title") or ["Untitled"])[0]),
        "authors_html": authors_html(authors),
        "first_author": bool(authors) and is_me(authors[0]),
        "year": doc.get("year"),
        "venue": doc.get("pub"),
        "volume": doc.get("volume"),
        "page": page,
        "refereed": "REFEREED" in doc.get("property", []),
        "doctype": doc.get("doctype"),
        "citations": doc.get("citation_count") or 0,
        "ads_url": f"https://ui.adsabs.harvard.edu/abs/{doc['bibcode']}/abstract",
        "doi_url": f"https://doi.org/{doi}" if doi else None,
        "arxiv_url": f"https://arxiv.org/abs/{arxiv}" if arxiv else None,
    }


def h_index(citations: list[int]) -> int:
    ranked = sorted(citations, reverse=True)
    return sum(1 for i, c in enumerate(ranked, start=1) if c >= i)


def main() -> int:
    token = os.environ.get("ADS_TOKEN", "").strip()
    if not token:
        print("ADS_TOKEN is not set; leaving publications unchanged.", file=sys.stderr)
        return 1

    try:
        docs = fetch(token)
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        print(f"ADS request failed: {exc}", file=sys.stderr)
        return 1

    papers = [convert(d) for d in docs if d.get("doctype") in INCLUDE_DOCTYPES]
    if not papers:
        print("ADS returned no publications; leaving file unchanged.", file=sys.stderr)
        return 1

    data = {
        "updated": dt.date.today().isoformat(),
        "source": "NASA ADS",
        "ads_search_url": "https://ui.adsabs.harvard.edu/search/q="
        + urllib.parse.quote(QUERY)
        + "&sort=date%20desc%2C%20bibcode%20desc",
        "metrics": {
            "papers": len(papers),
            "refereed": sum(p["refereed"] for p in papers),
            "first_author": sum(p["first_author"] for p in papers),
            "citations": sum(p["citations"] for p in papers),
            "h_index": h_index([p["citations"] for p in papers]),
        },
        "papers": papers,
    }

    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    m = data["metrics"]
    print(
        f"Wrote {m['papers']} papers ({m['refereed']} refereed, "
        f"{m['citations']} citations, h={m['h_index']}) to {OUT_FILE}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
