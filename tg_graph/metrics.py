import networkx as nx
from typing import Dict


def compute_metrics(G: nx.MultiDiGraph) -> Dict[str, float]:
    metrics = {
        'nodes': G.number_of_nodes(),
        'edges': G.number_of_edges(),
    }
    if G.number_of_nodes() == 0:
        return metrics
    degrees = dict(G.degree())
    metrics['avg_degree'] = sum(degrees.values()) / len(degrees)
    metrics['degree_centrality'] = nx.degree_centrality(G)
    metrics['betweenness_centrality'] = nx.betweenness_centrality(G)
    metrics['closeness_centrality'] = nx.closeness_centrality(G)
    metrics['pagerank'] = nx.pagerank(G)
    try:
        clusters = nx.algorithms.community.louvain_communities(G)
        metrics['clusters'] = len(clusters)
    except Exception:
        metrics['clusters'] = 0
    try:
        metrics['diameter'] = nx.diameter(G.to_undirected())
    except Exception:
        metrics['diameter'] = 0
    return metrics
