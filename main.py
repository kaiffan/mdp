from aiogram import Bot, Dispatcher, html, F
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from keyboards import registration_keyboard
from dotenv import load_dotenv
from os import getenv

import asyncio

load_dotenv()

bot = Bot(token=getenv('TOKEN'))
dp = Dispatcher()


class MyCallback(CallbackData, prefix="my"):
    foo: str
    bar: int


@dp.message(Command("start"))
async def command_start(message: Message) -> None:
    await message.answer('Hello!')  # добавить сообщение приветствия


@dp.message(Command("help"))
async def command_help(message: Message) -> None:
    await message.answer("Команды бота: ")  # добавить описание команд бота


@dp.message(Command('registration'))
async def command_help(message: Message) -> None:
    await message.answer("Регистрация в гугл календаре: ", reply_markup=registration_keyboard())  # добавить описание


@dp.message(Command("create_event"))
async def command_create_event(message: Message) -> None:
    await message.answer("Процесс создания бота...")


@dp.callback_query(MyCallback.filter(F.foo == "demo"))
async def my_callback_foo(query: CallbackQuery, callback_data: MyCallback):
    await query.message.answer(f'Кнопка нажата {callback_data}')


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
