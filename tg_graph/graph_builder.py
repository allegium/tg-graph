import networkx as nx
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

def build_graph(
    messages: List[Message],
    median_delta: float,
    user_map: Dict[str, str],
    username_map: Dict[str, str],
) -> nx.MultiDiGraph:
    """Build a directed multigraph using display names instead of user IDs."""
    G = nx.MultiDiGraph()
    msg_map = {m.id: m for m in messages}
    last_message = None
    for m in messages:
        author = m.from_name
        if not author or author.lower() == "user":
            last_message = m
            continue
        G.add_node(author)
        if m.reply_to:
            target_msg = msg_map.get(m.reply_to)
            if target_msg and target_msg.from_name and target_msg.from_name.lower() != "user":
                target = target_msg.from_name
                G.add_edge(author, target, weight=INTERACTION_WEIGHTS['reply'])
        if isinstance(m.text, str) and '@' in m.text:
            # naive mention detection
            for word in m.text.split():
                if word.startswith('@'):
                    nick = word[1:].rstrip('.,!?:;')
                    target = username_map.get(nick, nick)
                    if target.lower() != "user":
                        G.add_edge(author, target, weight=INTERACTION_WEIGHTS['mention'])
        if m.forwarded_from:
            fwd = m.forwarded_from
            if isinstance(fwd, dict):
                fwd = str(fwd.get('id') or fwd.get('from_id') or fwd)
            else:
                fwd = str(fwd)
            target = user_map.get(fwd) or username_map.get(fwd.lstrip('@')) or "Unknown"
            if target.lower() != "user":
                G.add_edge(author, target, weight=INTERACTION_WEIGHTS['forward'])
        if m.reactions:
            for reaction in m.reactions:
                actor = reaction.get('actor')
                if actor:
                    if isinstance(actor, dict):
                        actor = str(actor.get('id') or actor.get('from_id') or actor)
                    else:
                        actor = str(actor)
                    actor_name = user_map.get(actor) or username_map.get(actor.lstrip('@')) or "Unknown"
                    if actor_name.lower() != "user":
                        G.add_edge(actor_name, author, weight=INTERACTION_WEIGHTS['reaction'])
        if last_message and median_delta > 0:
            prev_author = last_message.from_name
            if prev_author and prev_author.lower() != "user":
                G.add_edge(
                    author,
                    prev_author,
                    weight=INTERACTION_WEIGHTS['temporal'],
                )
        last_message = m
    return G
