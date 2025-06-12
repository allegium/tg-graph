import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict
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


def visualize_graph(G: nx.MultiDiGraph, metrics: Dict[str, float], path: str) -> None:
    """Save an interaction graph as a high resolution PNG image."""

    # Larger figure with high DPI for readability
    plt.figure(figsize=(12, 10), dpi=200)

    # Spread nodes further apart so that labels do not overlap
    pos = nx.spring_layout(G, k=2.0, seed=42)
    # Move the most connected nodes closer to the center
    degrees = dict(G.degree())
    if degrees:
        top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:3]
        for n in top_nodes:
            x, y = pos[n]
            pos[n] = (x * 0.2, y * 0.2)
    weights = [float(data.get("weight", 1.0)) for *_, data in G.edges(data=True)]

    # Sanitize labels so exotic symbols do not break the font
    labels = {node: sanitize_text(str(node)) for node in G.nodes()}
    label_pos = _adjust_label_positions(pos)

    node_colors = range(G.number_of_nodes())
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=150,
        node_color=node_colors,
        cmap=plt.cm.tab20,
        edgecolors="black",
        linewidths=0.5,
    )

    nx.draw_networkx_edges(
        G,
        pos,
        width=[w * 2.0 for w in weights],
        alpha=0.7,
        edge_color="gray",
        arrows=True,
    )

    nx.draw_networkx_labels(
        G,
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
