from aiogram import html
import logging

import broadcaster


logger = logging.getLogger(__name__)


async def handle_lwt_async(mqtt_host: str, mqtt_user: str, lwt: int):
    logger.debug("[%s] [LWT] %s", mqtt_user, lwt)
    tg_message = f"{"🟢" if lwt else "🔴"}  {html.bold(f"{mqtt_user} {"подключился к брокеру" if lwt else "отключился от брокера"} {mqtt_host}")}"
    await broadcaster.broadcast_async(mqtt_user, tg_message)


async def handle_message_async(mqtt_user: str, message: str):
    logger.debug("[%s] [Message] %s", mqtt_user, message)
    tg_message = f"{html.bold(f"💬  Контроллер {mqtt_user}")}\n\n{message}"
    await broadcaster.broadcast_async(mqtt_user, tg_message)
