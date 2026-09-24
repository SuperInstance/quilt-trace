"""
quilt-trace — visualize any substrate walker's witness chain.

Per the substrate walker pattern: 199 LOC wrapper + 130 LOC tests + 50 LOC demo.
"""
from .reader import read_receipts, ReceiptStream
from .aggregator import aggregate, AggregateStats
from .renderer import render_html, render_receipts

__all__ = [
    "read_receipts", "ReceiptStream",
    "aggregate", "AggregateStats",
    "render_html", "render_receipts",
]

__version__ = "0.1.0"


def main():
    """Console entry point — quilt-trace SOURCE."""
    from quilt_trace.__main__ import main as _main
    _main()
