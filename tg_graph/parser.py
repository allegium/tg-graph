import json
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Message:
    id: int
    date: str
    from_id: Optional[str]
    from_name: Optional[str]
    text: str
    reply_to: Optional[int] = None
    forwarded_from: Optional[str] = None
    reactions: Optional[List[Dict]] = None
    text_entities: Optional[List[Dict]] = None

@dataclass
class User:
    id: str
    name: Optional[str]
    username: Optional[str]

def load_chat(path: str) -> Dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_messages(data: Dict) -> List[Message]:
    messages = []
    for msg in data.get('messages', []):
        messages.append(
            Message(
                id=msg.get('id'),
                date=msg.get('date'),
                from_id=msg.get('from_id'),
                from_name=msg.get('from'),
                text=msg.get('text') if isinstance(msg.get('text'), str) else '',
                reply_to=msg.get('reply_to_message_id'),
                forwarded_from=msg.get('forwarded_from'),
                reactions=msg.get('reactions'),
                text_entities=msg.get('text_entities'),
            )
        )
    return messages

def parse_users(data: Dict) -> List[User]:
    users = []
    for user in data.get('users', []):
        users.append(
            User(
                id=str(user.get('id')),
                name=user.get('name'),
                username=user.get('username'),
            )
        )
    return users
