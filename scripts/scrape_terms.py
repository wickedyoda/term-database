#!/usr/bin/env python3
"""
Term Scraper
Extracts IT/networking/cybersecurity term definitions from web sources
and writes them into the term database.

Uses the MediaWiki API to fetch Wikipedia glossary pages and parse
definition-list (<dt>/<dd>) pairs into structured term entries.
"""
import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "terms.json")

API = "https://en.wikipedia.org/w/api.php"
UA = "term-database-scraper/1.0 (https://github.com/wickedyoda/term-database; educational reference project)"

CATEGORY_SOURCES = {
    "networking": [
        ("Internet Protocol", "networking concept"),
        ("Transmission Control Protocol", "transport protocol"),
        ("User Datagram Protocol", "transport protocol"),
        ("Hypertext Transfer Protocol", "application protocol"),
        ("Domain Name System", "application protocol"),
        ("Border Gateway Protocol", "routing protocol"),
        ("Open Shortest Path First", "routing protocol"),
        ("Network address translation", "networking concept"),
        ("Virtual private network", "networking concept"),
        ("Quality of service", "networking concept"),
    ],
    "security": [
        ("Phishing", "threat"),
        ("Malware", "threat"),
        ("Ransomware", "threat"),
        ("Denial-of-service attack", "threat"),
        ("Man-in-the-middle attack", "threat"),
        ("Cross-site scripting", "vulnerability"),
        ("SQL injection", "vulnerability"),
        ("Zero-day (computing)", "vulnerability"),
        ("Public key infrastructure", "cryptography"),
        ("Encryption", "cryptography"),
        ("Multi-factor authentication", "identity"),
        ("Role-based access control", "identity"),
    ],
    "infrastructure": [
        ("Cloud computing", "cloud"),
        ("Containerization", "containerisation"),
        ("Kubernetes", "orchestration"),
        ("Infrastructure as code", "provisioning"),
        ("Load balancing (computing)", "networking"),
    ],
    "programming": [
        ("Application programming interface", "api"),
        ("JSON", "data format"),
        ("Regular expression", "data format"),
        ("Version control", "tooling"),
    ],
}


def fetch_api(title, timeout=25):
    """Fetch a Wikipedia page's extract via the MediaWiki API."""
    params = urllib.parse.urlencode({
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "explaintext": "1",
        "redirects": "1",
        "titles": title,
    })
    url = f"{API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            return page.get("extract") or ""
    except Exception as e:
        print(f"  ! API error for '{title}': {e}")
    return ""


def first_sentence(text, max_len=300):
    """Return the first sentence of a page extract, cleaned."""
    if not text:
        return ""
    text = html.unescape(text).strip()
    text = re.sub(r"\s+", " ", text)
    # Drop empty parentheticals left behind when IPA/pronunciation is stripped
    # by explaintext (e.g. "pronounced /ˈdʒeɪsən/" -> "pronounced or )").
    text = re.sub(r",?\s*\(\s*\)", "", text)
    text = re.sub(r",?\s+pronounced\s+or\s+\)", ")", text)
    m = re.match(r"^(.+?[.!?])(?:\s|$)", text)
    sentence = (m.group(1) if m else text[:max_len]).strip()
    if len(sentence) > max_len:
        window = sentence[:max_len]
        # Prefer ending on a sentence boundary within the window.
        cut = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
        if cut > max_len // 2:
            sentence = window[:cut + 1].strip()
        else:
            sentence = window.rsplit(" ", 1)[0].rstrip(",") + "…"
    return sentence


def is_disambiguation(text):
    """Return True if the extract looks like a Wikipedia disambiguation page."""
    head = text[:400].lower()
    return "may refer to:" in head or "may stand for:" in head


