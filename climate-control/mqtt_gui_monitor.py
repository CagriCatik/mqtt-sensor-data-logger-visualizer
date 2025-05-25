import sys
import logging
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QSlider, QPushButton, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, Slot
import pyqtgraph as pg
import paho.mqtt.client as mqtt

# MQTT configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_TEMPERATURE = "home/temperature"
TOPIC_COMMAND = "home/heater_command"

logging.basicConfig(level=logging.INFO)

class MQTTSignals(QObject):
    temperature_received = Signal(float)
    command_received = Signal(str)

class LEDIndicator(QFrame):
    def __init__(self, diameter=20):
        super().__init__()
        self.setFixedSize(diameter, diameter)
        self.setFrameShape(QFrame.StyledPanel)
        self.set_color("gray")

    def set_color(self, color):
        self.setStyleSheet(f"background-color: {color}; border-radius: 10px;")

class SmartThermoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartThermoMQ Dashboard with Sensor")
        self.setMinimumSize(600, 500)

        self.signals = MQTTSignals()
        self.signals.temperature_received.connect(self.update_temperature_plot)
        self.signals.command_received.connect(self.update_command)

        self.temp_data = []

        # MQTT Setup
        self.client = mqtt.Client("SmartThermoGUI")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logging.error(f"MQTT connection failed: {e}")

        # Widgets
        self.temp_label = QLabel("Temperature: -- °C")
        self.status_label = QLabel("Heater Status:")
        self.led = LEDIndicator()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(10)
        self.slider.setMaximum(40)
        self.slider.setValue(25)
        self.slider.valueChanged.connect(self.slider_changed)

        self.slider_label = QLabel("Selected: 25 °C")

        # Plot
        self.plot = pg.PlotWidget()
        self.plot.setTitle("Temperature History")
        self.plot.setLabel('left', 'Temperature (°C)')
        self.plot.setLabel('bottom', 'Sample')
        self.plot.showGrid(x=True, y=True)
        self.temp_curve = self.plot.plot(pen='r')

        # Layouts
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.temp_label)
        top_layout.addStretch()
        top_layout.addWidget(self.status_label)
        top_layout.addWidget(self.led)

        sensor_layout = QHBoxLayout()
        sensor_layout.addWidget(self.slider_label)
        sensor_layout.addWidget(self.slider)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.plot)
        main_layout.addLayout(sensor_layout)
        self.setLayout(main_layout)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT broker")
            client.subscribe(TOPIC_TEMPERATURE)
            client.subscribe(TOPIC_COMMAND)
        else:
            logging.error(f"Failed to connect to broker, code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            if msg.topic == TOPIC_TEMPERATURE:
                self.signals.temperature_received.emit(float(payload))
            elif msg.topic == TOPIC_COMMAND:
                self.signals.command_received.emit(payload)
        except Exception as e:
            logging.warning(f"MQTT message error: {e}")

    @Slot(float)
    def update_temperature_plot(self, value):
        self.temp_label.setText(f"Temperature: {value:.2f} °C")
        self.temp_data.append(value)
        if len(self.temp_data) > 100:
            self.temp_data = self.temp_data[-100:]
        self.temp_curve.setData(self.temp_data)

    @Slot(str)
    def update_command(self, command):
        self.status_label.setText(f"Heater Status: {command}")
        color = {"HEATER_ON": "green", "HEATER_OFF": "red", "STANDBY": "gray"}.get(command, "gray")
        self.led.set_color(color)

    def slider_changed(self, value):
        self.slider_label.setText(f"Selected: {value} °C")
        logging.info(f"Slider changed - publishing: {value} °C")
        self.client.publish(TOPIC_TEMPERATURE, value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartThermoGUI()
    window.show()
    sys.exit(app.exec())
