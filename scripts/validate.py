#!/usr/bin/env python3
"""
Term Database Validator
Validates data/terms.json against the schema and referential integrity rules.
"""
import argparse
import json
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "terms.json")

ALLOWED_CATEGORIES = {"networking", "security", "infrastructure", "programming", "general"}
REQUIRED_FIELDS = ["id", "term", "definition", "category"]

def load_db():
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_schema(db):
    errors = []
    if "metadata" not in db or "terms" not in db:
        errors.append("Missing 'metadata' or 'terms' key at top level.")
        return errors
    for i, t in enumerate(db["terms"]):
        for field in REQUIRED_FIELDS:
            if field not in t or not t[field]:
                errors.append(f"Term #{i} missing or empty required field '{field}': {t.get('term', t.get('id', i))}")
        if t.get("category") and t["category"] not in ALLOWED_CATEGORIES:
            errors.append(f"Term '{t.get('term')}' has invalid category '{t['category']}'. Allowed: {', '.join(sorted(ALLOWED_CATEGORIES))}")
    return errors

def check_duplicates(db):
    errors = []
    seen = {}
    for t in db["terms"]:
        tid = t.get("id")
        if tid in seen:
            errors.append(f"Duplicate id '{tid}' (terms: '{seen[tid]}' and '{t.get('term')}')")
        else:
            seen[tid] = t.get("term")
    return errors

def check_references(db):
    errors = []
    ids = {t.get("id") for t in db["terms"]}
    for t in db["terms"]:
        for ref in t.get("related", []):
            if ref not in ids:
                errors.append(f"Term '{t.get('term')}' references unknown id '{ref}'")
    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate term database")
    parser.add_argument("--duplicates", action="store_true", help="Check for duplicate IDs")
    parser.add_argument("--references", action="store_true", help="Check related-term references")
    args = parser.parse_args()

    try:
        db = load_db()
    except json.JSONDecodeError as e:
        print(f"FAIL: data/terms.json is not valid JSON: {e}")
        return 1
    except FileNotFoundError:
        print(f"FAIL: {DB_PATH} not found.")
        return 1

    errors = validate_schema(db)
    if args.duplicates:
        errors += check_duplicates(db)
    if args.references:
        errors += check_references(db)

    if errors:
        print(f"FAIL: {len(errors)} validation error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"PASS: {db['metadata'].get('total_terms', len(db['terms']))} terms validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
