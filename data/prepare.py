#!/usr/bin/env python3
"""Aggregate block data to one row per site (replaces the spreadsheet step).

Input : data/blocks.csv      (block level, as exported from QGIS)
Output: data/sites.csv       (site level, read by LaTeX/datatool)
        data/dictionary.csv  (description, unit and source of every column)

Conventions
- decimal POINT and comma separator in all data files; locale formatting
  (e.g. decimal comma) happens only at output time, in LaTeX (siunitx).
- every derived quantity is computed here, with full precision.
"""
import csv
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent

SITE_NAMES = {
    "a": "North Campus", "b": "Riverside Works", "c": "Old Airfield",
    "d": "Science Park", "e": "Inner Quarter",
}
INCLUDE = {"within", "intersects"}   # selection rule, see documentation
TARGET_DENSITY = 10.0                # buildings per hectare at full build-out
# t CO2 per GWh, as used in the original project (state energy balance)
EMISSION_FACTORS = {"el": 365.22, "gas": 202.77, "heat": 219.65}
CARRIERS = {"el": "electricity", "gas": "natural gas", "heat": "district heating"}

DICTIONARY = [
    # column, description, unit, source
    ("id", "Short identifier of the site", "", "input"),
    ("name", "Name of the site", "", "input"),
    ("blocks", "Blocks assigned to the site (within or intersecting)", "count", "QGIS"),
    ("area-ha", "Total area of assigned blocks", "ha", "QGIS"),
    ("buildings", "Number of buildings", "count", "QGIS (ALKIS)"),
    ("density", "Buildings per hectare: buildings / area-ha", "1/ha", "computed"),
]
for c, label in CARRIERS.items():
    DICTIONARY += [
        (f"{c}-blocks", f"Blocks with {label} consumption", "count", "QGIS (Energieatlas)"),
        (f"{c}-reported", f"Blocks with a reported {label} value", "count", "QGIS (Energieatlas)"),
        (f"{c}-gwh-reported", f"Sum of reported {label} consumption", "GWh", "computed"),
        (f"{c}-gwh", f"Extrapolated {label} consumption: mean per reported block "
                     f"times {c}-blocks", "GWh", "computed"),
    ]
DICTIONARY += [
    ("total-gwh", "Extrapolated total supply: el-gwh + gas-gwh + heat-gwh", "GWh", "computed"),
    ("co2-t", "CO2 from total supply, using emission factors per carrier", "t", "computed"),
    ("factor-raw", "Target density / density (may be below 1)", "", "computed"),
    ("factor", "Build-out factor: max(1, factor-raw)", "", "computed"),
    ("total-gwh-future", "Total supply at full build-out: total-gwh times factor",
     "GWh", "computed"),
]


def main():
    blocks = defaultdict(list)
    with (HERE / "blocks.csv").open() as f:
        for row in csv.DictReader(f):
            if row["relation"] in INCLUDE:
                blocks[row["site"]].append(row)

    sites = []
    for sid, rows in blocks.items():
        s = {"id": sid, "name": SITE_NAMES[sid], "blocks": len(rows)}
        s["area-ha"] = sum(float(r["area-ha"]) for r in rows)
        s["buildings"] = sum(int(r["buildings"]) for r in rows)
        s["density"] = s["buildings"] / s["area-ha"]
        total = co2 = 0.0
        for c in CARRIERS:
            used = [r for r in rows if r[f"{c}-status"] != "none"]
            rep = [float(r[f"{c}-mwh"]) for r in used if r[f"{c}-status"] == "reported"]
            gwh_rep = sum(rep) / 1000
            # Extrapolation: mean of reported blocks times all blocks with consumption.
            # If nothing is reported, the estimate is 0 -- a known downward bias.
            gwh = gwh_rep / len(rep) * len(used) if rep else 0.0
            s.update({f"{c}-blocks": len(used), f"{c}-reported": len(rep),
                      f"{c}-gwh-reported": gwh_rep, f"{c}-gwh": gwh})
            total += gwh
            co2 += gwh * EMISSION_FACTORS[c]
        s["total-gwh"], s["co2-t"] = total, co2
        s["factor-raw"] = TARGET_DENSITY / s["density"]
        s["factor"] = max(1.0, s["factor-raw"])   # dense sites do not shrink
        s["total-gwh-future"] = total * s["factor"]
        sites.append(s)

    sites.sort(key=lambda s: s["total-gwh"], reverse=True)   # largest first
    cols = [d[0] for d in DICTIONARY]

    def fmt(v):  # full precision, decimal point, no thousands separator
        return f"{v:.6f}".rstrip("0").rstrip(".") if isinstance(v, float) else v

    with (HERE / "sites.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for s in sites:
            w.writerow([fmt(s[c]) for c in cols])
    with (HERE / "dictionary.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["column", "description", "unit", "source"])
        w.writerows(DICTIONARY)

    for s in sites:
        print(f"{s['id']}  {s['name']:16s} total {s['total-gwh']:8.2f} GWh  "
              f"density {s['density']:5.2f}  factor {s['factor']:5.2f}  "
              f"heat reported {s['heat-reported']}/{s['heat-blocks']}")


if __name__ == "__main__":
    main()
