import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


COLORS = [
    "#e74c3c",
    "#2ecc71",
    "#3498db",
    "#f39c12",
    "#9b59b6",
    "#1abc9c",
    "#e67e22",
    "#34495e",
]


class VoltageTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._curves = []
        self._channel_checks = []
        self._num_channels = 0
        self._fsamp = 500_000
        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        control_group = QGroupBox("Channels")
        control_layout = QVBoxLayout(control_group)
        control_layout.setAlignment(Qt.AlignTop)
        self._channels_info = QLabel("Waiting for acquisition data...")
        self._channels_info.setWordWrap(True)
        control_layout.addWidget(self._channels_info)
        control_layout.addSpacing(8)
        self._control_layout = control_layout
        control_group.setFixedWidth(200)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Voltage", units="V")
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.plot_widget)
        splitter.addWidget(control_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        main_layout.addWidget(splitter)

    def set_sampling_info(self, fsamp: int):
        self._fsamp = fsamp

    def reset_plots(self):
        self._curves.clear()
        self._channel_checks.clear()
        self._num_channels = 0
        self.plot_widget.clear()
        self._clear_checkboxes()
        self._channels_info.setText("Waiting for acquisition data...")

    def set_channel_names(self, names: list[str]):
        self.reset_plots()
        self._num_channels = len(names)
        self._channels_info.setText(f"Channels: {len(names)}")
        for i, name in enumerate(names):
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._update_visibility)
            self._control_layout.addWidget(checkbox)
            self._channel_checks.append(checkbox)
            curve = self.plot_widget.plot(
                pen=pg.mkPen(COLORS[i % len(COLORS)], width=1),
                name=name,
            )
            self._curves.append(curve)

    def on_voltage_data(self, voltages: np.ndarray):
        if self._num_channels == 0 or self._num_channels != voltages.shape[0]:
            return

        time_axis = np.arange(voltages.shape[1]) / self._fsamp
        for i in range(voltages.shape[0]):
            if self._channel_checks[i].isChecked():
                self._curves[i].setData(time_axis, voltages[i])
                self._curves[i].show()
            else:
                self._curves[i].hide()

    def _clear_checkboxes(self):
        for i in reversed(range(self._control_layout.count())):
            item = self._control_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QCheckBox):
                item.widget().deleteLater()

    def _update_visibility(self):
        for i in range(self._num_channels):
            if self._channel_checks[i].isChecked():
                self._curves[i].show()
            else:
                self._curves[i].hide()
