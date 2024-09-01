import asyncio
import traceback
import asyncio_mqtt as aiomqtt

import config
import mqtt_handlers


async def listen_async():
    async with aiomqtt.Client(config.MQTT_HOST, config.MQTT_PORT, username=config.MQTT_USER, password=config.MQTT_PASSWORD) as client:
        async with client.messages() as messages:
            await client.subscribe("+/telegram")
            await client.subscribe("+/tele/Aquarius/LWT")
            async for message in messages:
                try:
                    await handle_message_async(str(message.topic), message.payload.decode("utf-8"))
                except:
                    traceback.print_exc()


def get_mqtt_user(topic: str) -> str:
    return topic.split("/")[0]


async def handle_message_async(topic: str, message: str):
    mqtt_user = get_mqtt_user(topic)
    if topic.endswith("LWT"):
        await mqtt_handlers.handle_lwt_async(mqtt_user, int(message))
    else:
        await mqtt_handlers.handle_message_async(mqtt_user, message)


