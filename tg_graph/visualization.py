import networkx as nx
import matplotlib.pyplot as plt
import math
import json
from typing import Dict, Tuple
from .utils import sanitize_text


def _adjust_label_positions(
    pos: Dict[str, tuple], min_dist: float = 0.05
) -> Dict[str, tuple]:
    """Return new positions shifted slightly to reduce label overlap."""
    new_pos: Dict[str, tuple] = {}
    for node, (x, y) in pos.items():
        nx_, ny_ = x, y
        # Shift label until it does not collide with already placed labels
        while any(
            ((nx_ - ox) ** 2 + (ny_ - oy) ** 2) ** 0.5 < min_dist
            for ox, oy in new_pos.values()
        ):
            ny_ += min_dist
        new_pos[node] = (nx_, ny_)
    return new_pos


def _cluster_layout(
    G: nx.Graph, weight: str = "weight"
) -> Tuple[Dict[str, tuple], Dict[str, int]]:
    """Return node positions and a mapping of node to cluster index."""
    try:
        communities = list(nx.algorithms.community.louvain_communities(G))
    except Exception:
        communities = [set(G.nodes())]
    if not communities:
        communities = [set(G.nodes())]

    pos: Dict[str, tuple] = {}
    cluster_map: Dict[str, int] = {}
    angle_step = 2 * math.pi / len(communities)
    # Spread clusters further apart to reduce overlap
    radius = 22.0
    for idx, community in enumerate(communities):
        sub = G.subgraph(community)
        # Pull nodes of the same cluster closer together
        sub_pos = nx.spring_layout(sub, k=1.0, seed=42, weight=weight)
        angle = angle_step * idx
        cx = radius * math.cos(angle)
        cy = radius * math.sin(angle)
        for node, (x, y) in sub_pos.items():
            pos[node] = (x + cx, y + cy)
            cluster_map[node] = idx
    return pos, cluster_map


def _edge_color(weight: float) -> str:
    """Return edge color from light to saturated depending on weight."""
    t = min(weight / 6.0, 1.0)
    light = (198, 219, 239)
    dark = (8, 48, 107)
    r = int(light[0] + t * (dark[0] - light[0]))
    g = int(light[1] + t * (dark[1] - light[1]))
    b = int(light[2] + t * (dark[2] - light[2]))
    return f"#{r:02x}{g:02x}{b:02x}"


def _edge_width(weight: float) -> float:
    """Return line width for a given interaction strength."""
    return 1.0 + weight * 1.5


def _edge_opacity(weight: float) -> float:
    """Return line opacity for a given interaction strength.

    The opacity is clamped to the ``[0, 1]`` range to avoid invalid RGBA
    values that may cause ``matplotlib`` to fail when drawing edges with a
    very high weight.
    """
    return max(0.0, min(0.3 + 0.05 * weight, 1.0))


def _node_radius(degree: int) -> float:
    """Return node radius based on the total number of connections.

    The radius grows gradually with increasing degree but is capped at 30 so
    that very active participants do not create disproportionately large
    circles in the visualisation.
    """
    return min(30.0, 6.0 + degree * 1.1)


def _cluster_color(index: int) -> str:
    """Return a color for a given cluster index."""
    palette = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]
    return palette[index % len(palette)]


plt.rcParams["font.family"] = "DejaVu Sans"


def visualize_graph(
    G: nx.MultiDiGraph,
    metrics: Dict[str, float],
    strengths: Dict[Tuple[str, str], float],
    path: str,
    min_strength: float = 0.0,
) -> None:
    """Save an interaction graph as a high resolution PNG image.

    Parameters
    ----------
    G : nx.MultiDiGraph
        Source graph with all interactions.
    metrics : Dict[str, float]
        Computed metrics for the chat (currently unused).
    strengths : Dict[Tuple[str, str], float]
        Aggregated edge strengths.
    path : str
        Output image path.
    min_strength : float, optional
        Edges weaker than this value are hidden. By default all edges are shown.
    """

    # Larger figure with high DPI for readability
    plt.figure(figsize=(12, 10), dpi=200)

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
        if u == v:
            continue
        if u in valid_nodes and v in valid_nodes and w >= min_strength:
            agg.add_edge(u, v, weight=w)

    # Spread nodes further apart so that labels do not overlap
    pos, clusters = _cluster_layout(agg, weight="weight")
    # Move the most connected nodes closer to the center
    degrees = dict(agg.degree())
    if degrees:
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:3]
        for n in top_nodes:
            x, y = pos[n]
            pos[n] = (x * 0.2, y * 0.2)
    weights = [float(data.get("weight", 1.0)) for *_, data in agg.edges(data=True)]

    node_sizes = [_node_radius(degrees.get(n, 0)) ** 2 for n in agg.nodes()]

    # Sanitize labels so exotic symbols do not break the font
    # Only include labels for nodes that will actually be drawn
    labels = {node: sanitize_text(str(node)) for node in agg.nodes()}
    label_pos = pos

    node_colors = [_cluster_color(clusters.get(n, 0)) for n in agg.nodes()]
    nx.draw_networkx_nodes(
        agg,
        pos,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors="black",
        linewidths=0.5,
    )

    edge_colors = [_edge_color(w) for w in weights]

    nx.draw_networkx_edges(
        agg,
        pos,
        width=[_edge_width(w) + 1 for w in weights],
        alpha=1.0,
        edge_color="black",
        arrows=False,
    )
    nx.draw_networkx_edges(
        agg,
        pos,
        width=[_edge_width(w) for w in weights],
        alpha=[_edge_opacity(w) for w in weights],
        edge_color=edge_colors,
        arrows=True,
        arrowsize=4,
    )

    nx.draw_networkx_labels(
        agg,
        label_pos,
        labels=labels,
        font_size=7,
        font_color="white",
        horizontalalignment="center",
        verticalalignment="center",
    )

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, format="png", bbox_inches="tight")
    plt.close()


