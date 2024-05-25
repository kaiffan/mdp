from typing import List

from sqlalchemy.orm import Session

from models import User, engine, Calendar

session_database = Session(bind=engine)


def run_func():
    calendars = []
    id_user = session_database.query(User.id).filter_by(telegram_id=12345).scalar()
    calendars = session_database.query(Calendar).filter_by(id_user=1).all()
    print(id_user)
    for calendar in calendars:
        print(f"ID: {calendar.id}, Date: {calendar.calendar_id}, Event: {calendar.calendar_name}")


def get_user_calendars(id_user: int) -> List[Calendar]:
    return session_database.query(Calendar).filter_by(id_user=id_user).all()

if __name__ == '__main__':
    run_func()