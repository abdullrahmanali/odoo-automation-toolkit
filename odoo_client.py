"""
odoo_client.py
--------------
A small, well-documented wrapper around Odoo's External API (XML-RPC).

WHY THIS EXISTS (read this before the code):
Odoo is normally used through its web UI — you click "New Contact",
fill a form, click Save. But every business eventually needs to do
something in bulk that the UI can't: import 500 customers from a CSV,
sync orders from another system, or run a nightly data export. That's
what the External API is for, and being able to script it is exactly
what separates "I clicked around in Odoo once" from "I can automate
Odoo for a business" in an interview.

HOW ODOO'S API WORKS, IN PLAIN TERMS:
Odoo exposes two XML-RPC endpoints:
  - /xmlrpc/2/common  → login / authentication only
  - /xmlrpc/2/object  → everything else (create, read, update, search...)

Every business object in Odoo (a customer, a product, an invoice) is a
"model" identified by a dotted name, e.g. "res.partner" for contacts,
"product.product" for products, "sale.order" for sales orders. You
never talk to a special "customer API" — you always call the same
generic execute_kw() method and tell it which model, which action
(create/write/search_read/unlink...), and which data.

Run the self-test (no live Odoo server needed) with:
    python3 -m unittest test_odoo_client.py -v
"""
import xmlrpc.client


class OdooClient:
    """A thin, readable wrapper around Odoo's XML-RPC API.

    Example:
        client = OdooClient(url="http://localhost:8069", db="mycompany",
                             username="admin", password="admin")
        client.login()
        new_id = client.create("res.partner", {"name": "Acme Corp", "is_company": True})
    """

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self._common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
        self._models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def login(self) -> int:
        """Authenticate and cache the numeric user id (uid) Odoo needs
        for every subsequent call. Returns the uid."""
        self.uid = self._common.authenticate(self.db, self.username, self.password, {})
        if not self.uid:
            raise ConnectionError(
                "Odoo login failed — check url/db/username/password. "
                "(This is the #1 thing that goes wrong: db name is case-sensitive.)"
            )
        return self.uid

    def _ensure_logged_in(self):
        if self.uid is None:
            self.login()

    def create(self, model: str, values: dict) -> int:
        """Create one record. Returns its new id.
        Example: create("res.partner", {"name": "Ahmed", "email": "a@x.com"})
        """
        self._ensure_logged_in()
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, "create", [values]
        )

    def create_many(self, model: str, records: list[dict]) -> list[int]:
        """Bulk create — this is the actual point of automating Odoo.
        Doing 500 individual create() calls works but is slow (one
        network round-trip each); Odoo's create() also accepts a list
        of dicts to create many records in a single call."""
        self._ensure_logged_in()
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, "create", [records]
        )

    def search_read(self, model: str, domain: list = None, fields: list = None, limit: int = 0):
        """Read records matching a domain filter.
        domain uses Odoo's filter syntax, e.g. [["city", "=", "Khobar"]].
        An empty domain [] means "all records" — be careful with that
        on a real database.
        """
        self._ensure_logged_in()
        domain = domain or []
        kwargs = {"fields": fields} if fields else {}
        if limit:
            kwargs["limit"] = limit
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, "search_read", [domain], kwargs
        )

    def write(self, model: str, ids: list[int], values: dict) -> bool:
        """Update one or more existing records by id."""
        self._ensure_logged_in()
        return self._models.execute_kw(
            self.db, self.uid, self.password, model, "write", [ids, values]
        )
