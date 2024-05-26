from telebot.handler_backends import State, StatesGroup


class TextWaitState(StatesGroup):
    WaitingTextEvent = State()
    WaitingSummaryEvent = State()