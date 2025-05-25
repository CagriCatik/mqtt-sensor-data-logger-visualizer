import logging
import time
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import QTimer
from mqtt_client import MQTTClient
from data_buffer import CircularBuffer
from plot_view import PlotView

# Configure module-level logger
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    Main application window: sets up the plot view, timer, and MQTT handlers, with debug logging.
    """
    def __init__(self, mqtt_client: MQTTClient, buffers: dict[str, CircularBuffer]):
        super().__init__()
        logger.debug("MainWindow: Initializing")
        self.setWindowTitle("Sensor Data Logger & Visualizer")
        self.resize(800, 400)    # width=1200px, height=600px
        self.buffers = buffers
        self.plot_view = PlotView(self.buffers)
        self.setCentralWidget(self.plot_view)

        self.timer = QTimer(self)
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.plot_view.update_plot)
        self.timer.start()
        logger.debug("MainWindow: Timer started with 500ms interval")

        for topic in self.buffers.keys():
            mqtt_client.register_handler(topic, self._make_handler(topic))
            logger.debug("MainWindow: Registered handler for topic %s", topic)

    def _make_handler(self, topic: str):
        def handler(value: float):
            ts = time.time()
            self.buffers[topic].append(ts, value)
            logger.debug("MainWindow: Buffered value %s for topic %s at %s", value, topic, ts)
        return handler