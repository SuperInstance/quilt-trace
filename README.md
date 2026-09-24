# 🌱 quilt-trace

> The organism's eyes — visualize any substrate walker's witness chain.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](tests/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## What is this?

`quilt-trace` reads receipts from **any** substrate walker (quilt-seed, quilt-optimization, quilt-organism, jev-quilt) and renders the witness chain as a self-contained HTML page. The organism sees itself.

```bash
python3 -m quilt_trace your_receipts.jsonl --out organism.html
# open organism.html in a browser
```

The landing page shows:

- **Chain head** — the latest witness_id in the chain
- **Polarity histogram** — ACCEPT / DRIFT / REFUSE bars
- **Substrate breakdown** — which substrates emitted how many receipts
- **Top items** — most-cited cells (by receipt count)
- **Witness chain** — the receipts as a force-directed graph (D3.js)

## Install

```bash
pip install quilt-trace
```

## Quickstart

```python
from quilt_trace import render_receipts

# Read receipts from any source
receipts = [
    {"witness_id": "abc...", "prev_witness_id": "", "polarity": "ACCEPT",
     "substrate": "cuopt-lp", "cell_id": "production-mix", "status": "Optimal"},
    {"witness_id": "def...", "prev_witness_id": "abc...", "polarity": "ACCEPT",
     "substrate": "cuopt-routing", "cell_id": "fleet-routes", "status": "Optimal"},
]

# Render the organism view
html = render_receipts(receipts, title="The Production Cell")
open("organism.html", "w").write(html)
```

## The receipt schema (canonical)

`quilt-trace` accepts any receipt with these fields:

```json
{
  "witness_id": "abc123...",        // sha256-of-canonical (or any unique id)
  "prev_witness_id": "def456...",   // chain link (empty = root)
  "polarity": "ACCEPT",             // or DRIFT | REFUSE
  "substrate": "cuopt-lp",          // which wrapper emitted this
  "cell_id": "production-mix",      // which item was observed
  "status": "Optimal",              // raw status (cuOpt PascalCase, etc.)
  "payload": {...},                 // optional
  "timestamp": 1790232629
}
```

This is the substrate-walker-compatible envelope — same shape as `CellReceipt` (quilt-seed), `OptimizationReceipt` (quilt-optimization), `OrganismReceipt` (quilt-organism).

## The landing page

Open `site/organism.html` (or any rendered output) in a browser. You'll see:

```
┌─────────────────────────────────────────────────────────┐
│  🌱 The Production Cell                                  │
│  Chain head: abc123... | Chain length: 47 | Intact: ✓   │
├─────────────────────────────────────────────────────────┤
│  ACCEPT  ████████████████████  35                      │
│  DRIFT   ██████              10                         │
│  REFUSE  ██                   2                         │
├─────────────────────────────────────────────────────────┤
│  Substrates                                              │
│  cuopt-lp        ████████████  18                       │
│  cuopt-routing   █████████     14                       │
│  jev             ████           6                       │
│  vibe            ████           5                       │
│  cu              ███            4                       │
├─────────────────────────────────────────────────────────┤
│  Witness chain (D3.js force-directed)                   │
│  ●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●                 │
└─────────────────────────────────────────────────────────┘
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover tests -v
```

## Related

- [quilt-organism](https://github.com/SuperInstance/quilt-organism) — emits receipts that this visualizes
- [quilt-seed](https://github.com/SuperInstance/quilt-seed) — CellReceipt envelope
- [quilt-optimization](https://github.com/SuperInstance/quilt-optimization) — OptimizationReceipt
- [jev-quilt](https://github.com/SuperInstance/jev-quilt) — JEV oracle receipts (483+ JSON sessions)

## License

Apache-2.0
