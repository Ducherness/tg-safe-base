# lib/utils.py
import asyncio
from lib.db import get_conn
from datetime import datetime

async def due_notes_worker(bot):
    await asyncio.sleep(1)
    while True:
        try:
            now = datetime.utcnow()
            conn = get_conn()
            cur = conn.cursor()
            cur.execute('SELECT id, user_id, title, content, due_datetime FROM notes WHERE notified = 0 AND due_datetime IS NOT NULL')
            rows = cur.fetchall()
            for r in rows:
                due = datetime.fromisoformat(r['due_datetime'])
                if due <= now:
                    try:
                        text = f"⏰ Напоминание: <b>{r['title'] or '(без заголовка)'}</b>\n{r['content']}"
                        await bot.send_message(r['user_id'], text)
                        cur.execute('UPDATE notes SET notified = 1 WHERE id = ?', (r['id'],))
                        conn.commit()
                    except Exception:
                        pass
            conn.close()
        except Exception:
            pass
        await asyncio.sleep(30)
