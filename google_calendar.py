from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from keyboards import auth_google_keyboard  # предполагается, что вы определили это где-то
from models import User, engine, Calendar
from aioauth_client import GoogleClient
from sqlalchemy.orm import Session
from aiohttp import ClientSession
from dotenv import load_dotenv
from typing import List, Dict
from asyncio import run
from json import load
from os import getenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
session_database = Session(bind=engine)
telegram_cred = {}


def get_credentials_info(name_credentials_file: str) -> dict:
    """
    Загрузка учетных данных Google API из файла JSON.

    Args:
        name_credentials_file (str): имя файла JSON, содержащего учетные данные.

    Returns:
        dict: словарь с учетными данными Google API.
    """
    with open(name_credentials_file, 'r') as credentials_file:
        cred_data = load(credentials_file)
        return cred_data['web']


async def get_authorization_code():
    """
    Асинхронное получение кода авторизации.

    Returns:
        str: код авторизации, полученный от сервера.
    """
    authorization_code = None
    while not authorization_code:
        async with ClientSession() as session:
            async with session.get(getenv('REDIRECT_URI')) as response:
                if response.status == 200:
                    authorization_code = await response.text()
                    break
    return authorization_code


def get_google_client(installed_data: Dict) -> GoogleClient:
    """
    Создание и возврат объекта GoogleClient.

    Args:
        installed_data (Dict): словарь с установленными данными.

    Returns:
        GoogleClient: экземпляр GoogleClient.
    """
    return GoogleClient(
        client_id=installed_data['client_id'],
        client_secret=installed_data['client_secret'],
        redirect_uri=getenv('REDIRECT_URI'),
        scope=SCOPES[0]
    )


def authenticate_google_calendar(telegram_id: int, bot, message):
    """
    Аутентификация пользователя в Google Календаре.

    Args:
        telegram_id (int): ID пользователя в Telegram.
        bot: экземпляр бота Telegram.
        message: объект сообщения, полученный от пользователя.

    Returns:
        Resource: ресурс Google Календаря API.
    """
    installed_data: Dict = get_credentials_info(getenv('CREDENTIALS_FILE'))

    client = get_google_client(installed_data)
    auth_link = client.get_authorize_url()
    auth_keyboard = auth_google_keyboard(auth_link)
    bot.send_message(message.chat.id, "Ссылка для регистрации в Google API", reply_markup=auth_keyboard)

    if not auth_link.startswith('https://'):
        raise ValueError("authorization_url должен начинаться с https://")

    access_token = session_database.query(User).filter_by(telegram_id=telegram_id).first()
    if not access_token:
        authorization_code = run(get_authorization_code())
        access_token, expires_in = run(client.get_access_token(code=authorization_code))
        user: User = User(telegram_id=telegram_id, access_token=access_token)
        session_database.add(user)
        session_database.commit()
    bot.send_message(message.chat.id, "Успешная регистрация в Google API")
    credentials = Credentials(access_token)
    telegram_cred.update({message.from_user.id: credentials})
    return build('calendar', 'v3', credentials=credentials)


def get_all_calendars_user(telegram_id: int, bot, message) -> List[Calendar]:
    """
    Получение всех календарей, связанных с пользователем.

    Args:
        telegram_id (int): ID пользователя в Telegram.
        bot: экземпляр бота Telegram.
        message: объект сообщения, полученный от пользователя.

    Returns:
        List[Calendar]: Список объектов календаря.
    """
    service = get_service_google_calendar(telegram_id, bot, message)

    id_user = session_database.query(User.id).filter_by(telegram_id=telegram_id).scalar()
    user_calendars_type_list = session_database.query(Calendar).filter_by(id_user=id_user).all()
    user_calendars = [Calendar(
        calendar_id=calendar.calendar_id,
        calendar_name=calendar.calendar_name,
        id_user=calendar.id_user)
        for calendar in user_calendars_type_list]

    if not user_calendars:
        calendars = service.calendarList().list().execute()
        for calendar in calendars.get('items', []):
            calendar_row: Calendar = Calendar(
                calendar_id=calendar['id'],
                calendar_name=calendar['summary'],
                id_user=id_user
            )
            user_calendars.append(calendar_row)
        session_database.add_all(user_calendars)
        session_database.commit()
    return user_calendars


def get_service_google_calendar(telegram_id, bot, message):
    """
    Получение сервиса Google Календаря.

    Args:
        telegram_id: ID пользователя в Telegram.
        bot: экземпляр бота Telegram.
        message: объект сообщения, полученный от пользователя.

    Returns:
        Resource: ресурс Google Календаря API.
    """
    access_token = session_database.query(User).filter_by(telegram_id=telegram_id).first()
    if not access_token:
        return authenticate_google_calendar(telegram_id=telegram_id, bot=bot, message=message)
    return build(
        serviceName='calendar',
        version='v3',
        credentials=telegram_cred.get(message.from_user.id)
    )


def get_calendar_id(telegram_id: int, calendar_name: str) -> str:
    """
        Получает идентификатор календаря по имени календаря и ID пользователя в Telegram.

        Args:
            telegram_id: ID пользователя в Telegram.
            calendar_name: имя календаря.

        Returns:
            str: идентификатор календаря.
        """
    id_user = session_database.query(User).filter_by(telegram_id=telegram_id).first().id
    return session_database.query(Calendar).filter_by(id_user=id_user,
                                                      calendar_name=calendar_name).first().calendar_id


def create_event_to_calendar(
        calendar_id: str,
        summary: str,
        description: str,
        date_start_iso: str,
        date_end_iso: str,
        telegram_id: int,
        bot, message) -> None:
    """
    Создает событие в календаре.

    Args:
        calendar_id (str): идентификатор календаря, в котором нужно создать событие.
        summary (str): краткое описание события.
        description (str): подробное описание события.
        date_start_iso (str): дата и время начала события в формате ISO 8601.
        date_end_iso (str): дата и время окончания события в формате ISO 8601.
        telegram_id (int): ID пользователя в Telegram.
        bot: экземпляр бота Telegram.
        message: объект сообщения, полученный от пользователя.

    Returns:
        None
    """
    service = get_service_google_calendar(telegram_id, bot, message)

    service.events().insert(
        calendarId=calendar_id,
        body={
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": date_start_iso,
                "timeZone": 'Europe/Moscow'
            },
            "end": {
                "dateTime": date_end_iso,
                "timeZone": 'Europe/Moscow'
            }
        }).execute()
    bot.send_message(message.chat.id, "Событие создано")
