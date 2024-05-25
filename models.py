from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine, String, ForeignKey, Column, Integer

engine = create_engine(url="postgresql://postgres:postgres@localhost:5433/mdp")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(nullable=True, unique=True)
    access_token: Mapped[str] = mapped_column(String(255), nullable=False)


class Calendar(Base):
    __tablename__ = "calendars"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    calendar_id: Mapped[str] = mapped_column(String(255), nullable=False)
    calendar_name: Mapped[str] = mapped_column(String(255), nullable=False)
    id_user = Column(Integer, ForeignKey("users.id"))


Base.metadata.create_all(bind=engine)
