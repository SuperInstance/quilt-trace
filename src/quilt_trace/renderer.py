"""
renderer.py — render receipts to a self-contained HTML page with D3.js graph.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Iterable

from .aggregator import aggregate, AggregateStats


# D3.js inline (no external CDN — must work offline)
_D3_JS = "https://d3js.org/d3.v7.min.js"

_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  :root {{
    --bg: #0a0e14;
    --panel: #131820;
    --border: #1f2733;
    --text: #c5cdd9;
    --muted: #6c7a8c;
    --accept: #4ade80;
    --drift: #fbbf24;
    --refuse: #f87171;
    --accent: #818cf8;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    margin: 0; padding: 24px; line-height: 1.5;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  header {{
    display: flex; justify-content: space-between; align-items: baseline;
    border-bottom: 1px solid var(--border); padding-bottom: 16px; margin-bottom: 24px;
  }}
  h1 {{ margin: 0; font-size: 28px; font-weight: 500; color: var(--accent); }}
  .chain-head {{ font-family: monospace; font-size: 13px; color: var(--muted); }}
  .panel {{
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 8px; padding: 20px; margin-bottom: 20px;
  }}
  .panel h2 {{ margin: 0 0 16px 0; font-size: 14px; font-weight: 500;
              color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
  .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }}
  .stat {{ text-align: center; }}
  .stat-value {{ font-size: 32px; font-weight: 600; }}
  .stat-label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; }}
  .bar {{ display: flex; align-items: center; margin: 6px 0; font-size: 13px; }}
  .bar-label {{ width: 130px; font-family: monospace; }}
  .bar-track {{ flex: 1; height: 18px; background: var(--bg); border-radius: 2px;
                overflow: hidden; position: relative; }}
  .bar-fill {{ height: 100%; background: var(--accent); transition: width 0.3s; }}
  .bar-fill.accept {{ background: var(--accept); }}
  .bar-fill.drift {{ background: var(--drift); }}
  .bar-fill.refuse {{ background: var(--refuse); }}
  .bar-value {{ width: 50px; text-align: right; font-family: monospace; color: var(--muted); }}
  .graph {{ height: 480px; background: var(--bg); border-radius: 4px; position: relative; }}
  .graph svg {{ width: 100%; height: 100%; }}
  .legend {{ display: flex; gap: 16px; margin-top: 12px; font-size: 12px;
            color: var(--muted); justify-content: center; }}
  .legend-dot {{ display: inline-block; width: 10px; height: 10px;
                 border-radius: 50%; vertical-align: middle; margin-right: 4px; }}
  .intact {{ color: var(--accept); }}
  .broken {{ color: var(--refuse); }}
  footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border);
            color: var(--muted); font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>🌱 {title}</h1>
    <div class="chain-head">chain head: {chain_head_short}</div>
  </header>

  <div class="panel">
    <h2>Overview</h2>
    <div class="stats">
      <div class="stat">
        <div class="stat-value">{total}</div>
        <div class="stat-label">receipts</div>
      </div>
      <div class="stat">
        <div class="stat-value">{unique_cells}</div>
        <div class="stat-label">cells</div>
      </div>
      <div class="stat">
        <div class="stat-value">{unique_substrates}</div>
        <div class="stat-label">substrates</div>
      </div>
      <div class="stat">
        <div class="stat-value {intact_class}">{intact_label}</div>
        <div class="stat-label">chain</div>
      </div>
    </div>
  </div>

  <div class="panel">
    <h2>Polarity</h2>
    {polarity_bars}
  </div>

  <div class="panel">
    <h2>Substrates</h2>
    {substrate_bars}
  </div>

  <div class="panel">
    <h2>Top Cells</h2>
    {top_cells_bars}
  </div>

  <div class="panel">
    <h2>Witness Chain</h2>
    <div class="graph" id="graph"></div>
    <div class="legend">
      <span><span class="legend-dot" style="background: var(--accept)"></span>ACCEPT</span>
      <span><span class="legend-dot" style="background: var(--drift)"></span>DRIFT</span>
      <span><span class="legend-dot" style="background: var(--refuse)"></span>REFUSE</span>
    </div>
  </div>

  <footer>
    quilt-trace v0.1.0 · the organism sees itself · {generated_at}
  </footer>
</div>

<script src="{d3_url}"></script>
<script>
const data = {graph_data};
const container = document.getElementById('graph');
const width = container.clientWidth;
const height = container.clientHeight;

const svg = d3.select('#graph').append('svg')
  .attr('viewBox', [0, 0, width, height]);

const colorMap = {{
  ACCEPT: '#4ade80', DRIFT: '#fbbf24', REFUSE: '#f87171'
}};

const link = svg.append('g')
  .attr('stroke', '#3a4554')
  .attr('stroke-opacity', 0.5)
  .selectAll('line')
  .data(data.links)
  .join('line')
  .attr('stroke-width', 1);

const node = svg.append('g')
  .selectAll('circle')
  .data(data.nodes)
  .join('circle')
  .attr('r', 5)
  .attr('fill', d => colorMap[d.polarity] || '#818cf8')
  .attr('stroke', '#1f2733')
  .attr('stroke-width', 1.5)
  .call(d3.drag()
    .on('start', (event, d) => {{
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
    }})
    .on('drag', (event, d) => {{
      d.fx = event.x; d.fy = event.y;
    }})
    .on('end', (event, d) => {{
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null; d.fy = null;
    }}));

node.append('title').text(d => d.label);

const simulation = d3.forceSimulation(data.nodes)
  .force('link', d3.forceLink(data.links).id(d => d.id).distance(40).strength(0.7))
  .force('charge', d3.forceManyBody().strength(-80))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .on('tick', () => {{
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    node.attr('cx', d => d.x).attr('cy', d => d.y);
  }});
</script>
</body>
</html>
"""


