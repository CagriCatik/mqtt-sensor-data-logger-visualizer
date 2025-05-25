import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog
import pyqtgraph as pg
from data_buffer import CircularBuffer
import pandas as pd

# Configure module-level logger
logger = logging.getLogger(__name__)

class PlotView(QWidget):
    """
    A QWidget that renders real-time plots using pyqtgraph
    for each sensor topic in its own subwindow and provides CSV export,
    with debug logging.
    """
    def __init__(self, buffers: dict[str, CircularBuffer]):
        super().__init__()
        self.buffers = buffers
        logger.debug("PlotView: Initializing with buffers: %s", list(self.buffers.keys()))
        self._setup_ui()
        self._setup_plots()
        logger.debug("PlotView: UI and plot setup complete")

    def _setup_ui(self):
        logger.debug("PlotView: Setting up UI components")
        # Container layouts
        self.main_layout = QVBoxLayout(self)
        self.plots_layout = QHBoxLayout()

        # Export button
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self._export_csv)

        # Add subwindow slot for each topic
        self.plot_widgets: dict[str, pg.PlotWidget] = {}
        for topic in self.buffers.keys():
            pw = pg.PlotWidget(title=topic)
            pw.setLabel('bottom', 'Time', units='s')
            pw.setLabel('left', 'Value')
            pw.addLegend()
            self.plots_layout.addWidget(pw)
            self.plot_widgets[topic] = pw

        # Assemble layouts
        self.main_layout.addLayout(self.plots_layout)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        self.main_layout.addLayout(btn_layout)
        logger.debug("PlotView: UI components added to layout")

    def _setup_plots(self):
        logger.debug("PlotView: Initializing plot curves for each subwindow")
        # Create a data curve for each topic in its widget
        self.curves: dict[str, pg.PlotDataItem] = {}
        for idx, (topic, pw) in enumerate(self.plot_widgets.items()):
            color = pg.intColor(idx, hues=len(self.plot_widgets))
            pen = pg.mkPen(color=color, width=2)
            curve = pw.plot([], [], name=topic, pen=pen)
            self.curves[topic] = curve
        logger.debug("PlotView: Plot curves configured for topics: %s", list(self.curves.keys()))

    def update_plot(self):
        logger.debug("PlotView: Updating plot data for each subwindow")
        for topic, buf in self.buffers.items():
            times, values = buf.get_series()
            logger.debug("PlotView: Retrieved %d points for topic %s", len(times), topic)
            if times and values:
                t0 = times[0]
                rel = [t - t0 for t in times]
                self.curves[topic].setData(rel, values)
        logger.debug("PlotView: Plot curves updated")

    def _export_csv(self):
        logger.debug("PlotView: Export CSV triggered")
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Data to CSV", filter="CSV Files (*.csv)"
        )
        if not path:
            logger.debug("PlotView: Export cancelled by user")
            return
        dfs = []
        for topic, buf in self.buffers.items():
            times, values = buf.get_series()
            logger.debug("PlotView: Adding %d records for topic %s to CSV DataFrame", len(times), topic)
            dfs.append(pd.DataFrame({
                "timestamp": times,
                topic: values
            }))
        combined = pd.concat(dfs, axis=1)
        combined.to_csv(path, index=False)
        logger.info("PlotView: Data exported to CSV at %s", path)
