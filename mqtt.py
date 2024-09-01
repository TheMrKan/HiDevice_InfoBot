import asyncio
import asyncio_mqtt as aiomqtt
import logging

import config
import mqtt_handlers

logger = logging.getLogger("MQTT")    # по какой-то причине логгер 'mqtt' не работает


async def listen_async(host: str, port: int, username: str, password: str):
    logger.debug(f"Connecting to {username}@{host}:{port}...")
    async with aiomqtt.Client(host, port, username=username, password=password) as client:
        logger.info(f"Listening for MQTT server {username}@{host}:{port}")
        async with client.messages() as messages:
            await client.subscribe("+/telegram")
            await client.subscribe("+/tele/Aquarius/LWT")
            async for message in messages:
                try:
                    await handle_message_async(host, str(message.topic), message.payload.decode("utf-8"), message.retain)
                except Exception as e:
                    logger.exception("Failed to handle message '%s' from %s", message.payload, str(message.topic), exc_info=e)


def get_mqtt_user(topic: str) -> str:
    return topic.split("/")[0]


async def handle_message_async(mqtt_host: str, topic: str, message: str, retain: bool):
    if retain or not message.strip():
        return

    mqtt_user = get_mqtt_user(topic)
    if topic.endswith("LWT"):
        await mqtt_handlers.handle_lwt_async(mqtt_host, mqtt_user, int(message))
    else:
        await mqtt_handlers.handle_message_async(mqtt_user, message.strip())


