#!/usr/bin/env python3
"""Generate a realistic, large e-commerce review dataset for testing reviewiq.

Models a big home-furnishing retailer (IKEA-style): a varied product catalog
across many categories, with reviews whose text carries real *themes* (assembly
difficulty, missing parts, shipping damage, value, sturdiness, comfort, quality)
so the Bedrock analysis has genuine signal to find.

A few products are deliberately given a strong negative skew on one theme, so the
report surfaces clear priority issues + an anomaly — makes the demo compelling.

Usage:
    python generate_reviews.py --count 1000 --out reviews_ikea
    python generate_reviews.py --count 5000 --out big --xlsx

Columns match the reviewiq pipeline exactly:
    product_id, product_name, rating, review_text, date, platform
"""

import argparse
import csv
import random
from datetime import date, timedelta

# ---- Product catalog (name, category) — IKEA-style Scandinavian names --------
CATALOG = [
    # Sofas
    ("KLIPPAN Loveseat", "Sofa"), ("EKTORP 3-Seat Sofa", "Sofa"),
    ("FRIHETEN Sleeper Sofa", "Sofa"), ("SÖDERHAMN Sectional", "Sofa"),
    ("VIMLE 3-Seat Sofa", "Sofa"), ("KIVIK Corner Sofa", "Sofa"),
    ("LANDSKRONA Armchair", "Sofa"), ("STOCKSUND Loveseat", "Sofa"),
    # Beds & mattresses
    ("MALM Bed Frame", "Bed"), ("HEMNES Bed Frame", "Bed"),
    ("BRIMNES Storage Bed", "Bed"), ("SONGESAND Bed Frame", "Bed"),
    ("TARVA Bed Frame", "Bed"), ("HÖVÅG Mattress", "Mattress"),
    ("HAUGESUND Mattress", "Mattress"), ("MORGEDAL Foam Mattress", "Mattress"),
    ("ÅSVANG Mattress", "Mattress"),
    # Desks & office
    ("BEKANT Desk", "Desk"), ("MICKE Desk", "Desk"), ("LINNMON Table Top", "Desk"),
    ("ALEX Desk", "Desk"), ("IDÅSEN Sit/Stand Desk", "Desk"),
    ("TROTTEN Desk", "Desk"), ("HELMER Drawer Unit", "Office Storage"),
    ("ALEX Drawer Unit", "Office Storage"),
    # Chairs
    ("MARKUS Office Chair", "Chair"), ("POÄNG Armchair", "Chair"),
    ("JÄRVFJÄLLET Office Chair", "Chair"), ("ADDE Chair", "Chair"),
    ("TOBIAS Chair", "Chair"), ("ODGER Chair", "Chair"),
    ("STEFAN Chair", "Chair"), ("LÅNGFJÄLL Office Chair", "Chair"),
    # Shelving & storage
    ("BILLY Bookcase", "Shelving"), ("KALLAX Shelf Unit", "Shelving"),
    ("IVAR Shelf Unit", "Shelving"), ("FJÄLLBO Shelf", "Shelving"),
    ("LACK Wall Shelf", "Shelving"), ("EKET Cabinet", "Storage"),
    ("BESTÅ Storage Combo", "Storage"), ("TROFAST Storage", "Storage"),
    # Wardrobes
    ("PAX Wardrobe", "Wardrobe"), ("BRIMNES Wardrobe", "Wardrobe"),
    ("HEMNES Wardrobe", "Wardrobe"), ("KLEPPSTAD Wardrobe", "Wardrobe"),
    # Lighting
    ("RANARP Work Lamp", "Lighting"), ("FADO Table Lamp", "Lighting"),
    ("HEKTAR Pendant Lamp", "Lighting"), ("TERTIAL Work Lamp", "Lighting"),
    ("FOTO Pendant Lamp", "Lighting"), ("NYMÅNE Floor Lamp", "Lighting"),
    # Rugs & textiles
    ("STOENSE Rug", "Rug"), ("VINDUM Rug", "Rug"), ("LOHALS Rug", "Rug"),
    ("GURLI Cushion Cover", "Textile"), ("FÄRGKLAR Bowl Set", "Kitchenware"),
    # Kitchen
    ("KNOXHULT Kitchen", "Kitchen"), ("RÅSKOG Utility Cart", "Kitchen"),
    ("VARIERA Box", "Kitchen"), ("IKEA 365+ Cookware Set", "Kitchenware"),
    ("VARDAGEN Frying Pan", "Kitchenware"), ("KONCIS Roasting Pan", "Kitchenware"),
    # Kids
    ("KURA Reversible Bed", "Kids"), ("FLISAT Table", "Kids"),
    ("TROFAST Frame", "Kids"), ("SUNDVIK Crib", "Kids"),
    # Bathroom
    ("GODMORGON Cabinet", "Bathroom"), ("LILLÅNGEN Sink Cabinet", "Bathroom"),
    ("HEMNES Bathroom Vanity", "Bathroom"),
    # Outdoor
    ("APPLARÖ Table", "Outdoor"), ("FALSTER Chair", "Outdoor"),
    ("TÄRNÖ Bistro Set", "Outdoor"),
    # Dining
    ("EKEDALEN Dining Table", "Dining"), ("NORDEN Gateleg Table", "Dining"),
    ("INGATORP Table", "Dining"), ("LISABO Table", "Dining"),
]

