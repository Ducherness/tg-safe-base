#!/usr/bin/env python3
import sys
import json
import base64
import getpass
from pathlib import Path

from lib.crypto import derive_key

CFG_PATH = Path(__file__).parent / 'data' / 'config.json'
CFG_PATH.parent.mkdir(exist_ok=True)

def load_cfg():
    if CFG_PATH.exists():
        return json.loads(CFG_PATH.read_text(encoding='utf-8'))
    return {}

def save_cfg(cfg):
    CFG_PATH.write_text(json.dumps(cfg, indent=2))
    try:
        import os
        os.chmod(CFG_PATH, 0o600)
    except Exception:
        pass

def set_master():
    pw = getpass.getpass("Введите мастер-пароль: ")
    pw2 = getpass.getpass("Повторите пароль: ")
    if pw != pw2:
        print("Пароли не совпадают. Отмена.")
        sys.exit(1)
    key = derive_key(pw)
    cfg = load_cfg()
    cfg['master_key'] = base64.b64encode(key).decode()
    save_cfg(cfg)
    print("master_key записан в data/config.json")

def help_msg():
    print("Использование:")
    print("  python manage.py set-master   # задать master-пароль (запишет master_key в data/config.json)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        help_msg()
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'set-master':
        set_master()
    else:
        help_msg()
