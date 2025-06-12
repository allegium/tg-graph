import networkx as nx
from collections import defaultdict
from typing import Dict, List
from .parser import Message

INTERACTION_WEIGHTS = {
    'reply': 1.0,
    'mention': 0.5,
    'forward': 0.7,
    'reaction': 0.3,
    'temporal': 0.2,
}

def compute_median_delta(messages: List[Message]) -> float:
    deltas = []
    msg_map = {m.id: m for m in messages}
    prev_date = None
    for m in messages:
        if m.reply_to and m.reply_to in msg_map:
            # difference from replied message
            # placeholder: for now use 0 since we do not parse datetime
            deltas.append(0)
        elif prev_date:
            deltas.append(0)
        prev_date = m.date
    if not deltas:
        return 0
    deltas.sort()
    mid = len(deltas) // 2
    return float(deltas[mid])

def build_graph(messages: List[Message], median_delta: float) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    last_message = None
    for m in messages:
        author = m.from_id
        G.add_node(author)
        if m.reply_to:
            target = next((msg.from_id for msg in messages if msg.id == m.reply_to), None)
            if target:
                G.add_edge(author, target, weight=INTERACTION_WEIGHTS['reply'])
        if isinstance(m.text, str) and '@' in m.text:
            # naive mention detection
            for word in m.text.split():
                if word.startswith('@'):
                    G.add_edge(author, word[1:], weight=INTERACTION_WEIGHTS['mention'])
        if m.forwarded_from:
            G.add_edge(author, m.forwarded_from, weight=INTERACTION_WEIGHTS['forward'])
        if m.reactions:
            for reaction in m.reactions:
                actor = reaction.get('actor')
                if actor:
                    G.add_edge(actor, author, weight=INTERACTION_WEIGHTS['reaction'])
        if last_message and median_delta > 0:
            G.add_edge(author, last_message.from_id, weight=INTERACTION_WEIGHTS['temporal'])
        last_message = m
    return G