PLATFORMS = ["IKEA.com", "Trustpilot", "Google Reviews", "Amazon", "Reddit"]

# ---- Review themes: (sentiment, rating range, templates) ---------------------
# {p} = product name, {c} = category (lowercased)
THEMES = {
    "assembly_hard": (2, 3, [
        "Assembly was a nightmare — took me over three hours and the pre-drilled holes didn't line up.",
        "The instructions for this {c} were confusing, lots of unlabeled parts. Needed a second person.",
        "Spent an entire afternoon building this. Some cam locks wouldn't tighten properly.",
    ]),
    "missing_parts": (1, 2, [
        "Package arrived missing several screws and a cam lock. Had to wait a week for replacements.",
        "Two dowels were missing from the box, couldn't finish assembly until IKEA shipped more.",
        "Bag of hardware was incomplete — frustrating when you've set aside the whole day for it.",
    ]),
    "damaged_shipping": (1, 2, [
        "Arrived with a deep scratch and a dented corner, clearly damaged in transit.",
        "One of the panels was cracked right out of the box. Packaging was too thin for a {c} this size.",
        "The finish was chipped on delivery. Return process was a hassle.",
    ]),
    "great_value": (5, 5, [
        "Incredible value for the price — looks far more expensive than it is.",
        "You genuinely cannot beat this {c} for the money. Bought two.",
        "Amazing quality for such a low price. Would recommend to anyone furnishing on a budget.",
    ]),
    "sturdy": (4, 5, [
        "Surprisingly sturdy and solid, no wobble at all even after months of daily use.",
        "This {c} feels rock-solid. Much more robust than I expected at this price.",
        "Really well built — my kids climb on it and it hasn't budged.",
    ]),
    "wobbly": (2, 3, [
        "Feels flimsy and wobbles, the screws keep loosening no matter how often I tighten them.",
        "Wobbles side to side the moment you lean on it. Had to add brackets to the wall.",
        "Not very stable — this {c} shakes whenever you touch it.",
    ]),
    "comfortable": (5, 5, [
        "Extremely comfortable, we sit on it every single evening.",
        "So comfortable I nearly fall asleep in it. Best {c} we've owned.",
        "Perfect firmness and support, no back pain anymore.",
    ]),
    "uncomfortable": (1, 2, [
        "The cushions flattened within a few weeks, not comfortable at all anymore.",
        "Way too firm and the edges dig in. Regret buying this {c}.",
        "Sags in the middle after light use. Uncomfortable to sit on for long.",
    ]),
    "easy_assembly": (5, 5, [
        "Assembled in about 20 minutes, clear instructions and every part was labeled.",
        "Easiest flat-pack I've built — everything lined up on the first try.",
        "Genuinely simple to put together, even solo.",
    ]),
    "looks_great": (4, 5, [
        "Looks beautiful in our living room, exactly as pictured online.",
        "Gorgeous, minimalist design. This {c} ties the whole room together.",
        "Elegant and clean-looking, guests always compliment it.",
    ]),
    "poor_quality": (1, 2, [
        "Particleboard chipped at the edges within a month and the finish scratches if you look at it.",
        "Cheap feeling materials, the veneer is already peeling on this {c}.",
        "Fell apart faster than I expected. You get what you pay for.",
    ]),
    "durable": (5, 5, [
        "Three years in and still going strong, no complaints whatsoever.",
        "This {c} has survived two moves and still looks new.",
        "Built to last — daily use and it hasn't shown any wear.",
    ]),
    "broke_quickly": (1, 2, [
        "A drawer rail snapped after just a month of normal use.",
        "The leg cracked within weeks. Disappointed in this {c}.",
        "Broke almost immediately — the joints couldn't handle everyday use.",
    ]),
    "delivery_late": (2, 3, [
        "Delivery was two weeks late and customer service was unhelpful the whole time.",
        "Ordered a month ago, arrived way past the promised date. The {c} itself is fine though.",
        "Shipping took forever and tracking never updated.",
    ]),
    "color_mismatch": (3, 3, [
        "Color looked lighter in person than online — still okay, but not what I expected.",
        "The finish is a bit different from the photos. This {c} is fine otherwise.",
        "Slightly different shade than pictured, minor letdown.",
    ]),
}

