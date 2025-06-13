import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, Tuple
from .utils import sanitize_text


def _adjust_label_positions(pos: Dict[str, tuple], min_dist: float = 0.05) -> Dict[str, tuple]:
    """Return new positions shifted slightly to reduce label overlap."""
    new_pos: Dict[str, tuple] = {}
    for node, (x, y) in pos.items():
        nx_, ny_ = x, y
        # Shift label until it does not collide with already placed labels
        while any(((nx_ - ox) ** 2 + (ny_ - oy) ** 2) ** 0.5 < min_dist for ox, oy in new_pos.values()):
            ny_ += min_dist
        new_pos[node] = (nx_, ny_)
    return new_pos

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
    pos = nx.spring_layout(agg, k=4.0, seed=42, weight="weight")
    # Move the most connected nodes closer to the center
    degrees = dict(agg.degree())
    if degrees:
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:3]
        for n in top_nodes:
            x, y = pos[n]
            pos[n] = (x * 0.2, y * 0.2)
    weights = [float(data.get("weight", 1.0)) for *_, data in agg.edges(data=True)]

    # Sanitize labels so exotic symbols do not break the font
    labels = {node: sanitize_text(str(node)) for node in G.nodes()}
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
    G: nx.MultiDiGraph, strengths: Dict[Tuple[str, str], float], path: str
) -> None:
    """Save an interactive graph visualisation as a standalone HTML file."""

    agg = nx.DiGraph()
    valid_nodes = [n for n in G.nodes() if sanitize_text(str(n))]
    agg.add_nodes_from(valid_nodes)
    for (u, v), w in strengths.items():
        if u in valid_nodes and v in valid_nodes:
            agg.add_edge(u, v, weight=w)

    pos = nx.spring_layout(agg, k=4.0, seed=42, weight="weight")

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

    shifted = {n: (x - min_x + margin, y - min_y + margin) for n, (x, y) in scaled.items()}

    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        "<meta charset='utf-8'>",
        "<style>",
        "line {stroke-width: 1.5; opacity: 0.7;}",
        "line:hover {stroke: red; stroke-width: 3;}",
        "circle {fill: #1f77b4; stroke: black; stroke-width: 1;}",
        "circle:hover {fill: orange;}",
        "text {font-size: 12px; font-family: Arial, sans-serif;}",
        "</style>",
        "</head>",
        "<body>",
        f"<svg width='{width}' height='{height}' xmlns='http://www.w3.org/2000/svg'>",
        "<defs>",
        "<marker id='arrow' viewBox='0 0 10 10' refX='6' refY='5' markerWidth='3' markerHeight='3' orient='auto-start-reverse'>",
        "<path d='M 0 0 L 10 5 L 0 10 z' fill='context-stroke' />",
        "</marker>",
        "</defs>",
    ]

    def _color(weight: float) -> str:
        if weight <= 1:
            return "#fff7ae"  # pastel yellow
        if weight <= 3:
            return "#b2ffb2"  # pastel green
        if weight <= 5:
            return "#b2e1ff"  # pastel blue
        return "#d7b2ff"  # pastel purple

    for (u, v), w in strengths.items():
        x1, y1 = shifted[u]
        x2, y2 = shifted[v]
        su = sanitize_text(str(u))
        sv = sanitize_text(str(v))
        color = _color(w)
        parts.append(
            f"<line x1='{x1:.2f}' y1='{y1:.2f}' x2='{x2:.2f}' y2='{y2:.2f}' marker-end='url(#arrow)' style='stroke:{color}; stroke-width:{w * 2.0:.2f}'>"
            f"<title>{su} \u2192 {sv} | \u0421\u0438\u043b\u0430: {w:.2f}</title></line>"
        )

    for node, (x, y) in shifted.items():
        label = sanitize_text(str(node))
        if not label:
            continue
        parts.append(f"<circle cx='{x:.2f}' cy='{y:.2f}' r='8'><title>{label}</title></circle>")
        parts.append(f"<text x='{x + 10:.2f}' y='{y - 10:.2f}'>{label}</text>")

    parts.extend(["</svg>", "</body>", "</html>"])

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
