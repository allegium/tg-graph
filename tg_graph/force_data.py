"""Utilities to build data for force-directed graphs from Telegram exports."""

from typing import Dict, List, Tuple

from .parser import load_chat, parse_messages, Message


def build_user_name_map(messages: List[Message]) -> Dict[str, str]:
    """Return mapping from user_id to a display name.

    The ``from`` field is used as the preferred name. ``text_entities`` are
    inspected for additional nicknames when available. First discovered name for
    a user id is kept."""

    names: Dict[str, str] = {}
    for m in messages:
        uid = m.from_id
        if uid and m.from_name:
            names[str(uid)] = m.from_name
        if m.text_entities:
            for ent in m.text_entities:
                user = ent.get("user_id")
                text = ent.get("text")
                if user and text and str(user) not in names:
                    names[str(user)] = text.lstrip("@")
    return names


def build_reply_edges(messages: List[Message]) -> Dict[Tuple[str, str], int]:
    """Aggregate reply interactions between users."""

    msg_map = {m.id: m for m in messages}
    edges: Dict[Tuple[str, str], int] = {}
    for m in messages:
        if m.reply_to and m.from_id:
            target = msg_map.get(m.reply_to)
            if target and target.from_id:
                src = str(m.from_id)
                dst = str(target.from_id)
                key = (src, dst)
                edges[key] = edges.get(key, 0) + 1
    return edges


def prepare_force_data(path: str) -> Dict[str, List[Dict]]:
    """Load a Telegram export and return nodes and links for visualisation."""

    data = load_chat(path)
    messages = parse_messages(data)
    names = build_user_name_map(messages)
    edges = build_reply_edges(messages)

    nodes = [
        {"id": uid, "label": name}
        for uid, name in names.items()
    ]

    links = [
        {"source": s, "target": t, "weight": w}
        for (s, t), w in edges.items()
    ]

    return {"nodes": nodes, "links": links}


__all__ = [
    "build_user_name_map",
    "build_reply_edges",
    "prepare_force_data",
]

