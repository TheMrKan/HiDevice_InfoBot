from aiogram import Router, html, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ErrorEvent,
                           InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery)
from aiogram.types import BotCommand
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
CONFIGURE = "Настроить"
DIAGNOSTICS = "Диагностика"

COMMAND_LIST = [
        BotCommand(command="/list", description="Список подключенных контроллеров"),
        BotCommand(command="/add_controller", description="Подключить контроллер"),
        BotCommand(command="/remove_controller", description="Удалить контроллер"),
        BotCommand(command="/configure", description="Настроить уведомления"),
        BotCommand(command="/diagnostics", description="Запрос диагностических данных с контроллера")
    ]

START_MESSAGE = f"""
{html.bold("🤖 Hi-Garden Telegram Bot")}

Бот позволяет подключить оповещения в Telegram от контроллеров {html.link("Hi-Garden", "https://hi-garden.ru/")}.

Используйте /add_controller, введите имя пользователя и пароль MQTT от Вашего контроллера, чтобы начать получать оповещения.

Другие команды:
/list - посмотреть список подключенных устройств
/remove_controller - удалить контроллер из бота
/configure - настроить уведомления
/diagnostics - запросить диагностические данные с контроллера
"""

NOTIFICATION_TRANSLATIONS = {
    "channel_status": "Статус каналов",
    "dry_mode": "Сухой режим",
    "clock_error": "Ошибка часов"
}


