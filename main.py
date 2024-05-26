from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, html, F
from aiogram.fsm.context import FSMContext
from logging import basicConfig, INFO
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from state import TextWaitState
from dotenv import load_dotenv
from asyncio import run
from os import getenv
from keyboards import calendars_list_keyboard
from google_calendar import get_all_calendars_user

basicConfig(level=INFO)
load_dotenv()

bot = Bot(token=getenv('TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
list_text = []
selected_items = []


@dp.message(Command("start"))
async def command_start(message: Message) -> None:
    await message.answer('Привет! Тебя приветствует бот по созданию событий, '
                         'основываясь на введённом тобой тексте.')


@dp.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer(
        "Команды бота: "
        "\n/start - запуск бота "
        "\n/help - справка по командам "
        "\n/registration - предоставление доступа боту к Google Calendar API"
        "\n/create_event - создание события в гугл календаре по текстовому описанию \n")


@dp.message(Command("create_event"))
async def command_create_event(message: Message) -> None:
    await message.answer("")


@dp.message(Command("add_text_with_date"))
async def command_add_text_with_date(message: Message, state: FSMContext) -> None:
    await state.set_state(TextWaitState.WaitingTextEvent)
    await message.reply("Введите текст с датой для создания события")


@dp.message(TextWaitState.WaitingTextEvent)
async def wait_text_event(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    list_text.append([message.from_user.id, message.text])
    print(*[message.from_user.id, message.text])
    await message.reply("Ваш текст принят для обработки")
    await state.clear()


@dp.message(Command("choose_calendar"))
async def command_choose_calendar(message: Message) -> None:
    print(f"Telegram_id {message.from_user.id}")
    calendar_list_user = get_all_calendars_user(message.from_user.id)
    inline_kb = calendars_list_keyboard(calendars=calendar_list_user)
    await message.answer("Выберите элемент:", reply_markup=inline_kb)


@dp.message()
async def handle_unexpected_message(message: Message):
    await message.reply("Некорректная команда")


@dp.callback_query(lambda calendar: calendar.data.startswith('calendar_'))
async def calendar_choose_calendar(callback_query: CallbackQuery):
    calendar_id = callback_query.data.split('_')[1]
    selected_items.append(calendar_id)

    await bot.answer_callback_query(callback_query.id, text=f"Вы выбрали элемент {calendar_id}")
    await bot.send_message(callback_query.from_user.id,
                           f"Элемент {calendar_id} добавлен в список. Текущий список: {', '.join(selected_items)}")


async def main() -> None:
    await dp.start_polling(bot)


def get_bot() -> Bot:
    return bot


if __name__ == "__main__":
    run(main())
