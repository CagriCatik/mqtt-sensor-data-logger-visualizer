#!/usr/bin/env python3
"""
1. Tests TCP connectivity to the broker.
2. Enables Paho-MQTT’s debug logging (CONNECT, SUBACK, etc).
3. Subscribes to all sensor topics (sensor/#) and prints incoming messages.
"""

import socket
import sys
import logging
import json
import paho.mqtt.client as mqtt

BROKER_HOST = 'localhost'
BROKER_PORT = 1883
TOPIC_WILDCARD = 'sensor/#'
CONNECT_TIMEOUT = 5  # seconds

def test_tcp_connect(host: str, port: int, timeout: int = CONNECT_TIMEOUT) -> bool:
    """Try opening a TCP connection to (host, port)."""
    try:
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        print(f"[✔] TCP connection to {host}:{port} succeeded")
        return True
    except Exception as e:
        print(f"[✘] TCP connection to {host}:{port} failed: {e}")
        return False

def on_connect(client, userdata, flags, rc):
    """Paho-MQTT callback when CONNACK is received."""
    if rc == 0:
        print(f"[✔] MQTT CONNECT successful (rc={rc})")
        # Subscribe to the wildcard topic
        client.subscribe(TOPIC_WILDCARD, qos=1)
        print(f"[→] SUBSCRIBED to '{TOPIC_WILDCARD}' (QoS 1)")
    else:
        print(f"[✘] MQTT CONNECT failed with rc={rc}")

def on_message(client, userdata, msg):
    """Paho-MQTT callback when a PUBLISH arrives."""
    try:
        payload = msg.payload.decode('utf-8')
        # Try parsing JSON if applicable
        try:
            parsed = json.loads(payload)
            payload_str = json.dumps(parsed, indent=None)
        except json.JSONDecodeError:
            payload_str = payload

        print(f"[←] {msg.topic} → {payload_str}")
    except Exception as e:
        print(f"[!] Error processing incoming message: {e}")

def main():
    # 1) Test raw TCP connectivity
    test_tcp_connect(BROKER_HOST, BROKER_PORT)

    # 2) Configure logging to see Paho internal debug
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)s %(levelname)s: %(message)s')
    paho_logger = logging.getLogger('paho')
    
    # 3) Instantiate client and enable its logger
    client = mqtt.Client(client_id="mqtt_verifier", clean_session=True)
    client.enable_logger(paho_logger)
    client.on_connect = on_connect
    client.on_message = on_message

    # 4) Connect and enter loop
    try:
        print(f"[→] Connecting to MQTT broker at {BROKER_HOST}:{BROKER_PORT} …")
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user, exiting…")
        client.disconnect()
        sys.exit(0)
    except Exception as e:
        print(f"[✘] Failed to connect/loop: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
