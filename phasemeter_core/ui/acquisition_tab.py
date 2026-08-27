import collections

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


class AcquisitionTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase_buffers = []
        self._time_buffers = []
        self._curves = []
        self._output_checks = []
        self._output_names = []
        self._frame_count = 0
        self._num_outputs = 0
        self._fphase = 1000
        self._duration = 60
        self._build_ui()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        output_group = QGroupBox("Outputs")
        output_layout = QVBoxLayout(output_group)
        output_layout.setAlignment(Qt.AlignTop)
        self._output_info = QLabel("Waiting for acquisition data...")
        self._output_info.setWordWrap(True)
        output_layout.addWidget(self._output_info)
        output_layout.addSpacing(8)
        self._output_layout = output_layout
        output_group.setFixedWidth(200)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Phase", units="rad")
        self.plot_widget.setLabel("bottom", "Time", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.enableAutoRange()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.plot_widget)
        splitter.addWidget(output_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        main_layout.addWidget(splitter)

    def set_phase_params(self, fphase: int, duration: int):
        self._fphase = fphase
        self._duration = duration

    def set_output_names(self, names: list[str]):
        self._output_names = names
        self._init_plots(len(names))

    def reset_plots(self):
        self._phase_buffers.clear()
        self._time_buffers.clear()
        self._curves.clear()
        self._output_checks.clear()
        self._frame_count = 0
        self._num_outputs = 0
        self.plot_widget.clear()
        self._clear_checkboxes()
        self._output_info.setText("Waiting for acquisition data...")

    def _init_plots(self, num_outputs: int):
        self.reset_plots()
        self._num_outputs = num_outputs
        self._output_info.setText(f"Outputs: {num_outputs}")
        n_seconds = max(10, self._duration if self._duration > 0 else 10)
        maxlen = n_seconds * self._fphase
        for i in range(num_outputs):
            self._phase_buffers.append(collections.deque(maxlen=maxlen))
            self._time_buffers.append(collections.deque(maxlen=maxlen))
            name = self._output_names[i] if i < len(self._output_names) else f"ch{i}"
            curve = self.plot_widget.plot(
                pen=pg.mkPen(COLORS[i % len(COLORS)], width=1.5),
                name=name,
            )
            self._curves.append(curve)
            checkbox = QCheckBox(name)
            checkbox.setChecked(True)
            checkbox.toggled.connect(self._update_visibility)
            self._output_layout.addWidget(checkbox)
            self._output_checks.append(checkbox)

    def on_phase_data(self, phases: np.ndarray):
        if self._num_outputs == 0:
            self._init_plots(phases.shape[0])
        elif self._num_outputs != phases.shape[0]:
            self._init_plots(phases.shape[0])

        timestamp = self._frame_count / self._fphase
        self._frame_count += 1

        for i in range(phases.shape[0]):
            self._time_buffers[i].append(timestamp)
            self._phase_buffers[i].append(phases[i])
            self._curves[i].setData(
                np.array(self._time_buffers[i]),
                np.array(self._phase_buffers[i]),
            )

    def _clear_checkboxes(self):
        for i in reversed(range(self._output_layout.count())):
            item = self._output_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QCheckBox):
                item.widget().deleteLater()

    def _update_visibility(self):
        for i in range(self._num_outputs):
            if self._output_checks[i].isChecked():
                self._curves[i].show()
            else:
                self._curves[i].hide()