def visualize_graph_html(
    G: nx.MultiDiGraph,
    strengths: Dict[Tuple[str, str], float],
    path: str,
    min_strength: float = 0.0,
) -> None:
    """Save an interactive graph visualisation as a standalone HTML file.

    Parameters
    ----------
    G : nx.MultiDiGraph
        Source graph with all interactions.
    strengths : Dict[Tuple[str, str], float]
        Aggregated interaction strengths for each edge.
    path : str
        Output HTML file.
    min_strength : float, optional
        Edges weaker than this value are hidden. By default all edges are shown.
    """

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
        if u == v:
            continue
        if u in valid_nodes and v in valid_nodes and w >= min_strength:
            agg.add_edge(u, v, weight=w)
    degrees = dict(agg.degree())
    node_radii = {n: _node_radius(deg) for n, deg in degrees.items()}

    _, clusters = _cluster_layout(agg, weight="weight")
    node_colors = {n: _cluster_color(clusters.get(n, 0)) for n in agg.nodes()}

    node_strengths: Dict[str, float] = {}
    for (u, v), w in strengths.items():
        if u in valid_nodes:
            node_strengths[u] = node_strengths.get(u, 0.0) + w
        if v in valid_nodes:
            node_strengths[v] = node_strengths.get(v, 0.0) + w

    # ``width`` and ``height`` are kept for backwards compatibility but
    # the actual SVG dimensions will be set dynamically in the generated
    # HTML so the graph takes up the full browser window.
    width = 960
    height = 720

    nodes = [
        {
            "id": n,
            "label": sanitize_text(str(n)),
            "radius": node_radii.get(n, 6.0),
            "color": node_colors.get(n, "#1f77b4"),
            "strength": node_strengths.get(n, 0.0),
            "cluster": clusters.get(n, 0),
        }
        for n in agg.nodes()
        if sanitize_text(str(n)) and degrees.get(n, 0) > 0
    ]

    links = [
        {
            "source": u,
            "target": v,
            "weight": float(data.get("weight", 1.0)),
            "color": _edge_color(float(data.get("weight", 1.0))),
            "width": _edge_width(float(data.get("weight", 1.0))),
            "source_label": sanitize_text(str(u)),
            "target_label": sanitize_text(str(v)),
        }
        for u, v, data in agg.edges(data=True)
    ]

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    links_json = json.dumps(links, ensure_ascii=False)

    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<script src='https://d3js.org/d3.v7.min.js'></script>",
        "<style>",
        "body {font-family: Arial, sans-serif;}",
        "line {opacity: 0.7; transition: stroke-width 0.2s;}",
        "circle {stroke: black; stroke-width: 1;}",
        "circle:hover {fill: orange;}",
        "text {font-size: 12px;}",
        "#legend div {margin-bottom: 4px;}",
        "</style>",
        "</head>",
        "<body>",
        "<svg id='svggraph' style='width:100vw;height:100vh' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>",
        "<marker id='arrow' viewBox='0 0 10 10' refX='6' refY='5' markerWidth='0.6' markerHeight='0.6' orient='auto-start-reverse'>",
        "<path d='M 0 0 L 10 5 L 0 10 z' fill='context-stroke' />",
        "</marker>",
        "</defs>",
        "<g id='graph'></g>",
        "</svg>",
        "<div id='legend' style='position:absolute;right:6px;top:6px;background:#fff;padding:4px;border:1px solid #ccc;font-size:11px'>",
        "<strong>Легенда</strong>",
        f"<div><svg width='40' height='6'><line x1='0' y1='3' x2='40' y2='3' stroke='{_edge_color(1)}' stroke-width='{_edge_width(1):.1f}'/></svg> Слабая связь</div>",
        f"<div><svg width='40' height='6'><line x1='0' y1='3' x2='40' y2='3' stroke='{_edge_color(3)}' stroke-width='{_edge_width(3):.1f}'/></svg> Средняя связь</div>",
        f"<div><svg width='40' height='6'><line x1='0' y1='3' x2='40' y2='3' stroke='{_edge_color(6)}' stroke-width='{_edge_width(6):.1f}'/></svg> Сильная связь</div>",
        "<div style='margin-top:4px'>\u0421\u0438\u043b\u0430 \u0441\u0432\u044f\u0437\u0438 \u2014 \u0441\u0443\u043c\u043c\u0430 \u0432\u0441\u0435\u0445 \u0432\u0437\u0430\u0438\u043c\u043e\u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0439 \u043c\u0435\u0436\u0434\u0443 \u0443\u0447\u0430\u0441\u0442\u043d\u0438\u043a\u0430\u043c\u0438:</div>",
        "<div>\u043e\u0442\u0432\u0435\u0442 = 1, \u0443\u043f\u043e\u043c\u0438\u043d\u0430\u043d\u0438\u0435 = 0.5, \u043f\u0435\u0440\u0435\u0441\u044b\u043b\u043a\u0430 = 0.7, \u0440\u0435\u0430\u043a\u0446\u0438\u044f = 0.3, \u0441\u043e\u0441\u0435\u0434\u043d\u0438\u0435 \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u044f = 0.2</div>",
        "<div style='margin-top:4px'>\u0420\u0430\u0437\u043c\u0435\u0440 \u043a\u0440\u0443\u0433\u0430 \u2014 \u0447\u0438\u0441\u043b\u043e \u0441\u0432\u044f\u0437\u0435\u0439</div>",
        "<div>\u0426\u0432\u0435\u0442 \u043a\u0440\u0443\u0433\u0430 \u2014 \u043a\u043b\u0430\u0441\u0442\u0435\u0440</div>",
        "</div>",
        "<script>",
        "const nodes = "+nodes_json+";",
        "const links = "+links_json+";",
        "const svg = d3.select('#svggraph');",
        "const g = d3.select('#graph');",
        "const width = window.innerWidth;",
        "const height = window.innerHeight;",
        "svg.attr('width', width).attr('height', height);",
        "const clusters = Array.from(new Set(nodes.map(n => n.cluster)));",
        "const clusterCenters = {};",
        "const radius = Math.min(width, height) / 1.8;",
        "clusters.forEach((c, i) => {",
        "    const angle = 2 * Math.PI * i / clusters.length;",
        "    clusterCenters[c] = {x: width / 2 + radius * Math.cos(angle), y: height / 2 + radius * Math.sin(angle)};",
        "});",
        "svg.call(d3.zoom().on('zoom', e => g.attr('transform', e.transform)));",
        "const link = g.selectAll('line').data(links).enter().append('line')",
        "    .attr('stroke', d => d.color)",
        "    .attr('stroke-width', d => d.width)",
        "    .attr('marker-end', 'url(#arrow)')",
        "    .on('mouseover', function(event, d){ d3.select(this).attr('stroke','red').attr('stroke-width', d.width + 2); })",
        "    .on('mouseout', function(event, d){ d3.select(this).attr('stroke', d.color).attr('stroke-width', d.width); });",
        "link.append('title').text(d => d.source_label + ' \u2192 ' + d.target_label + ' | \u0421\u0438\u043b\u0430: ' + d.weight.toFixed(2));",
        "const node = g.selectAll('circle').data(nodes).enter().append('circle')",
        "    .attr('r', d => d.radius)",
        "    .attr('fill', d => d.color)",
        "    .call(d3.drag().on('start', dragStarted).on('drag', dragged).on('end', dragEnded));",
        "node.append('title').text(d => d.label + ' | \u0421\u0438\u043b\u0430: ' + d.strength.toFixed(2));",
        "const label = g.selectAll('text').data(nodes).enter().append('text').text(d => d.label)",
        "    .attr('text-anchor', 'middle').attr('alignment-baseline', 'middle');",
        "const simulation = d3.forceSimulation(nodes)",
        "    .force('link', d3.forceLink(links).id(d => d.id)"
        "        .distance(d => 150 / Math.max(d.weight, 0.1))"
        "        .strength(d => {",
        "            const base = Math.min(d.weight / 6, 1);",
        "            // Increase attraction within a cluster and reduce it across clusters",
        "            const cf = d.source.cluster === d.target.cluster ? 10 : 1 / 80;",
        "            return base * cf * 0.0001;",
        "        }))",
        "    .force('charge', d3.forceManyBody().strength(-14000))",
        "    .force('collide', d3.forceCollide().radius(d => d.radius + 8))",
        "    .force('clusterX', d3.forceX(d => clusterCenters[d.cluster].x).strength(1.8))",
        "    .force('clusterY', d3.forceY(d => clusterCenters[d.cluster].y).strength(1.8))",
        "    .force('center', d3.forceCenter(width / 2, height / 2));",
        "simulation.on('tick', () => {",
        "    link.attr('x1', d => d.source.x).attr('y1', d => d.source.y).attr('x2', d => d.target.x).attr('y2', d => d.target.y);",
        "    node.attr('cx', d => d.x).attr('cy', d => d.y);",
        "    label.attr('x', d => d.x).attr('y', d => d.y);",
        "});",
        "function dragStarted(event, d){ if(!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }",
        "function dragged(event, d){ d.fx = event.x; d.fy = event.y; }",
        "function dragEnded(event, d){ if(!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }",
        "</script>",
        "</body>",
        "</html>",
    ]

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
