from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
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


def get_credentials_info(name_credentials_file: str) -> dict:
    with open(name_credentials_file, 'r') as credentials_file:
        cred_data = load(credentials_file)
        return cred_data['web']


async def get_authorization_code():
    authorization_code = None
    while not authorization_code:
        async with ClientSession() as session:
            async with session.get(getenv('REDIRECT_URI')) as response:
                if response.status == 200:
                    authorization_code = await response.text()
                    break
    return authorization_code


def get_google_client(installed_data: Dict) -> GoogleClient:
    return GoogleClient(
        client_id=installed_data['client_id'],
        client_secret=installed_data['client_secret'],
        redirect_uri=getenv('REDIRECT_URI'),
        scope=SCOPES[0]
    )


def authenticate_google_calendar(telegram_id: int):
    installed_data: Dict = get_credentials_info(getenv('CREDENTIALS_FILE'))

    client = get_google_client(installed_data)
    authorization_url = client.get_authorize_url()
    print(authorization_url)

    # todo: прописать логику отправки ботом сообщения со ссылкой регистрации

    if not authorization_url.startswith('https://'):
        raise ValueError("authorization_url должен начинаться с https://")

    access_token = session_database.query(User).filter_by(telegram_id=telegram_id).first()
    if not access_token:
        authorization_code = run(get_authorization_code())
        access_token, expires_in = run(client.get_access_token(code=authorization_code))
        user: User = User(telegram_id=telegram_id, access_token=access_token)
        session_database.add(user)
        session_database.commit()

    credentials = Credentials(access_token)
    return build('calendar', 'v3', credentials=credentials)


def get_all_calendars_user(telegram_id: int) -> List[Calendar]:
    service = get_service_google_calendar(telegram_id)

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


def get_service_google_calendar(telegram_id):
    access_token = session_database.query(User).filter_by(telegram_id=telegram_id).first()
    if not access_token:
        return authenticate_google_calendar(telegram_id=telegram_id)
    return build(
        serviceName='calendar',
        version='v3',
        credentials=Credentials(access_token)
    )


def create_event_to_calendar(
        calendar_id: str,
        summary: str,
        description: str,
        date_start_iso: str,
        date_end_iso: str,
        telegram_id: int) -> None:
    service = get_service_google_calendar(telegram_id)

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
        }
    ).execute()


if __name__ == '__main__':
    print(get_all_calendars_user(12344))
