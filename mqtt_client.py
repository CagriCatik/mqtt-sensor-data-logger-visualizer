import json
import logging
import paho.mqtt.client as mqtt
from typing import Callable, Dict

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(
        self,
        broker: str,
        port: int = 1883,
        client_id: str = "visualizer",
        clean_session: bool = False,
        qos_map: Dict[str, int] = None
    ):
        # Initialize MQTT client
        self._client = mqtt.Client(client_id=client_id, clean_session=clean_session)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        # Configure Last-Will to announce offline status
        status_topic = "sensor/logger/status"
        self._client.will_set(
            status_topic,
            payload="OFFLINE",
            qos=1,
            retain=True
        )

        # Connection parameters
        self._broker = broker
        self._port = port

        # Handlers and QoS settings
        self._handlers: Dict[str, Callable[[float], None]] = {}
        self._qos_map: Dict[str, int] = qos_map or {}

        logger.debug(
            "MQTTClient initialized (broker=%s:%d, id=%s)",
            broker, port, client_id
        )

    def register_handler(
        self,
        topic: str,
        handler: Callable[[float], None],
        qos: int = 0
    ):
        """
        Register a callback for a topic, storing its desired QoS level.
        """
        if not callable(handler):
            logger.error("Handler for topic '%s' is not callable", topic)
            return
        self._handlers[topic] = handler
        self._qos_map[topic] = qos
        logger.debug(
            "Registered handler for '%s' with QoS %d", topic, qos
        )

    def connect(self):
        """
        Connect to the MQTT broker, publish ONLINE status, and start the network loop.
        """
        logger.info(
            "Connecting to MQTT broker %s:%d", self._broker, self._port
        )
        self._client.connect(self._broker, self._port)

        # Announce online status (retained)
        self._client.publish(
            "sensor/logger/status",
            payload="ONLINE",
            qos=1,
            retain=True
        )

        # Start background network loop
        self._client.loop_start()

    def disconnect(self):
        """
        Cleanly disconnect: stop loop and publish OFFLINE status.
        """
        # Announce offline status (retained)
        self._client.publish(
            "sensor/logger/status",
            payload="OFFLINE",
            qos=1,
            retain=True
        )
        self._client.loop_stop()
        self._client.disconnect()
        logger.info(
            "Disconnected from MQTT broker %s:%d", self._broker, self._port
        )

    def _on_connect(self, client, userdata, flags, rc):
        """
        Called on successful connection: subscribe to all registered topics.
        """
        logger.info(
            "Connected (rc=%d). Subscribing to topics: %s", rc,
            list(self._handlers.keys())
        )
        for topic, qos in self._qos_map.items():
            client.subscribe(topic, qos=qos)
            logger.debug(
                "Subscribed to '%s' with QoS %d", topic, qos
            )

    def _on_message(self, client, userdata, msg):
        """
        Called when a PUBLISH arrives: parse JSON and invoke handler.
        """
        try:
            payload = msg.payload.decode('utf-8')
            data = json.loads(payload)
            value = float(data.get('value', 0))
            logger.debug(
                "Received message on '%s': %s", msg.topic, value
            )

            handler = self._handlers.get(msg.topic)
            if handler:
                handler(value)
            else:
                logger.warning(
                    "No handler registered for topic '%s'", msg.topic
                )
        except Exception:
            logger.exception(
                "Error processing message on '%s'", msg.topic
            )
