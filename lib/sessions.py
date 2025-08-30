# lib/sessions.py
from datetime import datetime, timedelta

_unlocked = {}

def set_unlocked(user_id: int, key: bytes, seconds: int = 300):
    _unlocked[user_id] = {'key': key, 'until': datetime.utcnow() + timedelta(seconds=seconds)}

def is_unlocked(user_id: int) -> bool:
    v = _unlocked.get(user_id)
    if not v:
        return False
    if v['until'] < datetime.utcnow():
        _unlocked.pop(user_id, None)
        return False
    return True

def get_key(user_id: int):
    v = _unlocked.get(user_id)
    return v and v['key']

def lock_user(user_id: int):
    _unlocked.pop(user_id, None)
