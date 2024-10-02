import re
import sqlite3

from aiogram import F
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatPermissions
from loguru import logger

from models.models import connect_session_to_telegram_account
from system.dispatcher import bot, dp, allowed_user_ids

phone_number_pattern = re.compile(r'(\+?\d{1,3}[-\s]?\d{3,4}[-\s]?\d{2,4}[-\s]?\d{2,4})')

async def read_database():
    """Чтение с базы данных"""
    connection = sqlite3.connect('setting/database.db')  # Подключение к базе данных
    cursor = connection.cursor()  # Подключение к таблице
    cursor.execute('SELECT * FROM groups')  # Выполнение запроса
    users = cursor.fetchall()  # Выполнение запроса
    cursor.close()  # Закрытие подключения
    connection.close()  # Закрытие подключения
    return users


async def write_to_database(link):
    try:
        # Подключение к базе данных (создаст файл базы данных, если он не существует)
        conn = sqlite3.connect('setting/database.db')
        cursor = conn.cursor()
        # Создание таблицы, если она не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT NOT NULL UNIQUE,
                added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Проверка на наличие дубликата
        cursor.execute('SELECT COUNT(1) FROM links WHERE link = ?', (link,))
        if cursor.fetchone()[0] > 0:
            logger.info(f"Ссылка '{link}' уже существует в базе данных. Запись не требуется.")
            return
        # Вставка новой записи в таблицу
        cursor.execute('INSERT INTO links (link) VALUES (?)', (link,))
        # Сохранение изменений
        conn.commit()
        logger.info(f"Ссылка '{link}' успешно добавлена в базу данных.")
    except sqlite3.Error as error:
        logger.error(f"Ошибка при работе с базой данных: {error}")
    finally:
        # Закрытие соединения с базой данных
        conn.close()


@dp.message(F.text)
async def any_message(message: types.Message, state: FSMContext):
    """
    Проверка сообщения на наличие ссылок: если ссылка в сообщении есть, то удаляем сообщение и предупреждаем пользователя.
    """
    await state.clear()  # Завершаем состояние
    logger.info(f'Проверяем сообщение {message.text} от {message.from_user.username} {message.from_user.id}. Текст сообщения: {message.text}')

    if message.entities:  # Проверяем, есть ли сущности в сообщении
        for entity in message.entities:  # Проверка на наличие ссылок
            if entity.type in ["url", "text_link", "mention"]:
                link = message.text[
                       entity.offset:entity.offset + entity.length] if entity.type != "text_link" else entity.url
                logger.info(f"Тип ссылки: {entity.type}. Ссылка ({entity.type}) в сообщении 🔗: {link}")

                # Проверка на наличие ссылки в таблице links
                conn = sqlite3.connect('setting/database.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(1) FROM links WHERE link = ?', (link,))
                link_exists = cursor.fetchone()[0] > 0

                # Проверка на наличие ссылки в таблице url
                cursor.execute('CREATE TABLE IF NOT EXISTS url (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT)')
                cursor.execute('SELECT COUNT(1) FROM url WHERE url = ?', (link,))
                url_exists = cursor.fetchone()[0] > 0
                conn.close()

                # Если ссылка найдена в базе данных url, то блокируем пользователя
                if url_exists:
                    logger.info(f"Ссылка '{link}' найдена в таблице url. Блокируем пользователя.")
                    user_id = message.from_user.id
                    permissions = ChatPermissions(can_send_messages=False)
                    await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id, permissions=permissions)
                    await message.delete()  # Удаляем сообщение содержащее ссылку
                    return  # Переход к следующей ссылке, если она найдена в базе данных

                if link_exists:
                    logger.info(f"Ссылка '{link}' найдена в таблице links. Проверка по ID не требуется.")
                    return  # Переход к следующей ссылке, если она найдена в базе данных

                logger.info(f"Ссылка '{link}' не найдена в базе данных. Продолжаем проверку по ID.")

                username_id = await connect_session_to_telegram_account(link)

                if message.from_user.id not in allowed_user_ids:
                    logger.info(f'ID группы {link}: {username_id}')
                    users = await read_database()
                    user_found = False
                    for user in users:
                        logger.info(f'ID из базы данных: {user[0]}')
                        if username_id == user[0]:
                            user_found = True
                            user_id = message.from_user.id
                            permissions = ChatPermissions(can_send_messages=False)
                            await bot.restrict_chat_member(chat_id=message.chat.id, user_id=user_id,
                                                           permissions=permissions)
                            logger.info(f'Сообщение от:({message.from_user.username} '
                                        f'{message.from_user.id}). Текст сообщения {message.text}')
                            await message.delete()  # Удаляем сообщение содержащее ссылку
                    if not user_found:
                        logger.info(
                            f'ID группы {link}: {username_id} не найдено в базе данных. Записываем ссылку в базу данных.')
                        await write_to_database(link)  # Запись ссылки в базу данных


def register_greeting_handler():
    """Регистрируем handlers для бота"""
    dp.message.register(any_message)
