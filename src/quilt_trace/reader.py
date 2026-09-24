"""
reader.py — read receipts from any source (JSONL file, in-memory list, dict).
"""
from __future__ import annotations

import json
from typing import Iterator


def read_receipts(source) -> Iterator[dict]:
    """Yield normalized receipts from various sources.

    Source can be:
      - A file path (str or Path) to a JSONL file
      - An iterable of dicts
      - A single dict
    """
    if isinstance(source, (str, bytes)):
        # File path
        if isinstance(source, bytes):
            source = source.decode("utf-8")
        with open(source) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    elif hasattr(source, "__iter__"):
        # Iterable
        for item in source:
            if isinstance(item, dict):
                yield item
            elif isinstance(item, str):
                try:
                    yield json.loads(item)
                except json.JSONDecodeError:
                    continue


class ReceiptStream:
    """A streaming wrapper over read_receipts for memory-efficient processing."""

    def __init__(self, source):
        self._source = source

    def __iter__(self):
        return read_receipts(self._source)

    def to_list(self) -> list[dict]:
        return list(self)
