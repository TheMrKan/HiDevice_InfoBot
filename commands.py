from aiogram import Router, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ErrorEvent
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import traceback

from core.models import User
from core import controllers, users


router = Router(name="commands")


@router.error()
async def error_handler(event: ErrorEvent):
    traceback.print_exception(event.exception)
    if event.update.message:
        await event.update.message.answer("Во время обработки произошла непредвиденная ошибка")


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет!")


class AddControllerForm(StatesGroup):
    controller_name = State()
    controller_password = State()


@router.message(Command("add_controller"))
async def cmd_add_controller(message: Message, state: FSMContext):
    await state.set_state(AddControllerForm.controller_name)
    await message.answer(f"{html.bold("Добавление контроллера")}\n\nИмя пользователя MQTT:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text="Отменить")],
                             ]
                         ))


@router.message(F.text.casefold() == "отменить")
async def cmd_add_controller_cancel(message: Message, state: FSMContext):
    if state is None:
        return
    await state.clear()
    await message.answer("Добавление отменено",
                         reply_markup=ReplyKeyboardRemove())


@router.message(AddControllerForm.controller_name)
async def cmd_add_controller_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(controller_name=name)
    await state.set_state(AddControllerForm.controller_password)
    await message.answer(f"Пароль MQTT:",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text="Отменить")],
                             ]
                         ))


@router.message(AddControllerForm.controller_password)
async def cmd_add_controller_password(message: Message, session: AsyncSession, user: User, state: FSMContext):
    try:
        password = message.text.strip()
        name = (await state.get_data())["controller_name"]

        reply = ""
        try:
            was_added = await users.authorize_controller_async(session, user, name, password)
            if was_added:
                reply = f"Контроллер успешно добавлен!"
            else:
                reply = f"Контроллер уже добавлен"

        except users.AuthorizationError:
            reply = f"Неверные данные контроллера"

        if reply:
            await message.answer(reply,
                                 reply_markup=ReplyKeyboardRemove())
    finally:
        await state.clear()
