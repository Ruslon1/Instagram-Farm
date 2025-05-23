import asyncio
from telegram import Bot

def telegram_notify(token, chat_id, message):
    asyncio.run(notify(token, chat_id, message))

async def notify(token, chat_id, message):
    try:
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message)
    except Exception as e:
        print(f"Telegram notification error: {e}")
