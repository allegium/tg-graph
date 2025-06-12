import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict


def visualize_graph(G: nx.MultiDiGraph, metrics: Dict[str, float], path: str) -> None:
    plt.figure(figsize=(10, 8))
    # Spread nodes further apart for readability
    pos = nx.spring_layout(G, k=1.2, seed=42)
    weights = [data.get('weight', 1.0) for *_, data in G.edges(data=True)]

    node_colors = range(G.number_of_nodes())
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=400,
        node_color=node_colors,
        cmap=plt.cm.Set3,
        edgecolors="black",
    )
    nx.draw_networkx_edges(
        G,
        pos,
        width=[w * 1.5 for w in weights],
        alpha=0.7,
        edge_color="gray",
        arrows=True,
    )
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.axis("off")
    plt.title("Telegram Chat Graph")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
