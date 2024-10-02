import configparser

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage

config = configparser.ConfigParser(empty_lines_in_values=False, allow_no_value=True)
config.read("setting/config.ini")  # Чтение файла
BOT_TOKEN = config["BOT_TOKEN"]["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN,)
storage = MemoryStorage()  # Хранилище
dp = Dispatcher(storage=storage)

# allowed_user_ids = [53518551] # ID администраторов бота
allowed_user_ids = [53518551, 7181118530, 6329028511]  # ID администраторов бота

router = Router()
dp.include_router(router)
