from dotenv import dotenv_values
import openai
import sqlite3
import telebot
from requests.exceptions import ReadTimeout

env = {
    **dotenv_values(".env.prod"),
    **dotenv_values(".env.dev"),  # override
}

openai.api_key = env["API_KEY_CHATGPT"]
bot = telebot.TeleBot(env["TG_BOT_TOKEN"])
db_link = env["DB_LINK"]


def write_to_db(message):
    conn = sqlite3.connect(db_link)
    cursor = conn.cursor()
    select_id = cursor.execute(
        "SELECT id FROM user WHERE chat_id = ?", (str(message.chat.id),)
    )
    select_id = select_id.fetchone()
    if select_id:
        try:
            cursor.execute(
                "UPDATE user SET last_msg=?, last_login=? WHERE chat_id=?",
                (
                    message.text,
                    str(message.date),
                    str(message.chat.id),
                ),
            )
        except:
            conn.commit()
            cursor.close()
            bot.send_message(
                612063160,
                f"Ошибка при добавлении (INSERT) данных в базе Пользователь: {message.chat.id}",
            )
    else:
        try:
            cursor.execute(
                "INSERT INTO user (chat_id, last_login, username, first_name, last_name, last_msg) VALUES (?,?,?,?,?,?)",
                (
                    str(message.chat.id),
                    str(message.date),
                    message.chat.username if message.chat.username else "-",
                    message.chat.first_name
                    if message.chat.first_name
                    else "-",
                    message.chat.last_name if message.chat.last_name else "-",
                    message.text,
                ),
            )
        except:
            conn.commit()
            cursor.close()
            bot.send_message(
                612063160,
                f"Ошибка при добавлении (INSERT) данных в базе Пользователь: {message.chat.id}",
            )
    conn.commit()
    cursor.close()


@bot.message_handler(commands=["start"])
def send_start(message):
    text = """Приветствую ✌

Я - ChatGPT, крупнейшая языковая модель, созданная OpenAI. 

Я разработана для обработки естественного языка и могу помочь вам ответить на вопросы, 
обсудить темы или предоставить информацию на различные темы.

🔥В том числе на русском языке....🔥

👇Я постараюсь ответить на твои вопросы👇
"""
    write_to_db(message)
    bot.send_message(message.chat.id, text)


@bot.message_handler(content_types=["text"])
def send_msg_to_chatgpt(message):
    engine = "text-davinci-003"
    write_to_db(message)
    try:
        completion = openai.Completion.create(
            engine=engine,
            prompt=message.text,
            temperature=0.5,
            max_tokens=1000,
        )
        bot.send_message(message.chat.id, completion.choices[0]["text"])
    except openai.error.RateLimitError:
        bot.send_message(
            message.chat.id,
            "ChatGPT в данный момент перегружен запросами, пожалуйста повторите свой запрос чуть позже.",
        )
    except ReadTimeout:
        bot.send_message(
            message.chat.id,
            "ChatGPT в данный момент перегружен запросами, пожалуйста повторите свой запрос чуть позже.",
        )


if __name__ == "__main__":
    target = bot.infinity_polling()
