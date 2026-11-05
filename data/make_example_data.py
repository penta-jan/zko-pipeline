#!/usr/bin/env python3
"""Generate a synthetic block-level data set that mimics a QGIS export.

The real project joined Berlin's public block data (Umweltatlas / Energieatlas)
with the boundary polygons of eleven sites. Those results are not public, so this
script produces fictitious but plausible data with the same structure.

Output: data/blocks.csv  (one row per city block)
"""
import csv
import math
import random
from pathlib import Path

random.seed(2025)  # reproducible

# id, name, number of blocks, buildings per hectare,
# then per carrier: (probability block uses it, probability value is reported, mean MWh)
SITES = [
    ("a", "North Campus",    24,  7.5, (0.90, 0.55, 1500), (0.40, 0.50,  900), (0.80, 0.60, 2500)),
    ("b", "Riverside Works", 18,  1.6, (0.85, 0.50, 3000), (0.90, 0.55, 4000), (0.20, 0.50, 1500)),
    ("c", "Old Airfield",    10,  0.8, (0.60, 0.30,  800), (0.50, 0.30, 1200), (0.40, 0.00, 2000)),
    ("d", "Science Park",    30,  4.5, (0.90, 0.60, 2000), (0.60, 0.50, 1500), (0.60, 0.60, 1800)),
    ("e", "Inner Quarter",    8, 14.0, (0.95, 0.70, 1200), (0.50, 0.60,  700), (0.90, 0.70, 1600)),
]
CARRIERS = ("el", "gas", "heat")


def lognormal(mean, sigma=0.8):
    """Log-normal draw with the given arithmetic mean."""
    mu = math.log(mean) - sigma ** 2 / 2
    return random.lognormvariate(mu, sigma)


def main():
    out = Path(__file__).with_name("blocks.csv")
    fields = ["block-id", "site", "relation", "area-ha", "buildings"]
    for c in CARRIERS:
        fields += [f"{c}-status", f"{c}-mwh"]

    rows = []
    for sid, _name, n, density, *carriers in SITES:
        for k in range(1, n + 1):
            area = round(random.uniform(1.0, 6.0), 2)
            row = {
                "block-id": f"{sid}{k:03d}",
                "site": sid,
                # QGIS selection: block lies within the polygon or only intersects it
                "relation": "within" if random.random() < 0.75 else "intersects",
                "area-ha": area,
                "buildings": max(0, round(random.gauss(density * area, density * area * 0.3))),
            }
            for c, (p_use, p_rep, mean) in zip(CARRIERS, carriers):
                if random.random() >= p_use:
                    row[f"{c}-status"], row[f"{c}-mwh"] = "none", ""
                elif random.random() < p_rep:
                    row[f"{c}-status"], row[f"{c}-mwh"] = "reported", round(lognormal(mean), 1)
                else:
                    # consumption exists but is withheld (e.g. data protection)
                    row[f"{c}-status"], row[f"{c}-mwh"] = "suppressed", ""
            rows.append(row)

    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} blocks to {out}")


if __name__ == "__main__":
    main()
