import logging

logger = logging.getLogger("bridge.translator")

def can_to_mqtt(can_msg):
    """
    Translate a can.Message into an MQTT topic+payload.
    """
    topic   = f"can/out/{hex(can_msg.arbitration_id)}"
    payload = can_msg.data.hex()
    logger.debug(f"Translating CAN→MQTT: ID=0x{can_msg.arbitration_id:X} → ({topic}, {payload})")
    return topic, payload

def mqtt_to_can(topic, payload):
    """
    Translate an MQTT topic+payload into (can_id, data_bytes).
    """
    hex_id = topic.rsplit('/', 1)[-1]
    can_id = int(hex_id, 16)
    if isinstance(payload, bytes):
        payload = payload.decode()
    data = bytes.fromhex(payload)
    logger.debug(f"Translating MQTT→CAN: ({topic}, {payload}) → ID=0x{can_id:X}, data={data.hex()}")
    return can_id, data
