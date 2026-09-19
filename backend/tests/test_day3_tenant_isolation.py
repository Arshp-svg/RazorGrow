from types import SimpleNamespace

from app.services.catalog_service import find_candidates


class FakeQuery:
    def __init__(self, products):
        self.products = products

    def filter(self, *conditions):
        return self

    def all(self):
        return self.products


class FakeDB:
    def __init__(self, products):
        self.products = products

    def query(self, model):
        return FakeQuery(self.products)


def test_find_candidates_is_merchant_scoped():
    products = [
        SimpleNamespace(
            merchant_id=1,
            inventory=10,
            category="laptop",
            price=50000,
            use_cases="programming",
            tags="portable",
        ),
        SimpleNamespace(
            merchant_id=2,
            inventory=10,
            category="laptop",
            price=50000,
            use_cases="programming",
            tags="portable",
        ),
    ]

    intent = SimpleNamespace(
        category="laptop",
        budget=70000,
        use_case="programming",
    )

    candidates = find_candidates(FakeDB(products), intent, merchant_id=1)

    assert candidates == products
