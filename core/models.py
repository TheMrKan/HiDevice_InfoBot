from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, Table, ForeignKey


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)


class Controller(Base):
    __tablename__ = "controllers"

    mqtt_user: Mapped[str] = mapped_column(primary_key=True)
    mqtt_password: Mapped[str] = mapped_column()
    notifications: Mapped[int] = mapped_column(server_default="0")


class UserToController(Base):
    __tablename__ = "user_controllers"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    controller_user: Mapped[str] = mapped_column(ForeignKey("controllers.mqtt_user", ondelete="CASCADE"), primary_key=True)





