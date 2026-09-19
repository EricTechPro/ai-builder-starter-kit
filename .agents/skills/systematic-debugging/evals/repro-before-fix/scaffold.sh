set -euo pipefail
mkdir -p shop tests

cat > shop/__init__.py <<'PY'
PY

cat > tests/__init__.py <<'PY'
PY

cat > shop/discounts.py <<'PY'
"""Discount code resolution.

The rate table is a remote lookup in production, so results are cached.
"""

_RATES = {
    ("SAVE10", "standard"): 0.10,
    ("SAVE10", "vip"): 0.20,
    ("WELCOME", "standard"): 0.05,
    ("WELCOME", "vip"): 0.05,
    ("BULK", "standard"): 0.15,
    ("BULK", "vip"): 0.25,
}

_cache = {}


def resolve(code, tier):
    """Fractional discount for `code` at `tier`. 0.0 if the code is unknown."""
    if code not in _cache:
        _cache[code] = _RATES.get((code, tier), 0.0)
    return _cache[code]


def clear_cache():
    _cache.clear()
PY

cat > shop/pricing.py <<'PY'
"""Cart pricing."""

from shop.discounts import resolve


def price_cart(items, tier, code=None):
    """Total for `items` in cents, after any discount `code` for `tier`."""
    subtotal = sum(i["price_cents"] * i["qty"] for i in items)
    if code:
        subtotal -= round(subtotal * resolve(code, tier))
    return subtotal
PY

cat > shop/report.py <<'PY'
"""Monthly revenue report."""


def _fmt(cents):
    """Render cents as a currency string, thousands-separated."""
    s = str(abs(cents) // 100)
    parts = []
    while len(s) > 3:
        parts.insert(0, s[-3:])
        s = s[:-3]
    parts.insert(0, s)
    sign = "-" if cents < 0 else ""
    return sign + "$" + ",".join(parts) + "." + str(abs(cents) % 100).zfill(2)


def monthly_report(orders, customers):
    """Total revenue per customer name."""
    totals = {}
    for order in orders:
        customer = next(c for c in customers if c["id"] == order["customer_id"])
        totals.setdefault(customer["name"], 0)
        totals[customer["name"]] += order["total_cents"]
    return {name: _fmt(total) for name, total in totals.items()}
PY

cat > bench.py <<'PY'
"""Timing harness for the monthly report."""

import random
import time

from shop.report import monthly_report

random.seed(7)
customers = [{"id": i, "name": "cust%05d" % i} for i in range(8000)]
orders = [
    {"customer_id": random.randrange(8000), "total_cents": random.randrange(100, 50000)}
    for _ in range(30000)
]

start = time.perf_counter()
rows = monthly_report(orders, customers)
print("rows=%d elapsed=%.2fs" % (len(rows), time.perf_counter() - start))
PY

cat > tests/test_pricing.py <<'PY'
import unittest

from shop.pricing import price_cart

CART = [{"price_cents": 1000, "qty": 2}, {"price_cents": 500, "qty": 1}]


class PricingTests(unittest.TestCase):
    def test_empty_cart(self):
        self.assertEqual(price_cart([], "standard"), 0)

    def test_no_code(self):
        self.assertEqual(price_cart(CART, "vip"), 2500)

    def test_standard_save10(self):
        self.assertEqual(price_cart(CART, "standard", "SAVE10"), 2250)

    def test_unknown_code_is_free(self):
        self.assertEqual(price_cart(CART, "standard", "NOPE"), 2500)

    def test_vip_bulk(self):
        self.assertEqual(price_cart(CART, "vip", "BULK"), 1875)

    def test_welcome_same_for_both_tiers(self):
        self.assertEqual(price_cart(CART, "standard", "WELCOME"), 2375)


if __name__ == "__main__":
    unittest.main()
PY

cat > run_tests.sh <<'SH'
#!/usr/bin/env bash
exec python3 -m unittest discover -s tests -t . -v
SH
chmod +x run_tests.sh