# Themes weighted for a generally-positive-but-realistic mix.
THEME_WEIGHTS = {
    "great_value": 14, "sturdy": 10, "looks_great": 12, "easy_assembly": 10,
    "comfortable": 9, "durable": 8, "color_mismatch": 6,
    "assembly_hard": 7, "wobbly": 4, "poor_quality": 5, "delivery_late": 5,
    "missing_parts": 4, "damaged_shipping": 4, "uncomfortable": 4, "broke_quickly": 3,
}

# Deliberate defect signals: force a theme to dominate a specific product,
# so the report surfaces clear priority issues + an anomaly.
DEFECT_SKEW = {
    "BEKANT Desk": ("wobbly", 0.6),          # known wobble complaint
    "HÖVÅG Mattress": ("uncomfortable", 0.6),  # sags
    "EKTORP 3-Seat Sofa": ("missing_parts", 0.5),
    "MALM Bed Frame": ("assembly_hard", 0.5),
    "IKEA 365+ Cookware Set": ("poor_quality", 0.55),
}


def pick_theme(product_name):
    skew = DEFECT_SKEW.get(product_name)
    if skew and random.random() < skew[1]:
        return skew[0]
    themes, weights = zip(*THEME_WEIGHTS.items())
    return random.choices(themes, weights=weights, k=1)[0]


def make_row(rng_days):
    name, category = random.choice(CATALOG)
    theme = pick_theme(name)
    lo, hi, templates = THEMES[theme]
    rating = random.randint(lo, hi)
    text = random.choice(templates).format(p=name, c=category.lower())
    d = date.today() - timedelta(days=random.randint(0, rng_days))
    pid = "SKU-" + str(abs(hash(name)) % 100000).zfill(5)
    return {
        "product_id": pid,
        "product_name": name,
        "rating": rating,
        "review_text": text,
        "date": d.isoformat(),
        "platform": random.choice(PLATFORMS),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=1000, help="number of reviews")
    ap.add_argument("--out", default="reviews_ikea", help="output filename prefix")
    ap.add_argument("--days", type=int, default=30, help="spread dates over N days")
    ap.add_argument("--xlsx", action="store_true", help="also write an .xlsx file")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    random.seed(args.seed)
    rows = [make_row(args.days) for _ in range(args.count)]
    cols = ["product_id", "product_name", "rating", "review_text", "date", "platform"]

    csv_path = f"{args.out}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} reviews across {len({r['product_name'] for r in rows})} products → {csv_path}")

    if args.xlsx:
        try:
            from openpyxl import Workbook
        except ImportError:
            print("openpyxl not installed — skipping .xlsx (pip install openpyxl)")
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "reviews"
        ws.append(cols)
        for r in rows:
            ws.append([r[c] for c in cols])
        xlsx_path = f"{args.out}.xlsx"
        wb.save(xlsx_path)
        print(f"wrote {xlsx_path}")


if __name__ == "__main__":
    main()
