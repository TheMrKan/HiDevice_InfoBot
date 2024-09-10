import asyncio
import asyncio_mqtt as aiomqtt
import logging
from typing import Callable, Awaitable

import config

logger = logging.getLogger("MQTT")    # по какой-то причине логгер 'mqtt' не работает


lwt_handler_async: Callable[[str, str, int], Awaitable]
message_handler_async: Callable[[str, str], Awaitable]


__clients: set[aiomqtt.Client] = set()


async def listen_async(host: str, port: int, username: str, password: str):
    logger.debug(f"Connecting to {username}@{host}:{port}...")
    async with aiomqtt.Client(host, port, username=username, password=password) as client:
        logger.info(f"Listening for MQTT server {username}@{host}:{port}")
        __clients.add(client)
        try:
            async with client.messages() as messages:
                await client.subscribe("+/telegram")
                await client.subscribe("+/tele/Aquarius/LWT")
                async for message in messages:
                    try:
                        await handle_message_async(host, str(message.topic), message.payload.decode("utf-8"), message.retain)
                    except Exception as e:
                        logger.exception("Failed to handle message '%s' from %s", message.payload, str(message.topic), exc_info=e)
        finally:
            __clients.remove(client)


def get_mqtt_user(topic: str) -> str:
    return topic.split("/")[0]


async def handle_message_async(mqtt_host: str, topic: str, message: str, retain: bool):
    if retain or not message.strip():
        return

    mqtt_user = get_mqtt_user(topic)
    if topic.endswith("LWT"):
        await lwt_handler_async(mqtt_host, mqtt_user, int(message))
    else:
        await message_handler_async(mqtt_user, message.strip())


async def send_async(mqtt_user: str, message: str):
    topic = f"{mqtt_user}/aqua_smart"
    logger.info("Sending to '%s': '%s'", topic, message)
    await asyncio.gather(*(asyncio.create_task(c.publish(topic, message)) for c in __clients))


