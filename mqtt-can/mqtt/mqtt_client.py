import paho.mqtt.client as mqtt
import logging
from bridge.translator import mqtt_to_can
from canbus.can_interface import write_can

logger = logging.getLogger("mqtt.client")
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
        client.subscribe("can/in/#")
        logger.info("Subscribed to topic: can/in/#")
    else:
        logger.error(f"Failed to connect to MQTT broker, rc={rc}")

def on_message(client, userdata, msg):
    logger.debug(f"MQTT message received: topic={msg.topic}, payload={msg.payload}")
    try:
        can_id, data = mqtt_to_can(msg.topic, msg.payload)
        write_can(can_id, data)
    except Exception as e:
        logger.exception(f"Error processing MQTT message: {e}")

def connect(broker_host="broker.hivemq.com", broker_port=1883):
    logger.info(f"Connecting to MQTT broker at {broker_host}:{broker_port}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker_host, broker_port)
    client.loop_start()
