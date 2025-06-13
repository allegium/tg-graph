import networkx as nx
from typing import Dict, Iterable
from .utils import sanitize_text


def _simple_pagerank(
    G: nx.MultiDiGraph,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1.0e-06,
    nodes: Iterable = None,
) -> Dict[str, float]:
    """Compute PageRank without requiring SciPy.

    This implementation follows the power iteration method and
    works purely with standard Python containers so it does not
    depend on NumPy or SciPy. Only a small subset of the features
    of ``nx.pagerank`` are supported which is enough for the bot.
    """

    if nodes is None:
        nodes = list(G.nodes())
    else:
        nodes = list(nodes)

    n = len(nodes)
    if n == 0:
        return {}

    # Initial rank values
    rank = {u: 1.0 / n for u in nodes}

    # Pre-compute the sum of outgoing edge weights for efficiency
    out_weight = {}
    for u in nodes:
        total = 0.0
        for _, _, data in G.out_edges(u, data=True):
            total += float(data.get("weight", 1.0))
        out_weight[u] = total

    for _ in range(max_iter):
        prev_rank = rank.copy()
        dangling_sum = (
            alpha * sum(prev_rank[u] for u in nodes if out_weight[u] == 0.0) / n
        )
        for v in nodes:
            rank_v = (1.0 - alpha) / n + dangling_sum
            for u, _, data in G.in_edges(v, data=True):
                weight = float(data.get("weight", 1.0))
                if out_weight[u] != 0:
                    rank_v += alpha * prev_rank[u] * weight / out_weight[u]
            rank[v] = rank_v

        # Check convergence
        err = sum(abs(rank[u] - prev_rank[u]) for u in nodes)
        if err < tol:
            break

    return rank


def compute_metrics(G: nx.MultiDiGraph) -> Dict[str, float]:
    metrics = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
    }
    if G.number_of_nodes() == 0:
        return metrics
    degrees = dict(G.degree())
    metrics["avg_degree"] = sum(degrees.values()) / len(degrees)
    metrics["degree_centrality"] = nx.degree_centrality(G)
    metrics["betweenness_centrality"] = nx.betweenness_centrality(G)
    metrics["closeness_centrality"] = nx.closeness_centrality(G)
    try:
        # ``nx.pagerank`` uses SciPy when available. On systems where
        # SciPy is not installed this may fail, so we use a small
        # fallback implementation.
        metrics["pagerank"] = nx.pagerank(G)
    except ModuleNotFoundError:
        metrics["pagerank"] = _simple_pagerank(G)
    try:
        clusters = nx.algorithms.community.louvain_communities(G)
        metrics["clusters"] = len(clusters)
    except Exception:
        metrics["clusters"] = 0
    try:
        metrics["diameter"] = nx.diameter(G.to_undirected())
    except Exception:
        metrics["diameter"] = 0
    return metrics


def compute_interaction_strengths(G: nx.MultiDiGraph) -> Dict[tuple, float]:
    """Aggregate edge weights between every pair of participants."""
    strengths: Dict[tuple, float] = {}
    for u, v, data in G.edges(data=True):
        if not sanitize_text(str(u)) or not sanitize_text(str(v)):
            continue
        key = (u, v)
        strengths[key] = strengths.get(key, 0.0) + float(data.get("weight", 1.0))
    return strengths


def compute_node_strengths(G: nx.MultiDiGraph) -> Dict[str, float]:
    """Return the total strength of connections for every node."""
    totals: Dict[str, float] = {}
    for u, v, data in G.edges(data=True):
        w = float(data.get("weight", 1.0))
        if sanitize_text(str(u)):
            totals[u] = totals.get(u, 0.0) + w
        if sanitize_text(str(v)):
            totals[v] = totals.get(v, 0.0) + w
    return totals
