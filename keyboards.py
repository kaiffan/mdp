from typing import List
from models import Calendar

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def calendars_list_keyboard(calendars: List[Calendar]) -> InlineKeyboardMarkup:
    """
    Функция создания и заполнения календарями пользователя из Google Calendar
    :param calendars: календари пользователя
    :return: объект InlineKeyboardMarkup для отправки пользователю в сообщении
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    for i in range(0, len(calendars)):
        keyboard.add(InlineKeyboardButton(text=calendars[i].calendar_name, callback_data=f"calendar_{i}"))
    return keyboard


def settings_event_keyboard() -> InlineKeyboardMarkup:
    """
    Функция сборки клавиатуры для подтверждения создания события или для повторного ввода текста
    :return: объект InlineKeyboardMarkup для отправки пользователю в сообщении
    """
    keyboard = InlineKeyboardMarkup()
    done_button: InlineKeyboardButton = InlineKeyboardButton(text="Создать событие с этой датой",
                                                             callback_data='button_done')
    edit_button: InlineKeyboardButton = InlineKeyboardButton(text="Изменить дату",
                                                             callback_data='button_edit')
    return keyboard.add(done_button, edit_button)


def auth_google_keyboard(registration_url: str) -> InlineKeyboardMarkup:
    """
    Функция сборки клавиатуры для регистрации в Google API
    :param registration_url: ссылка для регистрации в Google Calendar API
    :return: объект InlineKeyboardMarkup для отправки пользователю в сообщении
    """
    keyboard = InlineKeyboardMarkup()
    registration_button: InlineKeyboardButton = InlineKeyboardButton(text="Регистрация в Google API",
                                                                     url=registration_url)
    return keyboard.add(registration_button)