def slugify(term):
    s = term.strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)          # drop parenthetical qualifiers
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_db(db):
    db["metadata"]["total_terms"] = len(db["terms"])
    db["metadata"]["updated_at"] = time.strftime("%Y-%m-%d", time.gmtime())
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def scrape_category(category, dry_run=False, limit=None):
    print(f"Scraping category: {category}")
    sources = CATEGORY_SOURCES.get(category, [])
    if limit:
        sources = sources[:limit]
    db = load_db()
    existing = {t["id"] for t in db["terms"]}
    # Dedup on id AND on term/alias names (case-insensitive) to avoid duplicate concepts.
    existing_names = set()
    for t in db["terms"]:
        existing_names.add(t["term"].lower())
        for a in t.get("aliases", []):
            existing_names.add(a.lower())
    added = skipped = dupes = 0

    for title, subcategory in sources:
        term_id = slugify(title)
        if term_id in existing or title.lower() in existing_names:
            print(f"  = {title} (already present)")
            dupes += 1
            continue
        extract = fetch_api(title)
        if not extract:
            skipped += 1
            continue
        if is_disambiguation(extract):
            print(f"  = {title} (disambiguation page, skipped)")
            skipped += 1
            continue
        definition = first_sentence(extract)
        if not definition or len(definition) < 20:
            skipped += 1
            continue
        entry = {
            "id": term_id,
            "term": title,
            "definition": definition,
            "category": category,
            "subcategory": subcategory,
            "aliases": [],
            "related": [],
            "sources": [f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"],
            "added_at": time.strftime("%Y-%m-%d", time.gmtime()),
        }
        if dry_run:
            print(f"  + [dry-run] {title} — {definition[:80]}...")
            added += 1
            continue
        db["terms"].append(entry)
        existing.add(term_id)
        added += 1
        print(f"  + {title}")
        time.sleep(0.5)  # be polite to the API

    if not dry_run:
        save_db(db)
    print(f"  Added: {added}, skipped: {skipped}, already present: {dupes}")
    return added


def refresh_definitions(dry_run=False, limit=None):
    """Re-fetch definitions for existing terms that carry a Wikipedia source."""
    db = load_db()
    updated = skipped = 0
    targets = [t for t in db["terms"] if t.get("sources") and "wikipedia.org" in t["sources"][0]]
    if limit:
        targets = targets[:limit]
    for t in targets:
        # Use the full title (including any disambiguating parenthetical) so the
        # API resolves the intended article, not a disambiguation page.
        title = t["term"]
        extract = fetch_api(title)
        if extract and is_disambiguation(extract):
            print(f"  = {t['id']} (disambiguation page, skipped)")
            skipped += 1
            continue
        definition = first_sentence(extract) if extract else ""
        if not definition or len(definition) < 20:
            print(f"  = {t['id']} (no usable extract)")
            skipped += 1
            continue
        if definition == t["definition"]:
            print(f"  = {t['id']} (unchanged)")
            skipped += 1
            continue
        if not dry_run:
            t["definition"] = definition
            t["updated_at"] = time.strftime("%Y-%m-%d", time.gmtime())
        updated += 1
        print(f"  ~ {t['id']}: {definition[:90]}...")
        time.sleep(0.5)
    if not dry_run and updated:
        save_db(db)
    print(f"  Updated: {updated}, unchanged/skipped: {skipped}")
    return updated


def main():
    parser = argparse.ArgumentParser(description="Term Scraper")
    parser.add_argument("--category", choices=list(CATEGORY_SOURCES.keys()) + ["all"], default="all")
    parser.add_argument("--dry-run", action="store_true", help="Fetch and preview without writing")
    parser.add_argument("--limit", type=int, help="Limit number of sources per category")
    parser.add_argument("--refresh", action="store_true",
                        help="Re-fetch definitions for existing Wikipedia-sourced terms")
    args = parser.parse_args()

    if args.refresh:
        print("Refreshing existing definitions from Wikipedia…")
        refresh_definitions(dry_run=args.dry_run, limit=args.limit)
        return 0

    cats = list(CATEGORY_SOURCES) if args.category == "all" else [args.category]
    total = 0
    for cat in cats:
        total += scrape_category(cat, dry_run=args.dry_run, limit=args.limit)
    print(f"\nTotal terms {'that would be ' if args.dry_run else ''}added: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
