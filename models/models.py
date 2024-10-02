import re
import sqlite3

from loguru import logger
from telethon import TelegramClient


def remove_digits_from_url(url):
    # Регулярное выражение для замены цифр в конце ссылки
    cleaned_url = re.sub(r'/\d+$', '', url)
    return cleaned_url


async def connect_session_to_telegram_account(username_messages):

    api_id = 12345
    api_hash = '0123456789abcdef0123456789abcdef'
    session_names = 'session_name'
    try:
        async with TelegramClient(f'setting/account/{session_names}', api_id, api_hash) as client:
            await client.connect()
            logger.info(f'Подключено к аккаунту Telegram с именем сеанса {session_names}')

            try:
                username = await client.get_entity(f'{username_messages}')
                logger.info(f"ID группы {username_messages}: {username.id}")
                username_id = username.id if username else None
                await client.disconnect()  # Отключение от аккаунта Telegram
                return username_id

            except ValueError:
                cleaned_url = remove_digits_from_url(username_messages)
                try:
                    username = await client.get_entity(cleaned_url)
                    logger.info(f"ID группы {cleaned_url}: {username.id}")
                    username_id = username.id if username else None
                    await client.disconnect()
                    return username_id
                except ValueError:
                    logger.error(f'Невозможно получить ID группы для {cleaned_url}')
                    await client.disconnect()
                    # continue

    except sqlite3.OperationalError:
        logger.error(f'База данных заблокирована для аккаунта {session_names}. Пробую следующий...')
        return

    except Exception as e:
        logger.error(f'Ошибка при подключении к аккаунту Telegram: {e}')
        await client.disconnect()  # Отключение от аккаунта Telegram
        return

    # logger.error('Не удалось подключиться ни к одному из аккаунтов Telegram')
    # return None
