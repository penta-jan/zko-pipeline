# zko-pipeline

A reproducible pipeline that turns public, block-level energy data into maps,
charts and in-text figures for reports and slide decks:

```
public data -> QGIS (spatial join) -> blocks.csv -> prepare.py -> sites.csv -> LaTeX/TikZ -> PDF
```

The documentation (`doku.tex` / `doku.pdf`) is itself the minimal working
example: every chart and every number in it is computed from the data files at
compile time. All data in this repository are **synthetic**; the pipeline was
originally developed for an internal study of eleven science and technology
sites in Berlin.

## Build

```sh
python3 data/make_example_data.py   # synthetic data/blocks.csv (skip with real data)
python3 data/prepare.py             # data/sites.csv and data/dictionary.csv
pdflatex doku.tex && pdflatex doku.tex
```

or simply `make`.

Requirements: Python 3.8+ (standard library only), a TeX distribution with
`tikz`, `datatool`, `siunitx`. Tested with TeX Live 2023 and pdflatex.

## Files

| File | Purpose |
|---|---|
| `data/make_example_data.py` | Generates synthetic block data in the format of the QGIS export |
| `data/prepare.py` | Aggregates per site, extrapolates withheld values, derives indicators, writes the data dictionary |
| `data/blocks.csv` | Block-level input (one row per city block) |
| `data/sites.csv` | Site-level data read by LaTeX |
| `data/dictionary.csv` | Description, unit and source of every column |
| `zkopipeline.sty` | Drawing and number macros (`\zkomap`, `\zkopies`, `\zkobars`, `\zkoshare`, `\zkogrowth`, ...) |
| `doku.tex` | Documentation and minimal working example |

## Design rules

1. Data flow in one direction; nothing that can be derived is typed by hand.
2. Machine format inside (decimal point, full precision), local format only on
   output (`siunitx`).
3. Shares, growth rates and ratios have separate, explicitly named macros.

See section "Lessons learned" in the documentation for the errors these rules
prevent.

## Licence

Code: MIT. Documentation: CC BY 4.0.