default_keyboard = ReplyKeyboardMarkup(
                             keyboard=[
                                 [KeyboardButton(text=LIST_CONTROLLERS)],
                                 [KeyboardButton(text=ADD_CONTROLLER), KeyboardButton(text=REMOVE_CONTROLLER)],
                                 [KeyboardButton(text=CONFIGURE), KeyboardButton(text=DIAGNOSTICS)],
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


def build_notifications_markup(controller_name: str, notifications: dict[str, bool]) -> InlineKeyboardMarkup:
    inline = InlineKeyboardMarkup(inline_keyboard=[[]])
    for key, enabled in notifications.items():
        text = ("🟢" if enabled else "🔴") + "   " + NOTIFICATION_TRANSLATIONS.get(key, key)
        inline.inline_keyboard.append([InlineKeyboardButton(text=text, callback_data=f"notification:{controller_name}:{key}")])

    return inline


def build_controller_name_markup(user_controllers: list[str]):
    keyboard = ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    for controller in user_controllers:
        keyboard.keyboard.append([KeyboardButton(text=controller)])
    keyboard.keyboard += cancel_keyboard.keyboard

    return keyboard


@router.error()
async def error_handler(event: ErrorEvent):
    logger.exception("An error occured during handling an event", exc_info=event.exception)
    if event.update.message:
        await event.update.message.answer("❌  Во время обработки произошла непредвиденная ошибка", reply_markup=default_keyboard)
    elif event.update.callback_query:
        await event.update.callback_query.answer("❌  Во время обработки произошла непредвиденная ошибка", reply_markup=default_keyboard)


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
async def cmd_remove_controller(message: Message, state: FSMContext, session: AsyncSession, user: User):
    await state.set_state(RemoveControllerForm.controller_name)
    user_controllers = await users.get_user_controllers_async(session, user)
    await message.answer(f"{html.bold("❗️ Удаление контроллера ❗️")}\n\n👤  Имя пользователя MQTT:", reply_markup=build_controller_name_markup(user_controllers))


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


class ConfigureForm(StatesGroup):
    controller_name = State()


@router.message(Command("configure"))
@router.message(F.text.casefold() == CONFIGURE.casefold())
async def cmd_configure(message: Message, state: FSMContext, session: AsyncSession, user: User):
    await state.set_state(ConfigureForm.controller_name)
    user_controllers = await users.get_user_controllers_async(session, user)
    await message.answer(f"{html.bold("⚙️ Настройка уведомлений ⚙️")}\n\n👤  Имя пользователя MQTT:",
                         reply_markup=build_controller_name_markup(user_controllers))


@router.message(ConfigureForm.controller_name)
async def cmd_configure_name(message: Message, session: AsyncSession, user: User, state: FSMContext):
    try:
        name = message.text.strip()

        if await users.has_controller_async(session, user, name):
            controller = await controllers.get_controller_async(session, name)
            notifications = controllers.get_controller_notifications(controller)

            inline = build_notifications_markup(name, notifications)

            await message.answer(text=f"⚙️ {html.bold(f"Настройка уведомлений {name}")} ⚙️\n\n", reply_markup=inline)
            reply = "Нажмите на необходимый пункт, чтобы изменить статус уведомлений."
        else:
            reply = "⚠️  Контроллер не добавлен"

        await message.answer(text=reply, reply_markup=default_keyboard)

    finally:
        await state.clear()


@router.callback_query(F.data.startswith('notification:'))
async def callback_notification(callback_query: CallbackQuery, session: AsyncSession, user: User):
    controller_name, notifications_key = callback_query.data.split(":")[1:3]
    if not await users.has_controller_async(session, user, controller_name):
        await callback_query.answer(text="❌  Ошибка доступа")
        return

    logger.info("User '%s' switched notifications '%s' for controller '%s'", user.id, notifications_key,
                controller_name)

    controller = await controllers.get_controller_async(session, controller_name)
    if controller is None:
        raise KeyError(f"Controller {controller_name!r} not found")

    new_state = await controllers.switch_notifications_async(controller, notifications_key)

    translation = NOTIFICATION_TRANSLATIONS.get(notifications_key, notifications_key)
    await callback_query.answer(text=f"{"🟢" if new_state else "🔴"} {translation} - {"ВКЛЮЧЕНО" if new_state else "ВЫКЛЮЧЕНО"}")

    notifications = controllers.get_controller_notifications(controller)
    inline = build_notifications_markup(controller_name, notifications)
    await callback_query.message.edit_reply_markup(reply_markup=inline)


class DiagnosticsForm(StatesGroup):
    controller_name = State()


@router.message(Command("diagnostics"))
@router.message(F.text.casefold() == DIAGNOSTICS.casefold())
async def cmd_diagnostics(message: Message, state: FSMContext, session: AsyncSession, user: User):
    await state.set_state(DiagnosticsForm.controller_name)
    user_controllers = await users.get_user_controllers_async(session, user)
    await message.answer(f"{html.bold("⚙️ Диагностика ⚙️")}\n\n👤  Имя пользователя MQTT:",
                         reply_markup=build_controller_name_markup(user_controllers))


@router.message(DiagnosticsForm.controller_name)
async def cmd_diagnostics_name(message: Message, session: AsyncSession, user: User, state: FSMContext):
    try:
        name = message.text.strip()

        if await users.has_controller_async(session, user, name):
            inline = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Вкл. сегодня", callback_data=f"diagnostics:{name}:{controllers.DiagnosticsData.TODAY.name}")],
                [InlineKeyboardButton(text="Вкл. вчера", callback_data=f"diagnostics:{name}:{controllers.DiagnosticsData.YESTERDAY.name}")]
            ])

            await message.answer(text=f"⚙️ {html.bold(f"Диагностика {name}")} ⚙️\n\n", reply_markup=inline)
            reply = "Нажмите на необходимый пункт, чтобы запросить диагностические данные с контроллера."
        else:
            reply = "⚠️  Контроллер не добавлен"

        await message.answer(text=reply, reply_markup=default_keyboard)

    finally:
        await state.clear()


@router.callback_query(F.data.startswith('diagnostics:'))
async def callback_notification(callback_query: CallbackQuery, session: AsyncSession, user: User):
    controller_name, diagnostics_key = callback_query.data.split(":")[1:3]
    if not await users.has_controller_async(session, user, controller_name):
        await callback_query.answer(text="❌  Ошибка доступа")
        return

    logger.info("User '%s' requsting '%s' diagnostics data for controller '%s'", user.id, diagnostics_key, controller_name)

    controller = await controllers.get_controller_async(session, controller_name)
    if controller is None:
        raise KeyError(f"Controller {controller_name!r} not found")

    await controllers.request_diagnostics_async(controller, controllers.DiagnosticsData[diagnostics_key])
    await callback_query.answer(text=f"Запрос отправлен")



