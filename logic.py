import sqlite3
import telebot
from config import TOKEN

bot = telebot.TeleBot(TOKEN)
INFO_BASE = "info.db"

# Инициализация базы данных при запуске
with sqlite3.connect(INFO_BASE) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            info TEXT
        )
    """)
    conn.commit()


def is_admin(chat_id, user_id):
    admins = bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)


@bot.message_handler(commands=["help", "start"])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я - бот для чата от @pocketgamer74."
    " Команды:"
    " /ban, /unban - бан, разбан"
    " /setInfo - создать информацию про себя"
    " /info - показать/прочитать чтью-то информацию")


@bot.message_handler(commands=["ban"])
def ban_user(message):
    if not message.reply_to_message:
        bot.reply_to(
            message,
            "Эта команда должна быть ответом на сообщение пользователя.",
        )
        return

    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Нужны права админа!")
        return

    user_id = message.reply_to_message.from_user.id
    try:
        bot.ban_chat_member(message.chat.id, user_id)
        bot.reply_to(message, "Пользователь забанен!")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=["unban"])
def unban_user(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "Нужны права админа!")
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Использование: /unban USER_ID (только цифры)")
        return

    user_id = int(args[1])
    try:
        bot.unban_chat_member(message.chat.id, user_id, only_if_banned=True)
        bot.reply_to(message, "Пользователь разбанен!")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")


@bot.message_handler(commands=["setInfo", "setinfo"])
def set_info(message):
    parts = message.text.split(maxsplit=1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        bot.reply_to(
            message,
            "Укажите текст после команды. Пример: /setInfo Люблю программировать",
        )
        return

    with sqlite3.connect(INFO_BASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, info) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, text),
        )
        conn.commit()

    bot.reply_to(message, "Информация сохранена!")


@bot.message_handler(commands=["info"])
def get_info(message):
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    else:
        target_id = message.from_user.id

    with sqlite3.connect(INFO_BASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()

    if user:
        username_display = f"@{user[1]}" if user[1] else "отсутствует"
        bot.reply_to(
            message,
            f"ID: {user[0]}\nUsername: {username_display}\nСообщение: {user[2]}",
        )
    else:
        bot.reply_to(message, "Пользователя нет в базе данных!")


if __name__ == "__main__":
    bot.infinity_polling(timeout=30, long_polling_timeout=30, skip_pending=True)