from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QMessageBox, QSplitter, QTabWidget

from .acquisition_tab import AcquisitionTab
from .settings_panel import SettingsPanel
from .voltage_tab import VoltageTab
from .worker import AcquisitionThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("phasemeter_core")
        self.resize(1400, 900)
        self._worker = None

        self._build_menu()
        self._build_central()
        self._build_statusbar()

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File(&F)")
        file_menu.addAction("Quit(&Q)", self.close, Qt.CTRL | Qt.Key_Q)
        help_menu = menubar.addMenu("Help(&H)")
        help_menu.addAction("About(&A)", self._show_about)

    def _build_central(self):
        splitter = QSplitter(Qt.Horizontal)

        self._settings_panel = SettingsPanel()
        self._settings_panel.request_start.connect(self._start_acquisition)
        self._settings_panel.request_stop.connect(self._stop_acquisition)
        splitter.addWidget(self._settings_panel)

        self._tab_widget = QTabWidget()
        self.volt_tab = VoltageTab()
        self._tab_widget.addTab(self.volt_tab, "Voltage")
        self.phase_tab = AcquisitionTab()
        self._tab_widget.addTab(self.phase_tab, "Phase")
        splitter.addWidget(self._tab_widget)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def _build_statusbar(self):
        self._status_bar = self.statusBar()
        self._status_bar.showMessage("Ready")

    def _show_about(self):
        QMessageBox.about(
            self,
            "About phasemeter_core",
            "phasemeter_core v0.1.0\n\n"
            "Realtime voltage acquisition and per-channel phase demodulation.",
        )

    def _start_acquisition(self, settings):
        if self._worker is not None:
            return

        output_names = settings.channel_names + [
            channel.name for channel in settings.derived_channels if channel.enabled
        ]

        self.volt_tab.set_sampling_info(settings.f_samp)
        self.volt_tab.set_channel_names(settings.channel_names)
        self.phase_tab.set_phase_params(settings.f_phase, settings.duration)
        self.phase_tab.set_output_names(output_names)

        self._worker = AcquisitionThread(settings)
        self._worker.phase_ready.connect(self.phase_tab.on_phase_data)
        self._worker.voltage_ready.connect(self.volt_tab.on_voltage_data)
        self._worker.completed.connect(self._on_acquisition_completed)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

        self._settings_panel.set_status(f"Acquiring from {settings.device_name}")
        self._status_bar.showMessage(f"Acquiring -> {settings.filename or '(not saved)'}")

    def _stop_acquisition(self):
        if self._worker is None:
            self._settings_panel.set_controls_enabled(True)
            self._settings_panel.set_status("Ready")
            return

        self._worker.stop()
        if not self._worker.wait(5000):
            self._worker.terminate()
            self._worker.wait()

        self._cleanup_worker()
        self._settings_panel.set_controls_enabled(True)
        self._settings_panel.set_status("Stopped")
        self._status_bar.showMessage("Stopped")

    def _on_acquisition_completed(self):
        self._cleanup_worker()
        self._settings_panel.set_controls_enabled(True)
        self._settings_panel.set_status("Acquisition completed")
        self._status_bar.showMessage("Acquisition completed")

    def _on_error(self, message: str):
        self._cleanup_worker()
        self._settings_panel.set_controls_enabled(True)
        self._settings_panel.set_status("Error")
        self._status_bar.showMessage("Error")
        QMessageBox.critical(self, "Acquisition error", message)

    def _cleanup_worker(self):
        if self._worker is not None:
            try:
                if self._worker.isRunning():
                    self._worker.stop()
                    self._worker.wait(2000)
            except RuntimeError:
                pass
            self._worker.deleteLater()
            self._worker = None

    def closeEvent(self, event):
        self._stop_acquisition()
        super().closeEvent(event)
