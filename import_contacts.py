"""
import_contacts.py
-------------------
Bulk-imports contacts from a CSV into Odoo as res.partner records.

This is the actual real-world use case for odoo_client.py: instead of
manually clicking "New Contact" 65 times, read a CSV and push it in
one batched call.

BEFORE YOU RUN THIS FOR REAL:
1. Install Odoo Community locally (part of weeks 2-5 of the learning
   plan) and create a database.
2. Fill in ODOO_URL / ODOO_DB / ODOO_USERNAME / ODOO_PASSWORD below
   (or better, set them as environment variables — never commit real
   credentials to a public repo).
3. Run with --dry-run first. It prints exactly what WOULD be created
   without touching Odoo at all, so you can sanity-check the data.

Usage:
    python3 import_contacts.py --dry-run
    python3 import_contacts.py            # actually creates the records
"""
import argparse
import csv
import os
from pathlib import Path

from odoo_client import OdooClient

ODOO_URL = os.environ.get("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.environ.get("ODOO_DB", "mycompany")
ODOO_USERNAME = os.environ.get("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD", "admin")

CSV_PATH = Path(__file__).parent / "data" / "customers_sample.csv"


def load_contacts(csv_path: Path) -> list[dict]:
    """Read the CSV and translate each row into the field names Odoo's
    res.partner model expects. This mapping step is the part that
    changes every time the source data is different — everything else
    in this project stays the same."""
    contacts = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            contacts.append({
                "name": row["customer_name"],
                "city": row["city"],
                "phone": row["phone"] or False,   # Odoo wants False, not "", for empty
                "email": row["email"] or False,
                "is_company": False,
                "customer_rank": 1,   # marks this partner as a customer in Odoo
            })
    return contacts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                         help="Print what would be created, without calling Odoo")
    args = parser.parse_args()

    contacts = load_contacts(CSV_PATH)
    print(f"Loaded {len(contacts)} contact(s) from {CSV_PATH.name}")

    if args.dry_run:
        print("\n--dry-run: nothing was sent to Odoo. Preview:")
        for c in contacts:
            print(f"  - {c['name']} ({c['city']}) phone={c['phone']} email={c['email']}")
        return

    client = OdooClient(url=ODOO_URL, db=ODOO_DB,
                         username=ODOO_USERNAME, password=ODOO_PASSWORD)
    client.login()
    new_ids = client.create_many("res.partner", contacts)
    print(f"Created {len(new_ids)} contact(s) in Odoo with ids: {new_ids}")


if __name__ == "__main__":
    main()
