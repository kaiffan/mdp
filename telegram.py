from datetime import datetime, timedelta
import os

import telebot
from telebot.types import Message, CallbackQuery
from google_calendar import get_all_calendars_user, get_calendar_id, create_event_to_calendar
from keyboards import calendars_list_keyboard, settings_event_keyboard
from rutimeparser import parse
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TOKEN'))
selected_calendars = {}
text_without_date = []
match_name_to_callback = {}


@bot.message_handler(commands=['start'])
def start_handler(message: Message) -> None:
    """
        Обработчик для приветственного сообщения пользователю
    """
    bot.send_message(message.chat.id, "Привет! Тебя приветствует бот по созданию событий, "
                                      "основываясь на введённом тобой тексте.")


@bot.message_handler(commands=['help'])
def help_handler(message: Message):
    """
        Обработчик для справки о командах бота
    """
    bot.send_message(message.chat.id,
                     "Команды бота: "
                     "\n/start - запуск бота"
                     "\n/help - справка по командам"
                     "\n/choose_calendar - выбор гугл календаря для создания в нем событий"
                     "\n/add_text_with_date - написать текст в дальнейшем из которого будет получена дата для создания события"
                     "\n/create_event - создание события в гугл календаре по текстовому описанию \n")


@bot.message_handler(commands=["choose_calendar"])
def choose_calendar_handler(message: Message):
    """
        Обработчик для выбора календаря пользователем через кнопки inline клавиатуры
    """
    calendar_list_user = get_all_calendars_user(telegram_id=message.from_user.id, bot=bot, message=message)
    for i in range(0, len(calendar_list_user)):
        match_name_to_callback.update({f"calendar_{i}": calendar_list_user[i].calendar_name})
    print(match_name_to_callback)
    inline_kb = calendars_list_keyboard(calendars=calendar_list_user)
    bot.send_message(message.chat.id, "Выберите элемент:", reply_markup=inline_kb)


@bot.callback_query_handler(func=lambda calendar: calendar.data.startswith('calendar_'))
def choose_calendar_callback(callback: CallbackQuery):
    """
        Обработчик кнопок inline клавиатуры
    """
    choose_calendar_user = match_name_to_callback.get(callback.data)
    selected_calendars.update({callback.from_user.id: choose_calendar_user})
    bot.answer_callback_query(callback.id, "Календарь выбран")
    bot.send_message(callback.message.chat.id, f"Календарь {choose_calendar_user} успешно выбран")
    match_name_to_callback.clear()


@bot.message_handler(commands=["add_text_with_date"])
def add_text_with_date_handler(message: Message):
    """
        Обработчик для ввода текста с датой пользователем
    """
    bot.send_message(message.chat.id, "Введите текст с использованием даты:")
    bot.register_next_step_handler(message, registrate_message_with_date)


def registrate_message_with_date(message: Message):
    """
        Функция получение текста с датой от пользователя
    """
    keyboard = settings_event_keyboard()
    date_in_text = parse(message.text)
    if not date_in_text:
        bot.send_message(message.chat.id, "В вашем сообщении нет даты. Введите новый текст")
        add_text_with_date_handler(message)
    text_without_date.append([message.text, date_in_text, message.from_user.id])
    bot.send_message(message.chat.id, f"Хотите ли создать событие с этой датой?\n{date_in_text}", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda button: button.data.startswith('button_'))
def add_text_with_date_callback(callback: CallbackQuery):
    """
        Регистрация callback от обработчика dd_text_with_date_handler
    """
    if callback.data == "button_done":
        bot.answer_callback_query(callback.id, "Создаём с этой датой")
        bot.send_message(callback.message.chat.id,
                         f"Дата сохранена.\nВведите /create_event для создания события с этой датой")
        # вызов handler создания события
    elif callback.data == "button_edit":
        for element in text_without_date:
            if element[2] == callback.message.chat.id:
                add_text_with_date_handler(callback.message)
                text_without_date.remove(element)
        bot.answer_callback_query(callback.id, "Будем редактировать")


@bot.message_handler(commands=['create_event'])
def create_event_handler(message: Message):
    """
        Обработчик для создания события
    """
    print(message.text)
    select_calendar = selected_calendars.get(message.from_user.id)
    if not select_calendar:
        choose_calendar_handler(message)
        return
    date_start = datetime.now()
    for element in text_without_date:
        if element[2] == message.from_user.id:
            date_start = element[1]
    date_end: datetime = date_start + timedelta(hours=1)
    print(date_end)
    calendar_id = get_calendar_id(telegram_id=message.from_user.id, calendar_name=select_calendar)
    print(calendar_id)
    create_event_to_calendar(calendar_id=calendar_id,
                             summary="Событие",
                             description="Тестовое описание",
                             date_start_iso=date_start.isoformat(),
                             date_end_iso=date_end.isoformat(),
                             telegram_id=message.from_user.id,
                             bot=bot,
                             message=message)
    # удалять пользователя токен на 1 сессию


@bot.message_handler(func=lambda message: True)
def handle_invalid_commands(message):
    bot.send_message(message.chat.id, "Команда не распознана. Пожалуйста, используйте корректную команду.")


def main():
    bot.polling(none_stop=True)


if __name__ == "__main__":
    main()
