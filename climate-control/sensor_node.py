# sensor_node.py

import time
import random
import logging
import paho.mqtt.client as mqtt
from mqtt_config import BROKER, PORT, TOPIC_TEMPERATURE, QOS

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [SensorNode] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def generate_temperature():
    return round(random.uniform(15.0, 30.0), 2)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT Broker successfully.")
    else:
        logging.error(f"Failed to connect to MQTT Broker, return code {rc}")

def on_publish(client, userdata, mid):
    logging.debug(f"Message published successfully, mid={mid}")

def on_disconnect(client, userdata, rc):
    logging.warning(f"Disconnected from broker with return code {rc}")

client = mqtt.Client("SensorNode")
client.on_connect = on_connect
client.on_publish = on_publish
client.on_disconnect = on_disconnect

try:
    logging.info(f"Connecting to broker at {BROKER}:{PORT}")
    client.connect(BROKER, PORT, 60)
except Exception as e:
    logging.exception(f"Connection error: {e}")

client.loop_start()
try:
    while True:
        temp = generate_temperature()
        logging.info(f"Generated temperature: {temp}°C")
        result = client.publish(TOPIC_TEMPERATURE, temp, qos=QOS)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logging.error("Publish failed.")
        time.sleep(1)
except KeyboardInterrupt:
    logging.info("SensorNode shutting down.")
finally:
    client.loop_stop()
    client.disconnect()
