"""
aggregator.py — aggregate receipts into stats the renderer uses.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class AggregateStats:
    """The organism's view of itself — one snapshot of all receipts."""
    total: int = 0
    by_polarity: dict = field(default_factory=lambda: {"ACCEPT": 0, "DRIFT": 0, "REFUSE": 0})
    by_substrate: dict = field(default_factory=dict)
    by_status: dict = field(default_factory=dict)
    top_cells: list = field(default_factory=list)
    chain_head: str = ""
    chain_intact: bool = True
    broken_links: list = field(default_factory=list)
    timestamp_range: tuple = (None, None)


def aggregate(receipts: Iterable[dict]) -> AggregateStats:
    """Compute aggregate stats from a receipt stream."""
    stats = AggregateStats()
    receipts = list(receipts)
    stats.total = len(receipts)
    if not receipts:
        return stats

    cell_counts = Counter()
    prev_to_curr = {}  # prev_witness_id -> set of witness_ids that link to it
    by_id = {}  # witness_id -> receipt

    for r in receipts:
        # Polarity
        pol = r.get("polarity", "DRIFT").upper()
        if pol not in stats.by_polarity:
            stats.by_polarity[pol] = 0
        stats.by_polarity[pol] += 1

        # Substrate
        sub = r.get("substrate", "unknown")
        stats.by_substrate[sub] = stats.by_substrate.get(sub, 0) + 1

        # Status
        st = r.get("status", "unknown")
        stats.by_status[st] = stats.by_status.get(st, 0) + 1

        # Cell counts
        cell = r.get("cell_id", "?")
        cell_counts[cell] += 1

        # Chain links
        wid = r.get("witness_id", "")
        prev = r.get("prev_witness_id", "")
        if wid:
            by_id[wid] = r
        if prev:
            prev_to_curr.setdefault(prev, set()).add(wid)

    # Top cells
    stats.top_cells = cell_counts.most_common(10)

    # Chain head — the receipt whose witness_id is not anyone's prev
    all_wids = set(by_id.keys())
    all_prevs = set()
    for r in receipts:
        prev = r.get("prev_witness_id", "")
        if prev:
            all_prevs.add(prev)
    heads = all_wids - all_prevs
    stats.chain_head = sorted(heads)[0] if heads else ""

    # Chain integrity — each receipt's prev should exist
    # (intact means the chain is well-formed; we check that no broken links exist)
    stats.broken_links = []
    for r in receipts:
        prev = r.get("prev_witness_id", "")
        if prev and prev not in by_id:
            stats.broken_links.append(r.get("witness_id", "?"))
    stats.chain_intact = len(stats.broken_links) == 0

    # Timestamp range
    timestamps = [r.get("timestamp", 0) for r in receipts if r.get("timestamp")]
    if timestamps:
        stats.timestamp_range = (min(timestamps), max(timestamps))

    return stats
