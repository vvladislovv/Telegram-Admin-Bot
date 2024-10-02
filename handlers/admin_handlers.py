import sqlite3

from aiogram import types
from aiogram.filters import Command
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from loguru import logger

from system.dispatcher import bot
from system.dispatcher import dp  # Подключение к боту и диспетчеру пользователя


def checking_for_presence_in_the_user_database(user_id):
    conn = sqlite3.connect('setting/database.db')  # Инициализация базы данных SQLite
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY)')
    cursor.execute('SELECT id FROM groups WHERE id = ?', (user_id,))  # Проверка наличия ID в базе данных
    result = cursor.fetchone()
    return result


@dp.message(Command('id'))
async def process_id_command(message: types.Message):
    """Обработчик команды /id"""
    user_id = message.from_user.id  # Получаем ID пользователя
    if message.from_user.id not in [535185511, 7181118530, 6329028511]:
        await message.reply('У вас нет доступа к этой команде.')
        return
    logger.info(f'Админ {user_id} написал сообщение {message.text}')
    try:
        user_id = int(message.text.split()[1])
        result = checking_for_presence_in_the_user_database(user_id)  # Запись ID в базу данных
        if result is None:
            conn = sqlite3.connect('setting/database.db')  # Инициализация базы данных SQLite
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY)')
            cursor.execute('INSERT INTO groups (id) VALUES (?)', (user_id,))
            conn.commit()
            await message.reply(f"ID {user_id} успешно записан в базу данных.")
        else:
            await message.reply(f"ID {user_id} уже существует в базе данных.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду /id followed by ваш ID.")
    except Exception as error:
        logger.exception(error)

@dp.message(Command('del'))
async def process_id_command(message: types.Message):
    """Обработчик команды /id"""
    user_id = message.from_user.id  # Получаем ID пользователя
    if message.from_user.id not in [535185511, 7181118530, 6329028511]:
        await message.reply('У вас нет доступа к этой команде.')
        return
    logger.info(f'Админ {user_id} написал сообщение {message.text}')
    conn = sqlite3.connect('setting/database.db')  # Инициализация базы данных SQLite
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM links")
    conn.commit()
    conn.close()  # cursor_members.close() – закрытие соединения с БД.
    await message.reply(f"ID {user_id} уже существует в базе данных.")

# Создаем состояние для ввода URL
class URLForm(StatesGroup):
    url = State()

@dp.message(Command('url_add'))
async def process_url_command(message: types.Message, state: FSMContext):
    """Обработчик команды /url_add"""
    user_id = message.from_user.id  # Получаем ID пользователя
    if user_id not in [535185511, 7181118530, 6329028511]:
        await message.reply('У вас нет доступа к этой команде.')
        return
    logger.info(f'Админ {user_id} написал сообщение {message.text}')
    await message.reply("Пожалуйста, введите URL для добавления:")
    await state.set_state(URLForm.url)# Устанавливаем состояние ожидания URL

@dp.message(URLForm.url)
async def process_url_input(message: types.Message, state: FSMContext):
    """Обработчик ввода URL"""
    user_id = message.from_user.id
    url = message.text.strip()

    try:
        # Проверяем наличие URL в базе данных
        result = checking_for_presence_in_the_user_database(url)
        if result is None:
            conn = sqlite3.connect('setting/database.db')  # Инициализация базы данных SQLite
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS url (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT)')
            cursor.execute('INSERT INTO url (url) VALUES (?)', (url,))
            conn.commit()
            await message.reply(f"URL '{url}' успешно записан в базу данных.")
        else:
            await message.reply(f"URL '{url}' уже существует в базе данных.")
    except Exception as error:
        logger.exception(error)
        await message.reply("Произошла ошибка при добавлении URL.")
    finally:
        await state.clear()  # Завершаем состояние

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    # Если пользователя нет в базе данных, предлагаем пройти регистрацию
    sign_up_text = (
        "⚠️ Бот для администрирования групп ⚠️\n\n"
    )
    # Отправляем сообщение с предложением зарегистрироваться и клавиатурой
    await bot.send_message(message.from_user.id, sign_up_text,
                           disable_web_page_preview=True)



def greeting_handler():
    dp.message.register(process_id_command)
    dp.message.register(process_url_command)
    dp.message.register(command_start_handler)
