import time
import logging
from canbus.can_interface import read_can
from mqtt.mqtt_client import connect, client
from bridge.translator import can_to_mqtt

# Global logger & config
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("main")

def main_loop(poll_interval=0.1):
    """
    Main gateway loop:
      - read from CAN → publish to MQTT
      - incoming MQTT handled in mqtt_client.on_message()
    """
    while True:
        msg = read_can(timeout=1.0)
        if msg:
            topic, payload = can_to_mqtt(msg)
            logger.info(f"Publishing to MQTT: {topic} → {payload}")
            client.publish(topic, payload)
        time.sleep(poll_interval)

if __name__ == "__main__":
    logger.info("Starting MQTT–CAN gateway")
    connect()
    main_loop()
