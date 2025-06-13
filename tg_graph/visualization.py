import networkx as nx
import matplotlib.pyplot as plt
import math
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
    radius = 8.0
    for idx, community in enumerate(communities):
        sub = G.subgraph(community)
        sub_pos = nx.spring_layout(sub, k=4.0, seed=42, weight=weight)
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
    """Return node radius based on the total number of connections."""
    return 6.0 + degree * 2.0


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
    min_strength: float = 2.0,
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
        Edges weaker than this value are hidden.
    """

    # Larger figure with high DPI for readability
    plt.figure(figsize=(12, 10), dpi=200)

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
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
    label_pos = _adjust_label_positions(pos)

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
        font_color="black",
        bbox=dict(facecolor="white", edgecolor="none", pad=0.2, alpha=0.8),
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
        Edges weaker than this value are hidden.
    """

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
        if u in valid_nodes and v in valid_nodes and w >= min_strength:
            agg.add_edge(u, v, weight=w)
    degrees = dict(agg.degree())
    node_radii = {n: _node_radius(deg) for n, deg in degrees.items()}

    pos, clusters = _cluster_layout(agg, weight="weight")
    node_colors = {n: _cluster_color(clusters.get(n, 0)) for n in agg.nodes()}

    node_strengths: Dict[str, float] = {}
    for (u, v), w in strengths.items():
        if u in valid_nodes:
            node_strengths[u] = node_strengths.get(u, 0.0) + w
        if v in valid_nodes:
            node_strengths[v] = node_strengths.get(v, 0.0) + w

    coords = list(pos.values())
    min_dist = None
    for i, (x1, y1) in enumerate(coords):
        for x2, y2 in coords[i + 1 :]:
            d = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            if min_dist is None or d < min_dist:
                min_dist = d
    if not min_dist:
        min_dist = 0.01

    scale = 60.0 / min_dist  # 15 mm ~ 60 px
    scaled = {n: (x * scale, y * scale) for n, (x, y) in pos.items()}

    xs = [x for x, _ in scaled.values()]
    ys = [y for _, y in scaled.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    margin = 50
    width = int(max_x - min_x + 2 * margin)
    height = int(max_y - min_y + 2 * margin)

    shifted = {
        n: (x - min_x + margin, y - min_y + margin) for n, (x, y) in scaled.items()
    }

    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<script src='https://d3js.org/d3.v7.min.js'></script>",
        "<style>",
        "body {font-family: Arial, sans-serif;} ",
        "line {stroke-width: 1.5; opacity: 0.7; transition: stroke-width 0.2s;} ",
        "line:hover {stroke: red; stroke-width: 4;} ",
        "circle {stroke: black; stroke-width: 1;} ",
        "circle:hover {fill: orange;} ",
        "text {font-size: 12px;} ",
        "#legend div {margin-bottom: 4px;} ",
        "</style>",
        "</head>",
        "<body>",
        f"<svg id='svggraph' width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>",
        "<marker id='arrow' viewBox='0 0 10 10' refX='6' refY='5' markerWidth='3' markerHeight='3' orient='auto-start-reverse'>",
        "<path d='M 0 0 L 10 5 L 0 10 z' fill='context-stroke' />",
        "</marker>",
        "</defs>",
        "<g id='graph'>",
    ]

    for u, v, data in agg.edges(data=True):
        if u not in shifted or v not in shifted:
            # Skip edges for nodes that are not displayed
            continue
        w = float(data.get("weight", 1.0))
        color = _edge_color(w)
        x1, y1 = shifted[u]
        x2, y2 = shifted[v]
        su = sanitize_text(str(u))
        sv = sanitize_text(str(v))
        parts.append(
            f"<line x1='{x1:.2f}' y1='{y1:.2f}' x2='{x2:.2f}' y2='{y2:.2f}' marker-end='url(#arrow)' style='stroke:black; stroke-width:{_edge_width(w) + 1:.2f}; opacity:1; pointer-events:none'></line>"
        )
        parts.append(
            f"<line x1='{x1:.2f}' y1='{y1:.2f}' x2='{x2:.2f}' y2='{y2:.2f}' marker-end='url(#arrow)' style='stroke:{color}; stroke-width:{_edge_width(w):.2f}; opacity:{_edge_opacity(w):.2f}'>"
            f"<title>{su} \u2192 {sv} | \u0421\u0438\u043b\u0430: {w:.2f}</title></line>"
        )

    for node, (x, y) in shifted.items():
        label = sanitize_text(str(node))
        if not label:
            continue
        strength = node_strengths.get(node, 0.0)
        radius = node_radii.get(node, 6.0)
        color = node_colors.get(node, "#1f77b4")
        parts.append(
            f"<circle cx='{x:.2f}' cy='{y:.2f}' r='{radius:.2f}' fill='{color}'>"
            f"<title>{label} | \u0421\u0438\u043b\u0430: {strength:.2f}</title></circle>"
        )
        parts.append(f"<text x='{x + radius + 2:.2f}' y='{y - radius:.2f}'>{label}</text>")

    parts.extend([
        "</g>",
        "</svg>",
        "<div id='legend' style='position:absolute;right:10px;top:10px;background:#fff;padding:6px;border:1px solid #ccc'>",
        "<strong>Легенда</strong>",
        f"<div><svg width='40' height='6'><line x1='0' y1='3' x2='40' y2='3' stroke='{_edge_color(1)}' stroke-width='{_edge_width(1):.1f}'/></svg> Слабая связь</div>",
        f"<div><svg width='40' height='6'><line x1='0' y1='3' x2='40' y2='3' stroke='{_edge_color(3)}' stroke-width='{_edge_width(3):.1f}'/></svg> Средняя связь</div>",
        f"<div><svg width='40' height='6'><line x1='0' y1='3' x2='40' y2='3' stroke='{_edge_color(6)}' stroke-width='{_edge_width(6):.1f}'/></svg> Сильная связь</div>",
        "<div style='margin-top:4px'>Размер круга \u2014 число связей</div>",
        "<div>Цвет круга \u2014 кластер</div>",
        "</div>",
        "<script>const svg=d3.select('#svggraph');const g=d3.select('#graph');svg.call(d3.zoom().on('zoom',e=>g.attr('transform',e.transform)));</script>",
        "</body>",
        "</html>",
    ])

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
