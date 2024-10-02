import asyncio

from handlers.admin_handlers import greeting_handler
from handlers.handlers import register_greeting_handler
from system.dispatcher import dp, bot


async def main() -> None:
    """Запуск бота https://t.me/Newwwbotik_bot"""
    await dp.start_polling(bot, skip_updates=True)
    greeting_handler()  # Запись id группы админом
    register_greeting_handler()


if __name__ == '__main__':
    asyncio.run(main())
