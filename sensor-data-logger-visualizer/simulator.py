import time
import json
import random
import logging
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # — Configure logging —
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(name)s %(levelname)s: %(message)s'
    )

    # — MQTT setup —
    broker = 'localhost'
    port   = 1883

    # Topics and their QoS levels
    qos_map = {
        'sensor/temperature': 0,
        'sensor/humidity':    1,
        'sensor/co2':         2,
    }

    client = mqtt.Client(
        client_id="simulator",
        clean_session=True
    )

    # Last Will & Testament: notify if the simulator goes offline unexpectedly
    client.will_set(
        'sensor/logger/status',
        payload='OFFLINE',
        qos=1,
        retain=True
    )

    client.connect(broker, port)
    client.loop_start()

    # Announce online status
    client.publish(
        'sensor/logger/status',
        payload='ONLINE',
        qos=1,
        retain=True
    )

    logger.info("Simulator started publishing to %s:%s", broker, port)

    try:
        while True:
            for topic, qos in qos_map.items():
                # Generate a random value based on topic
                if topic.endswith('temperature'):
                    value = round(random.uniform(20.0, 30.0), 2)
                elif topic.endswith('humidity'):
                    value = round(random.uniform(30.0, 70.0), 2)
                else:  # CO2
                    value = round(random.uniform(400.0, 600.0), 2)

                payload = json.dumps({'value': value})
                client.publish(topic, payload, qos=qos)
                logger.debug("Published %s to %s @ QoS %d", value, topic, qos)

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping simulator…")
    finally:
        # Clean shutdown
        client.publish(
            'sensor/logger/status',
            payload='OFFLINE',
            qos=1,
            retain=True
        )
        client.loop_stop()
        client.disconnect()
        logger.info("Simulator stopped")