def _bars_html(items: list, max_value: int, klass: str = "") -> str:
    if not items:
        return "<div style='color: var(--muted);'>no data</div>"
    out = []
    for label, value in items:
        pct = (value / max_value * 100) if max_value > 0 else 0
        klass_attr = f' class="{klass}"' if klass else ""
        out.append(
            f'<div class="bar">'
            f'<div class="bar-label">{html.escape(str(label))}</div>'
            f'<div class="bar-track"><div class="bar-fill{klass_attr}" style="width: {pct:.1f}%"></div></div>'
            f'<div class="bar-value">{value}</div>'
            f'</div>'
        )
    return "\n".join(out)


def _polarity_bars_html(stats: AggregateStats) -> str:
    items = list(stats.by_polarity.items())
    items.sort(key=lambda x: -x[1])
    max_v = max((v for _, v in items), default=1)
    out = []
    for label, value in items:
        pct = (value / max_v * 100) if max_v > 0 else 0
        klass = label.lower() if label.lower() in ("accept", "drift", "refuse") else ""
        out.append(
            f'<div class="bar">'
            f'<div class="bar-label">{label}</div>'
            f'<div class="bar-track"><div class="bar-fill {klass}" style="width: {pct:.1f}%"></div></div>'
            f'<div class="bar-value">{value}</div>'
            f'</div>'
        )
    return "\n".join(out)


def _build_graph_data(receipts: list) -> dict:
    """Build the D3.js graph data (nodes + links)."""
    nodes = []
    links = []
    seen = set()
    for r in receipts:
        wid = r.get("witness_id", "")
        if not wid or wid in seen:
            continue
        seen.add(wid)
        label = f'{r.get("cell_id", "?")[:20]} ({r.get("substrate", "?")[:12]})'
        nodes.append({
            "id": wid,
            "polarity": r.get("polarity", "DRIFT"),
            "label": label,
        })
        prev = r.get("prev_witness_id", "")
        if prev:
            links.append({"source": prev, "target": wid})
    return {"nodes": nodes, "links": links}


def render_html(receipts: Iterable[dict], title: str = "The Organism",
                d3_url: str = _D3_JS) -> str:
    """Render receipts to a self-contained HTML page."""
    receipts = list(receipts)
    stats = aggregate(receipts)
    graph_data = _build_graph_data(receipts)

    if not stats.chain_intact:
        intact_class = "broken"
        intact_label = f"broken ({len(stats.broken_links)})"
    else:
        intact_class = "intact"
        intact_label = "intact"

    polarity_bars = _polarity_bars_html(stats)
    substrate_bars = _bars_html(list(stats.by_substrate.items()), max(stats.by_substrate.values(), default=1))
    top_cells_bars = _bars_html(stats.top_cells, max((v for _, v in stats.top_cells), default=1))

    return _TEMPLATE.format(
        title=html.escape(title),
        chain_head_short=html.escape(stats.chain_head[:16] + "...") if stats.chain_head else "(none)",
        total=stats.total,
        unique_cells=len(set(r.get("cell_id") for r in receipts if r.get("cell_id"))),
        unique_substrates=len(stats.by_substrate),
        intact_class=intact_class,
        intact_label=intact_label,
        polarity_bars=polarity_bars,
        substrate_bars=substrate_bars,
        top_cells_bars=top_cells_bars,
        graph_data=json.dumps(graph_data),
        d3_url=d3_url,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
    )


def render_receipts(receipts: Iterable[dict], title: str = "The Organism") -> str:
    """Shorthand for render_html."""
    return render_html(receipts, title=title)
