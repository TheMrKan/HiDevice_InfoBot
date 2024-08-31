import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

DB_URI = os.getenv("DB_URI")
if not DB_URI:
    raise ValueError("DB_URI environment variable is not set")

MQTT_HOST = os.getenv("MQTT_HOST")
if not MQTT_HOST:
    raise ValueError("MQTT_HOST environment variable is not set")

MQTT_PORT = os.getenv("MQTT_PORT")
if not MQTT_PORT:
    raise ValueError("MQTT_PORT environment variable is not set")
MQTT_PORT = int(MQTT_PORT)

MQTT_USER = os.getenv("MQTT_USER")
if not MQTT_USER:
    raise ValueError("MQTT_USER environment variable is not set")

MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
if not MQTT_PASSWORD:
    raise ValueError("MQTT_PASSWORD environment variable is not set")