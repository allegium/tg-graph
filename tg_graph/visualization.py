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


def _cluster_layout(G: nx.Graph, weight: str = "weight") -> Dict[str, tuple]:
    """Return node positions that emphasise densely connected groups."""
    try:
        communities = list(nx.algorithms.community.louvain_communities(G))
    except Exception:
        communities = [set(G.nodes())]
    if not communities:
        communities = [set(G.nodes())]

    pos: Dict[str, tuple] = {}
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
    return pos


plt.rcParams["font.family"] = "DejaVu Sans"


def visualize_graph(
    G: nx.MultiDiGraph,
    metrics: Dict[str, float],
    strengths: Dict[Tuple[str, str], float],
    path: str,
) -> None:
    """Save an interaction graph as a high resolution PNG image.

    The width of each edge reflects the cumulative strength of interactions
    between participants.
    """

    # Larger figure with high DPI for readability
    plt.figure(figsize=(12, 10), dpi=200)

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
        if u in valid_nodes and v in valid_nodes:
            agg.add_edge(u, v, weight=w)

    # Spread nodes further apart so that labels do not overlap
    pos = _cluster_layout(agg, weight="weight")
    # Move the most connected nodes closer to the center
    degrees = dict(agg.degree())
    if degrees:
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:3]
        for n in top_nodes:
            x, y = pos[n]
            pos[n] = (x * 0.2, y * 0.2)
    weights = [float(data.get("weight", 1.0)) for *_, data in agg.edges(data=True)]

    # Sanitize labels so exotic symbols do not break the font
    # Only include labels for nodes that will actually be drawn
    labels = {node: sanitize_text(str(node)) for node in agg.nodes()}
    label_pos = _adjust_label_positions(pos)

    node_colors = range(agg.number_of_nodes())
    nx.draw_networkx_nodes(
        agg,
        pos,
        node_size=150,
        node_color=node_colors,
        cmap=plt.cm.tab20,
        edgecolors="black",
        linewidths=0.5,
    )

    def _color(weight: float) -> str:
        if weight <= 1:
            return "#fff7ae"  # pastel yellow
        if weight <= 3:
            return "#b2ffb2"  # pastel green
        if weight <= 5:
            return "#b2e1ff"  # pastel blue
        return "#d7b2ff"  # pastel purple

    edge_colors = [_color(w) for w in weights]

    nx.draw_networkx_edges(
        agg,
        pos,
        width=[w * 2.0 + 2 for w in weights],
        alpha=1.0,
        edge_color="black",
        arrows=False,
    )
    nx.draw_networkx_edges(
        agg,
        pos,
        width=[w * 2.0 for w in weights],
        alpha=0.7,
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
    min_strength: float = 2.0,
) -> None:
    """Save an interactive graph visualisation as a standalone HTML file.

    Parameters
    ----------
    G : nx.MultiDiGraph
        Graph of interactions.
    strengths : Dict[Tuple[str, str], float]
        Aggregated edge weights between nodes.
    path : str
        Destination file for the HTML.
    min_strength : float, optional
        Threshold for displaying edges, by default 2.0.
    """

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
        if u in valid_nodes and v in valid_nodes:
            agg.add_edge(u, v, weight=w)

    pos = _cluster_layout(agg, weight="weight")

    node_strengths: Dict[str, float] = {}
    for (u, v), w in strengths.items():
        if u in valid_nodes:
            node_strengths[u] = node_strengths.get(u, 0.0) + w
        if v in valid_nodes:
            node_strengths[v] = node_strengths.get(v, 0.0) + w

    degrees = dict(agg.degree())

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
        "<style>",
        "body {background:#ffffff; margin:0; overflow:hidden; font-family:Arial, sans-serif; font-size:12px;}",
        "svg {width:100%; height:100%;}",
        "line {transition:opacity .2s, stroke-width .2s;}",
        "circle {fill:#1f77b4; stroke:black; stroke-width:1;}",
        "circle:hover {fill:orange;}",
        "text {font-size:12px; font-family:Arial, sans-serif;}",
        "</style>",
        "</head>",
        "<body>",
        f"<svg viewBox='0 0 {width} {height}' width='100%' height='100%' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>",
        "<marker id='arrow' viewBox='0 0 10 10' refX='6' refY='5' markerWidth='3' markerHeight='3' orient='auto-start-reverse'>",
        "<path d='M 0 0 L 10 5 L 0 10 z' fill='context-stroke' />",
        "</marker>",
        "</defs>",
        "<g id='legend' transform='translate(20,20)'>",
        "<rect x='0' y='0' width='140' height='110' fill='white' stroke='black' stroke-width='0.5' />",
        "<text x='10' y='15'>\u041b\u0435\u0433\u0435\u043d\u0434\u0430</text>",
        f"<line x1='10' y1='30' x2='40' y2='30' stroke='#fff7ae' stroke-width='{1 + 1*1.5:.1f}' />",
        "<text x='50' y='34'>\u0441\u0438\u043b\u0430 1</text>",
        f"<line x1='10' y1='45' x2='40' y2='45' stroke='#b2ffb2' stroke-width='{1 + 3*1.5:.1f}' />",
        "<text x='50' y='49'>\u0441\u0438\u043b\u0430 3</text>",
        f"<line x1='10' y1='60' x2='40' y2='60' stroke='#b2e1ff' stroke-width='{1 + 5*1.5:.1f}' />",
        "<text x='50' y='64'>\u0441\u0438\u043b\u0430 5</text>",
        f"<line x1='10' y1='75' x2='40' y2='75' stroke='#d7b2ff' stroke-width='{1 + 7*1.5:.1f}' />",
        "<text x='50' y='79'>\u0441\u0438\u043b\u0430 7+</text>",
        "<circle cx='20' cy='95' r='5' stroke='black' fill='#1f77b4' />",
        "<text x='50' y='99'>\u043c\u0435\u043d\u044c\u0448\u0435 \u0441\u0432\u044f\u0437\u0435\u0439</text>",
        "<circle cx='20' cy='110' r='10' stroke='black' fill='#1f77b4' />",
        "<text x='50' y='114'>\u0431\u043e\u043b\u044c\u0448\u0435 \u0441\u0432\u044f\u0437\u0435\u0439</text>",
        "</g>",
    ]

    def _color(weight: float) -> str:
        if weight <= 1:
            return "#fff7ae"  # pastel yellow
        if weight <= 3:
            return "#b2ffb2"  # pastel green
        if weight <= 5:
            return "#b2e1ff"  # pastel blue
        return "#d7b2ff"  # pastel purple

    for u, v, data in agg.edges(data=True):
        if u not in shifted or v not in shifted:
            # Skip edges for nodes that are not displayed
            continue
        w = float(data.get("weight", 1.0))
        if w < min_strength:
            continue
        x1, y1 = shifted[u]
        x2, y2 = shifted[v]
        su = sanitize_text(str(u))
        sv = sanitize_text(str(v))
        color = _color(w)
        width = 1 + w * 1.5
        opacity = 0.3 + 0.05 * w
        parts.append(
            f"<line x1='{x1:.2f}' y1='{y1:.2f}' x2='{x2:.2f}' y2='{y2:.2f}' marker-end='url(#arrow)' style='stroke:{color}; stroke-width:{width:.2f}; opacity:{opacity:.2f}'>"
            f"<title>{su} \u2192 {sv} | \u0421\u0438\u043b\u0430: {w:.2f}</title></line>"
        )

    for node, (x, y) in shifted.items():
        label = sanitize_text(str(node))
        if not label:
            continue
        strength = node_strengths.get(node, 0.0)
        radius = 5 + 0.5 * degrees.get(node, 0)
        parts.append(
            f"<circle cx='{x:.2f}' cy='{y:.2f}' r='{radius:.2f}'><title>{label} | \u0421\u0438\u043b\u0430: {strength:.2f}</title></circle>"
        )
        parts.append(f"<text x='{x + radius + 2:.2f}' y='{y - radius:.2f}'>{label}</text>")

    parts.extend([
        "</svg>",
        "<script src='https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js'></script>",
        "<script>svgPanZoom(document.querySelector('svg'), {zoomEnabled: true, controlIconsEnabled: true});</script>",
        "</body>",
        "</html>",
    ])

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
