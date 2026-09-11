"""
test_odoo_client.py
--------------------
Proves odoo_client.py's logic is correct WITHOUT needing a running Odoo
server. This matters for two reasons:

1. Practical: you can verify this code works before you even have Odoo
   installed (weeks 2-5 of the learning plan).
2. What it demonstrates: this is how you test code that talks to an
   external system — you don't test the real network call, you test
   that YOUR code builds the right request and handles the response
   correctly. This is a real, reusable skill, not just an Odoo trick.

We do this with unittest.mock, which replaces the XML-RPC ServerProxy
with a fake object we fully control, so the test is fast and needs no
network access.

Run:
    python3 -m unittest test_odoo_client.py -v
"""
import unittest
from unittest.mock import MagicMock, patch

from odoo_client import OdooClient


class TestOdooClient(unittest.TestCase):
    def setUp(self):
        # Patch xmlrpc.client.ServerProxy everywhere odoo_client.py uses it,
        # so OdooClient() never actually opens a network connection.
        patcher = patch("odoo_client.xmlrpc.client.ServerProxy")
        self.addCleanup(patcher.stop)
        self.mock_server_proxy = patcher.start()

        # Two separate proxies get created (common + models) — give each
        # call to ServerProxy(...) its own fresh mock.
        self.mock_common = MagicMock()
        self.mock_models = MagicMock()
        self.mock_server_proxy.side_effect = [self.mock_common, self.mock_models]

        self.client = OdooClient(
            url="http://localhost:8069", db="testdb",
            username="admin", password="admin",
        )

    def test_login_success_stores_uid(self):
        self.mock_common.authenticate.return_value = 7
        uid = self.client.login()
        self.assertEqual(uid, 7)
        self.assertEqual(self.client.uid, 7)
        self.mock_common.authenticate.assert_called_once_with(
            "testdb", "admin", "admin", {}
        )

    def test_login_failure_raises_clear_error(self):
        self.mock_common.authenticate.return_value = False
        with self.assertRaises(ConnectionError):
            self.client.login()

    def test_create_calls_execute_kw_with_correct_model_and_values(self):
        self.mock_common.authenticate.return_value = 1
        self.mock_models.execute_kw.return_value = 42

        new_id = self.client.create("res.partner", {"name": "Ahmed"})

        self.assertEqual(new_id, 42)
        self.mock_models.execute_kw.assert_called_once_with(
            "testdb", 1, "admin", "res.partner", "create", [{"name": "Ahmed"}]
        )

    def test_create_auto_logs_in_if_not_logged_in_yet(self):
        # This is the behaviour worth testing: calling create() before
        # login() should still work, because _ensure_logged_in() should
        # call login() automatically exactly once.
        self.mock_common.authenticate.return_value = 5
        self.mock_models.execute_kw.return_value = 1

        self.assertIsNone(self.client.uid)
        self.client.create("res.partner", {"name": "Sara"})
        self.assertEqual(self.client.uid, 5)
        self.mock_common.authenticate.assert_called_once()

    def test_search_read_passes_domain_and_fields(self):
        self.mock_common.authenticate.return_value = 1
        self.mock_models.execute_kw.return_value = [{"id": 1, "name": "Sara"}]

        result = self.client.search_read(
            "res.partner", domain=[["city", "=", "Khobar"]], fields=["name"]
        )

        self.assertEqual(result, [{"id": 1, "name": "Sara"}])
        self.mock_models.execute_kw.assert_called_once_with(
            "testdb", 1, "admin", "res.partner", "search_read",
            [[["city", "=", "Khobar"]]], {"fields": ["name"]},
        )

    def test_create_many_sends_a_single_batched_call(self):
        self.mock_common.authenticate.return_value = 1
        self.mock_models.execute_kw.return_value = [10, 11, 12]

        records = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
        ids = self.client.create_many("res.partner", records)

        self.assertEqual(ids, [10, 11, 12])
        # The key thing this test protects: create_many must make ONE
        # execute_kw call with the whole list, not three separate calls.
        self.assertEqual(self.mock_models.execute_kw.call_count, 1)


if __name__ == "__main__":
    unittest.main()
