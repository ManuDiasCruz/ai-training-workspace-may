"""Generate a representative sample shopping dataset.

The dataset mirrors the column shape of the popular "Customer Shopping
Trends" dataset that the task references. The real CSV from Google Drive
was not reachable from this sandboxed environment (drive.google.com is
not on the network allowlist), so this script produces a deterministic
sample that the API can be developed and tested against. Drop a real
CSV with matching columns into data/shopping.csv to replace it.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "shopping.csv"

CATEGORIES = {
    "Clothing": ["T-Shirt", "Sweater", "Jeans", "Shorts", "Dress", "Coat", "Blouse", "Pants", "Hoodie", "Skirt"],
    "Footwear": ["Sneakers", "Boots", "Sandals", "Loafers"],
    "Accessories": ["Hat", "Belt", "Scarf", "Gloves", "Sunglasses", "Handbag", "Backpack", "Jewelry"],
    "Outerwear": ["Jacket", "Raincoat", "Parka"],
}
LOCATIONS = [
    "California", "Texas", "New York", "Florida", "Illinois", "Pennsylvania",
    "Ohio", "Georgia", "North Carolina", "Michigan", "Washington", "Oregon",
    "Arizona", "Massachusetts", "Colorado",
]
SIZES = ["XS", "S", "M", "L", "XL"]
COLORS = ["Red", "Blue", "Green", "Black", "White", "Yellow", "Purple", "Pink", "Gray", "Brown", "Orange"]
SEASONS = ["Spring", "Summer", "Fall", "Winter"]
PAYMENTS = ["Credit Card", "Debit Card", "PayPal", "Cash", "Venmo", "Bank Transfer"]
SHIPPING = ["Standard", "Express", "Free Shipping", "Next Day Air", "2-Day Shipping", "Store Pickup"]
FREQUENCY = ["Weekly", "Bi-Weekly", "Monthly", "Quarterly", "Annually", "Every 3 Months"]
GENDERS = ["Male", "Female"]

HEADER = [
    "customer_id", "age", "gender", "item_purchased", "category",
    "purchase_amount_usd", "location", "size", "color", "season",
    "review_rating", "subscription_status", "payment_method",
    "shipping_type", "discount_applied", "promo_code_used",
    "previous_purchases", "frequency_of_purchases",
]


def generate(n: int = 1000, seed: int = 42) -> None:
    rng = random.Random(seed)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for i in range(1, n + 1):
            category = rng.choice(list(CATEGORIES.keys()))
            item = rng.choice(CATEGORIES[category])
            discount = rng.random() < 0.35
            w.writerow([
                i,
                rng.randint(18, 75),
                rng.choice(GENDERS),
                item,
                category,
                round(rng.uniform(20, 200), 2),
                rng.choice(LOCATIONS),
                rng.choice(SIZES),
                rng.choice(COLORS),
                rng.choice(SEASONS),
                round(rng.uniform(2.5, 5.0), 1),
                "Yes" if rng.random() < 0.4 else "No",
                rng.choice(PAYMENTS),
                rng.choice(SHIPPING),
                "Yes" if discount else "No",
                "Yes" if discount and rng.random() < 0.7 else "No",
                rng.randint(0, 50),
                rng.choice(FREQUENCY),
            ])
    print(f"Wrote {n} rows to {OUT}")


if __name__ == "__main__":
    generate()
