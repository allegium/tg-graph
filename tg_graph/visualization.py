import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict


def visualize_graph(G: nx.MultiDiGraph, metrics: Dict[str, float], path: str) -> None:
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)
    weights = [data.get('weight', 1.0) for *_ , data in G.edges(data=True)]
    nx.draw_networkx_nodes(G, pos, node_size=300)
    nx.draw_networkx_edges(G, pos, width=weights, alpha=0.5, arrows=True)
    nx.draw_networkx_labels(G, pos, font_size=8)
    plt.axis('off')
    plt.title('Telegram Chat Graph')
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
