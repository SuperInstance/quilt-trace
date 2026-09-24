"""CLI: quilt-trace SOURCE [--out FILE] [--title TITLE]"""
import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from quilt_trace import read_receipts, render_html


def main():
    p = argparse.ArgumentParser(description="Render receipts to HTML")
    p.add_argument("source", help="JSONL file with receipts (one per line)")
    p.add_argument("--out", default="organism.html", help="output HTML file")
    p.add_argument("--title", default="The Organism", help="page title")
    args = p.parse_args()

    receipts = list(read_receipts(args.source))
    html = render_html(receipts, title=args.title)
    with open(args.out, "w") as f:
        f.write(html)
    print(f"✓ Rendered {len(receipts)} receipts → {args.out} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
