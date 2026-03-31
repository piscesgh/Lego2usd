import unittest

from backend.app.services.part_registry import PartRegistry


class PartRegistryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = PartRegistry()

    def test_exact_match_ranks_first(self) -> None:
        results = self.registry.search("45602")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].sku, "45602")

    def test_prefix_search_returns_curated_parts(self) -> None:
        results = self.registry.search("456")
        self.assertEqual([part.sku for part in results], ["45601", "45602", "45603"])

    def test_supported_catalog_is_limited(self) -> None:
        results = self.registry.search("")
        self.assertEqual(len(results), 5)


if __name__ == "__main__":
    unittest.main()

