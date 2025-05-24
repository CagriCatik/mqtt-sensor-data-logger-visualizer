# sensor_app/main.py
import sys, logging
from PySide6.QtWidgets import QApplication

from mqtt_client import MQTTClient
from data_buffer import CircularBuffer
from ui import MainWindow

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s: %(message)s"
)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    topics = ["sensor/temperature", "sensor/humidity", "sensor/co2"]
    buffers = {t: CircularBuffer(maxlen=100) for t in topics}
    mqtt = MQTTClient(broker="localhost", port=1883)

    window = MainWindow(mqtt, buffers)
    mqtt.connect()

    window.show()
    sys.exit(app.exec())
