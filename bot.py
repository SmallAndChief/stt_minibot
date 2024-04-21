import logging
import time
import math
from telebot import TeleBot
from telebot.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, MAX_MESSAGE_BLOCKS, MAX_STT_MESSAGES, folder_id
from speechkit import create_iam_token, speech_to_text
from database import create_table, is_limit_users, insert_row, is_limit_messages


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='log_file.txt',
    filemode='a',
)


create_table()
token_data = create_iam_token()
expires_at = time.time() + token_data['expires_in']
iam_token = token_data['access_token']

bot = TeleBot(token=TOKEN)

bot.set_my_commands([BotCommand('start', 'начало работы'),
                     BotCommand('help', 'инструкция'),
                     BotCommand('stt', 'распознование речи')])

help_button = KeyboardButton("/help")
stt_button = KeyboardButton("/stt")


@bot.message_handler(commands=['start'])
def start_message(message):
    logging.info('Отправка приветственного сообщения')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(help_button)
    user_name = message.from_user.first_name
    bot.send_message(chat_id=message.chat.id,
                     text=f'Приветствую вас, {user_name}! Это бот для синтеза речи. Ознакомьтесь с помощь /help.',
                     reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_message(message):
    logging.info('Отправка инструкции')
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(stt_button)
    bot.send_message(chat_id=message.chat.id,
                     text=("Данный бот предоставляет возможности распознования речи.\nЧтобы начать необходимо ввести "
                           "команду /stt, а после отправить голосовое сообщение, которое необходимо обработать.\n"
                           f"Учтите, что длина одного сообщения имеет ограничение в {MAX_MESSAGE_BLOCKS*15} секунд, "
                           f"а всего можно отправить сообщений на распознование {MAX_STT_MESSAGES}."),
                     reply_markup=markup)


@bot.message_handler(commands=['stt'])
def help_message(message):
    logging.info('Введена команда stt')
    user_id = message.from_user.id
    chat_id = message.chat.id
    if is_limit_users():
        bot.send_message(chat_id=chat_id,
                         text="Достигнут лимит пользователей. Вы не сможете воспользоваться ботом.")
        logging.info("Достигнут лимит пользователей")
        return
    if is_limit_messages(user_id=user_id):
        bot.send_message(chat_id=chat_id,
                         text="Достигнут лимит сообщений. Вы не сможете воспользоваться ботом.")
        logging.info("Достигнут лимит пользователей")
        return
    bot.send_message(chat_id=chat_id,
                     text='Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, stt)


def stt(message, expires_at=expires_at, iam_token=iam_token):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if message.content_type != 'voice':
        bot.send_message(user_id, 'Отправь голосовое сообщение')
        logging.warning(f'Неверный тип данных {user_id}')
        bot.register_next_step_handler(message, stt)
        return
    tts_blocks = math.ceil(message.voice.duration / 15)
    if tts_blocks > MAX_MESSAGE_BLOCKS:
        bot.send_message(chat_id=chat_id,
                         text='Превышена длина сообщения. Сократите его и отправьте его снова!')
        logging.warning(f'Превышена длина сообщения {user_id}')
        bot.register_next_step_handler(message, stt)
        return
    if expires_at < time.time():
        token_data = create_iam_token()
        expires_at = time.time() + token_data['expires_in']
        iam_token = token_data['access_token']
        logging.info("смена iam_token")
    file_id = message.voice.file_id
    file_info = bot.get_file(file_id)
    file = bot.download_file(file_info.file_path)
    tts_answer = speech_to_text(data=file, iam_token=iam_token, folder_id=folder_id)
    if tts_answer:
        insert_row((user_id, tts_answer, tts_blocks))
        bot.send_message(chat_id=chat_id, text=tts_answer)
        logging.info(f'Отправка сообщения к {user_id}')
    else:
        bot.send_message(chat_id=message.chat.id,
                         text='Произошла ошибка. Попробуйте повторить чуть позже.')


@bot.message_handler(commands=['debug'])
def debug_message(message):
    with open("log_file.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(content_types=['text', 'voice'])
def text_message(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(help_button)
    bot.send_message(chat_id=message.chat.id,
                     text='Я не понимаю чего вы хотите. Введите /help.',
                     reply_markup=markup)
    logging.info(f'Неизвестная команда от {message.from_user.id}')


bot.infinity_polling()