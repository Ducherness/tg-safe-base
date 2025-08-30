# handlers/__init__.py
from . import notes, passwords, master

HANDLERS_ROUTERS = [notes.router, passwords.router, master.router]
