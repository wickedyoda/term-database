# Contributing to Term Database

Thank you for contributing. This document describes the process and standards.

## Adding a term

Use the CLI:

```bash
python3 scripts/term_manager.py add "TERM" "Definition." --category networking --subcategory transport --aliases "Alternate Name" --related "tcp"
```

Or edit `data/terms.json` directly, following the schema in the README.

## Standards

1. **Accuracy** — Definitions must be factually correct. Cite sources when possible.
2. **Neutrality** — No marketing language, vendor bias, or opinions.
3. **Conciseness** — Aim for one to three sentences.
4. **Consistency** — Use the same category and subcategory vocabulary.
5. **No duplicates** — Check for existing terms before adding.

## Categories

- `networking` — protocols, addressing, routing, switching, wireless
- `security` — threats, vulnerabilities, controls, cryptography, IAM
- `infrastructure` — cloud, containers, orchestration, virtualisation
- `programming` — languages, APIs, data formats, paradigms
- `general` — anything that does not fit the above

## Validation

The CI workflow (`validate.yml`) checks:

- `data/terms.json` is valid JSON
- Every term has `id`, `term`, `definition`, and `category`
- Every `id` is unique
- Every `category` is one of the allowed values
- Every `related` ID exists in the database

All checks must pass before a pull request can be merged.
