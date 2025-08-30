# main.py
import os
import asyncio
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)
LOG_LEVEL = logging.INFO

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise SystemExit('Set BOT_TOKEN environment variable')

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

import handlers as _handlers
for r in getattr(_handlers, 'HANDLERS_ROUTERS', []):
    dp.include_router(r)

from lib.utils import due_notes_worker

async def main():
    logger.info('Starting bot...')
    asyncio.create_task(due_notes_worker(bot))
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Stopped')
