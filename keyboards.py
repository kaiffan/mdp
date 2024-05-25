from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardMarkup


def registration_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text='Зарегистрироваться в Google Calendar',
        url='https://timeweb.cloud/my'
    )
    return builder.as_markup()


def create_event_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text='Добавить событие с этой датой')
    builder.button(text='Ввести текст с датой заново')
    builder.button(text='Отменить создание события')
    return builder.as_markup()
