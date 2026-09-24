"""Tests for quilt-trace."""
import sys, os, json, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from quilt_trace import read_receipts, aggregate, render_html, render_receipts
from quilt_trace.aggregator import AggregateStats


SAMPLE_RECEIPTS = [
    {"witness_id": "a", "prev_witness_id": "", "polarity": "ACCEPT",
     "substrate": "cuopt-lp", "cell_id": "production", "status": "Optimal",
     "timestamp": 100},
    {"witness_id": "b", "prev_witness_id": "a", "polarity": "ACCEPT",
     "substrate": "cuopt-routing", "cell_id": "fleet", "status": "Optimal",
     "timestamp": 200},
    {"witness_id": "c", "prev_witness_id": "b", "polarity": "DRIFT",
     "substrate": "vibe", "cell_id": "drifter", "status": "TimeLimit",
     "timestamp": 300},
    {"witness_id": "d", "prev_witness_id": "c", "polarity": "REFUSE",
     "substrate": "jev", "cell_id": "oracle", "status": "Infeasible",
     "timestamp": 400},
]


class TestReader(unittest.TestCase):
    def test_read_from_list(self):
        receipts = list(read_receipts(SAMPLE_RECEIPTS))
        self.assertEqual(len(receipts), 4)
        self.assertEqual(receipts[0]["witness_id"], "a")

    def test_read_from_jsonl_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for r in SAMPLE_RECEIPTS:
                f.write(json.dumps(r) + "\n")
            path = f.name
        try:
            receipts = list(read_receipts(path))
            self.assertEqual(len(receipts), 4)
            self.assertEqual(receipts[2]["polarity"], "DRIFT")
        finally:
            os.unlink(path)

    def test_read_skips_empty_lines(self):
        receipts = list(read_receipts(["", SAMPLE_RECEIPTS[0], "", SAMPLE_RECEIPTS[1]]))
        self.assertEqual(len(receipts), 2)

    def test_read_skips_invalid_json(self):
        receipts = list(read_receipts(["not json", SAMPLE_RECEIPTS[0]]))
        self.assertEqual(len(receipts), 1)


class TestAggregator(unittest.TestCase):
    def test_aggregate_total(self):
        stats = aggregate(SAMPLE_RECEIPTS)
        self.assertEqual(stats.total, 4)

    def test_aggregate_polarity(self):
        stats = aggregate(SAMPLE_RECEIPTS)
        self.assertEqual(stats.by_polarity["ACCEPT"], 2)
        self.assertEqual(stats.by_polarity["DRIFT"], 1)
        self.assertEqual(stats.by_polarity["REFUSE"], 1)

    def test_aggregate_substrates(self):
        stats = aggregate(SAMPLE_RECEIPTS)
        self.assertEqual(stats.by_substrate["cuopt-lp"], 1)
        self.assertEqual(stats.by_substrate["cuopt-routing"], 1)
        self.assertEqual(stats.by_substrate["vibe"], 1)
        self.assertEqual(stats.by_substrate["jev"], 1)

    def test_aggregate_chain_head(self):
        stats = aggregate(SAMPLE_RECEIPTS)
        # chain head is the receipt whose witness_id is not anyone's prev
        self.assertEqual(stats.chain_head, "d")

    def test_aggregate_chain_intact(self):
        stats = aggregate(SAMPLE_RECEIPTS)
        self.assertTrue(stats.chain_intact)
        self.assertEqual(len(stats.broken_links), 0)

    def test_aggregate_detects_broken_chain(self):
        receipts = [
            {"witness_id": "x", "prev_witness_id": "", "polarity": "ACCEPT",
             "substrate": "s", "cell_id": "c", "status": "ok"},
            {"witness_id": "y", "prev_witness_id": "missing", "polarity": "DRIFT",
             "substrate": "s", "cell_id": "c", "status": "drift"},
        ]
        stats = aggregate(receipts)
        self.assertFalse(stats.chain_intact)
        self.assertIn("y", stats.broken_links)

    def test_aggregate_top_cells(self):
        # Add multiple receipts for one cell
        receipts = list(SAMPLE_RECEIPTS) + [
            {"witness_id": "e", "prev_witness_id": "d", "polarity": "ACCEPT",
             "substrate": "cu", "cell_id": "production", "status": "ok"},
        ]
        stats = aggregate(receipts)
        self.assertEqual(stats.top_cells[0], ("production", 2))

    def test_aggregate_timestamp_range(self):
        stats = aggregate(SAMPLE_RECEIPTS)
        self.assertEqual(stats.timestamp_range, (100, 400))

    def test_aggregate_empty(self):
        stats = aggregate([])
        self.assertEqual(stats.total, 0)
        self.assertEqual(stats.chain_head, "")
        self.assertTrue(stats.chain_intact)


class TestRenderer(unittest.TestCase):
    def test_render_html_contains_title(self):
        html = render_html(SAMPLE_RECEIPTS, title="Test Organism")
        self.assertIn("Test Organism", html)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("d3", html.lower())  # d3.js reference

    def test_render_html_contains_polarity(self):
        html = render_html(SAMPLE_RECEIPTS)
        self.assertIn("ACCEPT", html)
        self.assertIn("DRIFT", html)
        self.assertIn("REFUSE", html)

    def test_render_html_contains_substrates(self):
        html = render_html(SAMPLE_RECEIPTS)
        self.assertIn("cuopt-lp", html)
        self.assertIn("cuopt-routing", html)

    def test_render_html_chain_intact(self):
        html = render_html(SAMPLE_RECEIPTS)
        self.assertIn("intact", html.lower())

    def test_render_html_escapes_title(self):
        html = render_html(SAMPLE_RECEIPTS, title="<script>alert(1)</script>")
        # XSS attempt should be escaped
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_render_html_with_broken_chain(self):
        receipts = [
            {"witness_id": "x", "prev_witness_id": "missing", "polarity": "ACCEPT",
             "substrate": "s", "cell_id": "c", "status": "ok"},
        ]
        html = render_html(receipts)
        self.assertIn("broken", html.lower())

    def test_render_html_with_empty_receipts(self):
        html = render_html([])
        self.assertIn("<!DOCTYPE html>", html)
        # Should not error
        self.assertIn("0", html)  # 0 receipts shown

    def test_render_receipts_shorthand(self):
        html = render_receipts(SAMPLE_RECEIPTS)
        self.assertIn("<!DOCTYPE html>", html)


class TestIntegration(unittest.TestCase):
    """End-to-end: real-shaped receipts from quilt-organism."""

    def test_organism_receipt_shape(self):
        # Mimics quilt_organism.OrganismReceipt shape
        receipts = [
            {"witness_id": "abc", "prev_witness_id": "", "polarity": "ACCEPT",
             "substrate": "VectorizeReceiver", "cell_id": "essay-1",
             "status": "vectorized", "payload": {"dim": 768},
             "timestamp": 1000},
            {"witness_id": "def", "prev_witness_id": "abc", "polarity": "ACCEPT",
             "substrate": "CanonScoreReceiver", "cell_id": "essay-1",
             "status": "canonical", "payload": {"canon_score": 0.86},
             "timestamp": 1100},
        ]
        stats = aggregate(receipts)
        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.by_substrate["VectorizeReceiver"], 1)
        html = render_html(receipts)
        self.assertIn("VectorizeReceiver", html)
        self.assertIn("CanonScoreReceiver", html)


if __name__ == "__main__":
    unittest.main()
