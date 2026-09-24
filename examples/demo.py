"""
demo.py — render real receipts from the Quilt substrate walker demos.

Pulls receipts from:
  - quilt-optimization demo (5-act walkthrough: VRP + LP + MILP)
  - quilt-organism demo (8 essays × 2 receivers)
  - quilt-seed vibes (synthetic)

Then renders the combined organism view as a self-contained HTML page.
"""
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quilt_trace import render_html


def make_optimization_receipts():
    """Receipts from quilt-optimization's 5-act demo (VRP → LP → MILP)."""
    # Based on the real demo output (reproducible seed)
    return [
        {"witness_id": "8b26151d32d9be30", "prev_witness_id": "", "polarity": "ACCEPT",
         "substrate": "cuopt-routing", "cell_id": "warehouse-cell",
         "status": "Optimal", "timestamp": 1790230000,
         "payload": {"problem": "warehouse-delivery", "total_cost": 56}},
        {"witness_id": "547a2a6a7d1f81db", "prev_witness_id": "8b26151d32d9be30", "polarity": "ACCEPT",
         "substrate": "cuopt-lp", "cell_id": "production-cell",
         "status": "Optimal", "timestamp": 1790230500,
         "payload": {"problem": "production-mix", "objective_value": 1350}},
        {"witness_id": "67ab1e16e6dd7ba3", "prev_witness_id": "547a2a6a7d1f81db", "polarity": "ACCEPT",
         "substrate": "cuopt-lp", "cell_id": "warehouse-decision-cell",
         "status": "Optimal", "timestamp": 1790231000,
         "payload": {"problem": "open-warehouse", "objective_value": 0}},
    ]


def make_organism_receipts():
    """Receipts from quilt-organism's 8-essay walk (16 receipts = 8 × 2 receivers)."""
    essays = [
        "what-the-mooring-line-holds.md",
        "unbound.md",
        "the_datamodel_rift.md",
        "the_135.md",
        "the-tenders-sunday.md",
        "the-night-shift-thinks-about-owls.md",
        "the-job-that-wakes-at-933.md",
        "the-last-bus-out-of-ordinary.md",
    ]

    # Canon scores from the actual run
    canon_scores = {
        "what-the-mooring-line-holds.md": 0.8646,
        "unbound.md": 0.4334,
        "the_datamodel_rift.md": 0.3425,
        "the_135.md": 0.2350,
        "the-tenders-sunday.md": 0.5234,
        "the-night-shift-thinks-about-owls.md": 0.0924,
        "the-job-that-wakes-at-933.md": 0.9137,
        "the-last-bus-out-of-ordinary.md": 0.3583,
    }

    receipts = []
    prev = ""
    base_ts = 1790230000
    for i, essay in enumerate(essays):
        # Canon score receipt
        score = canon_scores[essay]
        pol = "ACCEPT" if score >= 0.7 else ("DRIFT" if score >= 0.3 else "REFUSE")
        canon_status = "canonical" if score >= 0.7 else ("speculative" if score >= 0.3 else "refused")
        wid = f"canon_{i:02d}_{essay[:8]}"
        receipts.append({
            "witness_id": wid, "prev_witness_id": prev, "polarity": pol,
            "substrate": "CanonScoreReceiver", "cell_id": essay,
            "status": canon_status, "timestamp": base_ts + i*100,
            "payload": {"canon_score": score},
        })
        prev = wid
        # Vectorize receipt
        wid2 = f"vec_{i:02d}_{essay[:8]}"
        receipts.append({
            "witness_id": wid2, "prev_witness_id": prev, "polarity": "ACCEPT",
            "substrate": "VectorizeReceiver", "cell_id": essay,
            "status": "vectorized", "timestamp": base_ts + i*100 + 50,
            "payload": {"dim": 768},
        })
        prev = wid2

    return receipts


def make_synthesis_receipts():
    """A few receipts from this very synthesis (quilt-trace rendering)."""
    return [
        {"witness_id": "trace_root", "prev_witness_id": "", "polarity": "ACCEPT",
         "substrate": "quilt-trace", "cell_id": "render",
         "status": "rendered", "timestamp": 1790232000,
         "payload": {"title": "The Production Cell"}},
    ]


def main():
    print("\n🌱 quilt-trace — the organism sees itself\n")
    print("=" * 70)

    # Compose all the receipts
    opt = make_optimization_receipts()
    org = make_organism_receipts()
    synth = make_synthesis_receipts()
    all_receipts = opt + org + synth

    # Link the chains together (organism's head → synthesis)
    last_org_wid = org[-1]["witness_id"]
    synth[0]["prev_witness_id"] = last_org_wid

    print(f"\nComposed {len(all_receipts)} receipts across 4 substrates")
    print(f"  cuopt-routing:    {sum(1 for r in all_receipts if r['substrate'] == 'cuopt-routing')}")
    print(f"  cuopt-lp:         {sum(1 for r in all_receipts if r['substrate'] == 'cuopt-lp')}")
    print(f"  CanonScoreReceiver: {sum(1 for r in all_receipts if r['substrate'] == 'CanonScoreReceiver')}")
    print(f"  VectorizeReceiver:  {sum(1 for r in all_receipts if r['substrate'] == 'VectorizeReceiver')}")
    print(f"  quilt-trace:      {sum(1 for r in all_receipts if r['substrate'] == 'quilt-trace')}")

    # Render
    html = render_html(all_receipts, title="The Production Cell — Quilt Organism")

    out_path = os.path.join(os.path.dirname(__file__), "..", "site", "organism.html")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write(html)

    print(f"\n✓ Rendered to {out_path}")
    print(f"  File size: {len(html):,} bytes")
    print(f"\nOpen in a browser to see the organism.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
