#!/usr/bin/env python3
"""
Term Database Manager
CLI for adding, searching, and managing IT/networking/security terms.
"""
import argparse
import json
import os
import re
import signal
import sys
from datetime import datetime, timezone

# Exit cleanly when stdout is piped to a consumer that closes early (e.g. `| head`).
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "terms.json")

def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db):
    db["metadata"]["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db["metadata"]["total_terms"] = len(db["terms"])
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def slugify(term):
    s = term.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def add_term(term, definition, category="general", subcategory="", aliases=None, related=None, sources=None):
    db = load_db()
    term_id = slugify(term)
    existing = {t["id"] for t in db["terms"]}
    if term_id in existing:
        print(f"Error: term '{term}' (id={term_id}) already exists.")
        return 1
    entry = {
        "id": term_id,
        "term": term,
        "definition": definition,
        "category": category,
        "subcategory": subcategory,
        "aliases": aliases or [],
        "related": related or [],
        "sources": sources or [],
        "added_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    db["terms"].append(entry)
    save_db(db)
    print(f"Added '{term}' (id={term_id}) to {category}.")
    return 0

def search_terms(query, category=None):
    db = load_db()
    q = query.lower()
    results = []
    for t in db["terms"]:
        if category and t["category"] != category:
            continue
        haystack = " ".join([t["term"], t["definition"], " ".join(t["aliases"])]).lower()
        if q in haystack:
            results.append(t)
    return results

def list_terms(category=None):
    db = load_db()
    terms = db["terms"]
    if category:
        terms = [t for t in terms if t["category"] == category]
    return terms

def export_terms(format="json"):
    db = load_db()
    if format == "json":
        print(json.dumps(db, indent=2, ensure_ascii=False))
    elif format == "markdown":
        for t in db["terms"]:
            print(f"## {t['term']}")
            print(f"**Category:** {t['category']}")
            print(f"**Definition:** {t['definition']}")
            if t["aliases"]:
                print(f"**Aliases:** {', '.join(t['aliases'])}")
            print()

def main():
    parser = argparse.ArgumentParser(description="Term Database Manager")
    sub = parser.add_subparsers(dest="command")

    p_add = sub.add_parser("add", help="Add a term")
    p_add.add_argument("term")
    p_add.add_argument("definition")
    p_add.add_argument("--category", default="general")
    p_add.add_argument("--subcategory", default="")
    p_add.add_argument("--aliases", nargs="*", default=[])
    p_add.add_argument("--related", nargs="*", default=[])

    p_search = sub.add_parser("search", help="Search terms")
    p_search.add_argument("query")
    p_search.add_argument("--category")

    p_list = sub.add_parser("list", help="List terms")
    p_list.add_argument("--category")

    p_export = sub.add_parser("export", help="Export terms")
    p_export.add_argument("--format", default="json", choices=["json", "markdown"])

    p_stats = sub.add_parser("stats", help="Show database statistics")

    args = parser.parse_args()

    if args.command == "add":
        sys.exit(add_term(args.term, args.definition, args.category, args.subcategory, args.aliases, args.related))
    elif args.command == "search":
        results = search_terms(args.query, args.category)
        if not results:
            print(f"No terms found for '{args.query}'.")
        for t in results:
            print(f"[{t['id']}] {t['term']} ({t['category']})")
            print(f"    {t['definition']}")
    elif args.command == "list":
        terms = list_terms(args.category)
        print(f"{len(terms)} terms" + (f" in {args.category}" if args.category else ""))
        for t in terms:
            print(f"  [{t['id']}] {t['term']} ({t['category']})")
    elif args.command == "export":
        export_terms(args.format)
    elif args.command == "stats":
        db = load_db()
        print(f"Total terms: {db['metadata']['total_terms']}")
        print(f"Categories: {', '.join(db['metadata']['categories'])}")
        cats = {}
        for t in db["terms"]:
            cats[t["category"]] = cats.get(t["category"], 0) + 1
        for c, n in sorted(cats.items()):
            print(f"  {c}: {n}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
