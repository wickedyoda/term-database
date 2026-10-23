# Term Database

A central, community-maintained database of **IT, networking, and cybersecurity** terms with definitions.

Data is stored as structured JSON (`data/terms.json`), making it easy to search, query, and integrate into other tools, wikis, and applications.

## Purpose

This repository collects and curates technical terminology so it can be:

- Searched from the command line
- Imported into wikis, documentation, or chatbots
- Used as a reference for onboarding, study, and cross-team alignment
- Extended by scraping the web for new terms

## Structure

```
term-database/
├── data/
│   └── terms.json          # The database (single source of truth)
├── scripts/
│   ├── term_manager.py     # CLI: add / search / list / export / stats
│   └── scrape_terms.py     # Web scraper: harvest terms into the database
├── docs/                   # Extra documentation
└── .github/workflows/      # CI validation
```

## Data Schema

Each term is an object in `terms[]`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Slugified unique identifier (e.g. `tcp`) |
| `term` | string | The canonical term or acronym |
| `definition` | string | Plain-language definition |
| `category` | string | One of: `networking`, `security`, `infrastructure`, `programming`, `general` |
| `subcategory` | string | Finer grouping (e.g. `transport`, `web`, `cryptography`) |
| `aliases` | string[] | Alternate names / expansions |
| `related` | string[] | IDs of related terms |
| `sources` | string[] | Where the definition came from (URLs) |
| `added_at` | string | Date added (`YYYY-MM-DD`) |

## Usage

```bash
# Add a term
python3 scripts/term_manager.py add "ARP" "Address Resolution Protocol — maps IP addresses to MAC addresses." --category networking --subcategory data-link

# Search
python3 scripts/term_manager.py search "encryption"

# List by category
python3 scripts/term_manager.py list --category security

# Export
python3 scripts/term_manager.py export --format markdown

# Statistics
python3 scripts/term_manager.py stats
```

### Scraping new terms

```bash
# Preview what would be added (no writes)
python3 scripts/scrape_terms.py --category networking --dry-run

# Scrape all categories from Wikipedia
python3 scripts/scrape_terms.py --category all

# Refresh existing definitions from their Wikipedia sources
python3 scripts/scrape_terms.py --refresh
```

The scraper deduplicates on term ID **and** on term/alias names, skips
disambiguation pages, and cites the source URL on every scraped entry.

## Contributing

1. Fork the repository
2. Add terms using `term_manager.py add` or edit `data/terms.json` directly
3. Keep definitions accurate, neutral, and concise
4. Submit a pull request

## License

[CC BY-SA 4.0](LICENSE) — attribution required, share alike.
