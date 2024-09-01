from aiogram import html

import broadcaster


async def handle_lwt_async(mqtt_user: str, lwt: int):
    tg_message = f"{"🟢" if lwt else "🔴"}  {html.bold(f"{mqtt_user} {"подключился к брокеру" if lwt else "отключился от брокера"}")}"
    await broadcaster.broadcast_async(mqtt_user, tg_message)


async def handle_message_async(mqtt_user: str, message: str):
    tg_message = f"{html.bold(f"💬  Контроллер {mqtt_user}")}\n\n{message}"
    await broadcaster.broadcast_async(mqtt_user, tg_message)
