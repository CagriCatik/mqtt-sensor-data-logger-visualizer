import logging
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_TEMPERATURE = "home/temperature"
TOPIC_COMMAND = "home/heater_command"

logging.basicConfig(level=logging.INFO)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker")
        client.subscribe(TOPIC_TEMPERATURE)
    else:
        logging.error(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        temperature = float(msg.payload.decode())
        logging.info(f"Received temperature: {temperature:.2f} °C")

        if temperature < 20:
            command = "HEATER_ON"
        elif temperature > 25:
            command = "HEATER_OFF"
        else:
            command = "STANDBY"

        logging.info(f"Publishing heater command: {command}")
        client.publish(TOPIC_COMMAND, command)
    except ValueError:
        logging.warning(f"Invalid temperature data: {msg.payload}")
    except Exception as e:
        logging.error(f"Error processing message: {e}")

client = mqtt.Client("ControlNode")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()
