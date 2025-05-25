import os
import sys

# ── Ensure project root is on sys.path so imports resolve correctly ─────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import threading
import time
import logging

from canbus.can_interface import read_can, write_can
from mqtt.mqtt_client      import connect, client
from bridge.translator     import can_to_mqtt, mqtt_to_can

# ——— Logging Setup ———————————————————————————————————————————————
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("test.e2e")

# ——— Gateway Loop —————————————————————————————————————————————
def gateway_loop():
    """
    Mirror CAN→MQTT continuously.
    Incoming MQTT→CAN is handled in mqtt_client.on_message().
    """
    while True:
        msg = read_can(timeout=0.5)
        if msg:
            topic, payload = can_to_mqtt(msg)
            logger.info(f"[CAN→MQTT] {topic} ← ID=0x{msg.arbitration_id:X}, data={msg.data.hex()}")
            client.publish(topic, payload)
        time.sleep(0.1)

# ——— Test: CAN → MQTT ——————————————————————————————————————————
def test_can_to_mqtt():
    """
    Send a few CAN frames and ensure they appear as MQTT publishes.
    """
    for i in range(3):
        data = bytes([i, i+1, i+2, i+3])
        write_can(0x123, data)
        logger.info(f"[TEST CAN→MQTT] Injected CAN ID=0x123, data={data.hex()}")
        time.sleep(1)

# ——— Test: MQTT → CAN ——————————————————————————————————————————
def test_mqtt_to_can():
    """
    Publish to can/in and observe CAN writes back to the bus.
    """
    for i in range(3):
        topic   = "can/in/0x200"
        payload = ''.join(f"{x:02x}" for x in [10+i, 20+i, 30+i, 40+i])
        logger.info(f"[TEST MQTT→CAN] Publishing {topic} payload={payload}")
        client.publish(topic, payload)
        time.sleep(1)

if __name__ == "__main__":
    logger.info("Starting end-to-end test")

    # 1) start MQTT client
    connect()

    # 2) start gateway in background
    gw_thread = threading.Thread(target=gateway_loop, daemon=True)
    gw_thread.start()

    # give things a moment to settle
    time.sleep(1)

    # 3) run CAN→MQTT test
    test_can_to_mqtt()

    # 4) run MQTT→CAN test
    test_mqtt_to_can()

    # allow any last messages through
    time.sleep(2)

    logger.info("End-to-end test complete. Exiting.")
    client.loop_stop()
