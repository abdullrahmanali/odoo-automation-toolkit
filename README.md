# Odoo Automation Toolkit

A small, documented Python wrapper around Odoo's External API (XML-RPC),
plus a real bulk-import script — the kind of automation an ERP/data
role actually asks for once you're past just clicking around the UI.

**This is a learning project, in progress alongside my Odoo curriculum
(weeks 2-5 of my study plan).** The code is tested and correct on its
own (see `test_odoo_client.py`), but running the import script against
a live Odoo database is the next step once Odoo Community is installed.

## Why this project

Odoo's UI covers 95% of daily use, but every real ERP job eventually
needs bulk data operations the UI can't do — importing hundreds of
contacts, migrating data from Excel, syncing with another system. Being
able to script Odoo's API is a genuine differentiator for an entry-level
candidate.

## What's inside

| File | What it does |
|---|---|
| `odoo_client.py` | A readable wrapper around Odoo's XML-RPC API — `login`, `create`, `create_many`, `search_read`, `write` — with comments explaining how Odoo's model system works |
| `test_odoo_client.py` | Unit tests using `unittest.mock` that prove the wrapper builds correct requests, without needing a live Odoo server |
| `import_contacts.py` | A real, runnable script: reads a CSV, maps it to Odoo's `res.partner` fields, and bulk-creates the records (with a `--dry-run` mode that needs no Odoo connection at all) |
| `data/customers_sample.csv` | Sample input data |

## How to run it

```bash
pip install python-dateutil  # (xmlrpc.client is in the Python standard library — no install needed)

# 1. Prove the client logic works, no Odoo required:
python3 -m unittest test_odoo_client.py -v

# 2. Preview what an import would do, still no Odoo required:
python3 import_contacts.py --dry-run

# 3. Once Odoo Community is installed and running locally:
export ODOO_URL="http://localhost:8069"
export ODOO_DB="mycompany"
export ODOO_USERNAME="admin"
export ODOO_PASSWORD="admin"
python3 import_contacts.py
```

## How Odoo's External API actually works (the part worth understanding)

Odoo exposes two XML-RPC endpoints: `/xmlrpc/2/common` for login, and
`/xmlrpc/2/object` for everything else. Every business object — a
contact, a product, an invoice — is a "model" with a dotted name
(`res.partner`, `product.product`, `sale.order`...). There's no special
per-object API; you always call the same generic method
(`execute_kw`) and tell it which model, which action
(`create`/`search_read`/`write`...), and what data. Once that clicks,
automating any part of Odoo is the same four-step pattern repeated.

## Next steps (as I progress through my learning plan)

- Run this against a real local Odoo install and capture screenshots
- Add `import_products.py` and `import_orders.py` using the same pattern
- Connect this to the cleaned data from the [erp-data-cleaning-sql](../erp-data-cleaning-sql) project
