from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Column, Table, ForeignKey


Base = declarative_base()


user_to_controller_table = Table(
    "user_controllers",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("controller_user", ForeignKey("controllers.mqtt_user", ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    controllers: Mapped[list["Controller"]] = relationship(secondary=user_to_controller_table, back_populates="users", lazy="joined")

    def __init__(self, id: int):
        self.id = id
        self.controllers = []


class Controller(Base):
    __tablename__ = "controllers"

    mqtt_user: Mapped[str] = mapped_column(primary_key=True)
    mqtt_password: Mapped[str] = mapped_column()
    users: Mapped[list["User"]] = relationship(secondary=user_to_controller_table, back_populates="controllers", lazy="joined")





