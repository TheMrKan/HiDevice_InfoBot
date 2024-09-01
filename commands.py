from aiogram import Router, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ErrorEvent
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from core.models import User
from core import controllers, users


router = Router(name="commands")


LIST_CONTROLLERS = "Подключенные контроллеры"
ADD_CONTROLLER = "Добавить"
REMOVE_CONTROLLER = "Удалить"

START_MESSAGE = f"""
{html.bold("🤖 Hi-Garden Telegram Bot")}

Бот позволяет подключить оповещения в Telegram от контроллеров {html.link("Hi-Garden", "https://hi-garden.ru/")}.

Используйте /add_controller, введите имя пользователя и пароль MQTT от Вашего контроллера, чтобы начать получать оповещения.

Другие команды:
/list - посмотреть список подключенных устройств
/remove_controller - удалить контроллер из бота
"""


default_keyboard = ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text=LIST_CONTROLLERS)],
                                 [KeyboardButton(text=ADD_CONTROLLER), KeyboardButton(text=REMOVE_CONTROLLER)],
                             ],
                             resize_keyboard=True
                         )

cancel_keyboard = ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text="Отменить")],
                             ],
                             resize_keyboard=True
                         )


logger = logging.getLogger(__name__)


@router.error()
async def error_handler(event: ErrorEvent):
    logger.exception("An error occured during handling an event", exc_info=event.exception)
    if event.update.message:
        await event.update.message.answer("❌  Во время обработки произошла непредвиденная ошибка", reply_markup=default_keyboard)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(START_MESSAGE, reply_markup=default_keyboard)


@router.message(Command("list"))
@router.message(F.text.casefold() == LIST_CONTROLLERS.casefold())
async def cmd_list(message: Message, session: AsyncSession, user: User):
    user_controllers = await users.get_user_controllers_async(session, user)
    content = "Пусто" if not user_controllers else "\n".join((f"▫️ {name}" for name in user_controllers))
    await message.answer(f"{html.bold(f"❗️ Подключенные контроллеры ❗")}\n\n{content}", reply_markup=default_keyboard)


class AddControllerForm(StatesGroup):
    controller_name = State()
    controller_password = State()


@router.message(Command("add_controller"))
@router.message(F.text.casefold() == ADD_CONTROLLER.casefold())
async def cmd_add_controller(message: Message, state: FSMContext):
    await state.set_state(AddControllerForm.controller_name)
    await message.answer(f"{html.bold("❗️ Добавление контроллера ❗️")}\n\n👤  Имя пользователя MQTT:",
                         reply_markup=cancel_keyboard)


@router.message(F.text.casefold() == "отменить")
async def cmd_add_controller_cancel(message: Message, state: FSMContext):
    if state is None:
        return
    await state.clear()
    await message.answer("🚫  Действие отменено",
                         reply_markup=default_keyboard)


@router.message(AddControllerForm.controller_name)
async def cmd_add_controller_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(controller_name=name)
    await state.set_state(AddControllerForm.controller_password)
    await message.answer(f"🔑  Пароль MQTT:",
                         reply_markup=cancel_keyboard)


@router.message(AddControllerForm.controller_password)
async def cmd_add_controller_password(message: Message, session: AsyncSession, user: User, state: FSMContext):
    try:
        password = message.text.strip()
        name = (await state.get_data())["controller_name"]

        reply = ""
        try:
            was_added = await users.authorize_controller_async(session, user, name, password)
            if was_added:
                reply = f"✅  Контроллер успешно добавлен"
            else:
                reply = f"⚠️  Контроллер уже добавлен"

        except users.AuthorizationError:
            reply = f"❌  Неверные данные контроллера"

        if reply:
            await message.answer(reply,
                                 reply_markup=default_keyboard)
    finally:
        await state.clear()


class RemoveControllerForm(StatesGroup):
    controller_name = State()


@router.message(Command("remove_controller"))
@router.message(F.text.casefold() == REMOVE_CONTROLLER.casefold())
async def cmd_remove_controller(message: Message, state: FSMContext):
    await state.set_state(RemoveControllerForm.controller_name)
    await message.answer(f"{html.bold("❗️ Удаление контроллера ❗️")}\n\n👤  Имя пользователя MQTT:", reply_markup=cancel_keyboard)


@router.message(RemoveControllerForm.controller_name)
async def cmd_remove_controller_name(message: Message, session: AsyncSession, user: User, state: FSMContext):
    try:
        name = message.text.strip()
        removed = await users.unauthorize_controller_async(session, user, name)
        reply = ""
        if removed:
            reply = "✅  Контроллер удален"
        else:
            reply = "⚠️  Контроллер не добавлен"
        await message.answer(reply, reply_markup=default_keyboard)
    finally:
        await state.clear()
