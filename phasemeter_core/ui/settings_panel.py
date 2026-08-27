from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import config as cfg
from ..derived_channels import DerivedChannel, SafeExpression
from .settings import Settings


class SettingsPanel(QWidget):
    request_start = Signal(Settings)
    request_stop = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_settings()
        self._on_filename_changed()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        form_group = QGroupBox("Acquisition")
        form = QFormLayout(form_group)
        form.setSpacing(4)

        self._device_edit = QLineEdit()
        self._device_edit.setPlaceholderText(f"e.g. {cfg.DEVICE_NAME}")
        form.addRow("Device:", self._device_edit)

        self._channels_edit = QLineEdit()
        self._channels_edit.setPlaceholderText("comma-separated, e.g. " + ", ".join(cfg.CHANNEL_NAMES))
        form.addRow("Channels:", self._channels_edit)

        self._fhet_spin = QSpinBox()
        self._fhet_spin.setRange(1, 1_000_000)
        form.addRow("F_HET (Hz):", self._fhet_spin)

        self._fsamp_spin = QSpinBox()
        self._fsamp_spin.setRange(1000, 10_000_000)
        form.addRow("F_SAMP (Hz):", self._fsamp_spin)

        self._fphase_spin = QSpinBox()
        self._fphase_spin.setRange(1, 100_000)
        form.addRow("F_PHASE (Hz):", self._fphase_spin)

        self._filename_edit = QLineEdit()
        self._filename_edit.setPlaceholderText("leave empty to disable saving")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        self._filename_edit.textChanged.connect(self._on_filename_changed)

        file_row = QHBoxLayout()
        file_row.addWidget(self._filename_edit)
        file_row.addWidget(browse_btn)
        form.addRow("Save file:", file_row)

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(0, 999999)
        self._duration_spin.setSpecialValueText("Infinite")
        form.addRow("Duration (s):", self._duration_spin)

        derived_group = QGroupBox("Derived Channels")
        derived_layout = QVBoxLayout(derived_group)
        self._derived_table = QTableWidget(0, 3)
        self._derived_table.setHorizontalHeaderLabels(["On", "Name", "Expression"])
        self._derived_table.horizontalHeader().setStretchLastSection(True)
        self._derived_table.verticalHeader().setVisible(False)
        self._derived_table.setSelectionBehavior(QTableWidget.SelectRows)
        derived_layout.addWidget(self._derived_table)

        self._derived_name_edit = QLineEdit()
        self._derived_name_edit.setPlaceholderText("name")
        self._derived_expr_edit = QLineEdit()
        self._derived_expr_edit.setPlaceholderText("ai0 - ai1")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_derived_channel)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected_derived_channels)

        add_row = QHBoxLayout()
        add_row.addWidget(self._derived_name_edit)
        add_row.addWidget(self._derived_expr_edit)
        add_row.addWidget(add_btn)
        add_row.addWidget(remove_btn)
        derived_layout.addLayout(add_row)

        self._start_btn = QPushButton("Start")
        self._start_btn.setMinimumHeight(32)
        self._start_btn.clicked.connect(self._on_start)

        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setMinimumHeight(32)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)

        self._status_label = QLabel("Status: Ready")

        main_layout.addWidget(form_group)
        main_layout.addWidget(derived_group)
        main_layout.addWidget(self._start_btn)
        main_layout.addWidget(self._stop_btn)
        main_layout.addWidget(self._status_label)
        self.setFixedWidth(360)

    def _load_settings(self):
        settings = Settings.load()
        self._device_edit.setText(settings.device_name)
        self._channels_edit.setText(", ".join(settings.channel_names))
        self._fhet_spin.setValue(settings.f_het)
        self._fsamp_spin.setValue(settings.f_samp)
        self._fphase_spin.setValue(settings.f_phase)
        self._filename_edit.setText(settings.filename)
        self._duration_spin.setValue(settings.duration)
        for channel in settings.derived_channels:
            self._append_derived_channel(channel)

    def get_settings(self) -> Settings:
        raw_channels = self._channels_edit.text().strip()
        channel_names = [channel.strip() for channel in raw_channels.split(",") if channel.strip()]
        return Settings(
            device_name=self._device_edit.text().strip(),
            channel_names=channel_names,
            derived_channels=self._get_derived_channels(),
            f_samp=self._fsamp_spin.value(),
            f_phase=self._fphase_spin.value(),
            f_het=self._fhet_spin.value(),
            filename=self._filename_edit.text().strip(),
            duration=self._duration_spin.value() if self._filename_edit.text().strip() else 0,
        )

    def set_controls_enabled(self, enabled: bool):
        for widget in [
            self._device_edit,
            self._channels_edit,
            self._fhet_spin,
            self._fsamp_spin,
            self._fphase_spin,
            self._filename_edit,
            self._derived_table,
            self._derived_name_edit,
            self._derived_expr_edit,
        ]:
            widget.setEnabled(enabled)
        self._duration_spin.setEnabled(enabled and bool(self._filename_edit.text().strip()))
        self._start_btn.setEnabled(enabled)
        self._stop_btn.setEnabled(not enabled)

    def set_status(self, text: str):
        self._status_label.setText(f"Status: {text}")

    def _append_derived_channel(self, channel: DerivedChannel):
        row = self._derived_table.rowCount()
        self._derived_table.insertRow(row)

        checkbox = QCheckBox()
        checkbox.setChecked(channel.enabled)
        self._derived_table.setCellWidget(row, 0, checkbox)
        self._derived_table.setItem(row, 1, QTableWidgetItem(channel.name))
        self._derived_table.setItem(row, 2, QTableWidgetItem(channel.expression))

    def _get_derived_channels(self) -> list[DerivedChannel]:
        channels = []
        for row in range(self._derived_table.rowCount()):
            checkbox = self._derived_table.cellWidget(row, 0)
            name_item = self._derived_table.item(row, 1)
            expr_item = self._derived_table.item(row, 2)
            name = name_item.text().strip() if name_item else ""
            expression = expr_item.text().strip() if expr_item else ""
            if name and expression:
                channels.append(DerivedChannel(name, expression, checkbox.isChecked()))
        return channels

    def _add_derived_channel(self):
        name = self._derived_name_edit.text().strip()
        expression = self._derived_expr_edit.text().strip()
        if not name or not expression:
            QMessageBox.warning(self, "Invalid channel", "Enter both a name and an expression.")
            return
        self._append_derived_channel(DerivedChannel(name, expression, True))
        self._derived_name_edit.clear()
        self._derived_expr_edit.clear()

    def _remove_selected_derived_channels(self):
        rows = sorted({item.row() for item in self._derived_table.selectedItems()}, reverse=True)
        for row in rows:
            self._derived_table.removeRow(row)

    def _on_filename_changed(self, text: str = ""):
        self._duration_spin.setEnabled(bool((text or self._filename_edit.text()).strip()))

    def _browse_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "HDF5 files (*.h5)")
        if path:
            self._filename_edit.setText(path)

    def _on_start(self):
        settings = self.get_settings()
        error = self._validate_settings(settings)
        if error:
            QMessageBox.warning(self, "Invalid settings", error)
            return

        settings.save()
        self.set_controls_enabled(False)
        self.set_status("Acquiring...")
        self.request_start.emit(settings)

    def _validate_settings(self, settings: Settings) -> str:
        if not settings.device_name:
            return "Please enter a device name."
        if not settings.channel_names:
            return "Please enter at least one channel."
        if len(settings.channel_names) != len(set(settings.channel_names)):
            return "Real channel names must be unique."
        if settings.f_samp % settings.f_phase != 0:
            return "F_SAMP must be divisible by F_PHASE."
        if settings.f_samp % settings.f_het != 0:
            return "F_SAMP must be divisible by F_HET."

        names = set(settings.channel_names)
        derived_names = set()
        for channel in settings.derived_channels:
            if not channel.name.isidentifier():
                return f"Invalid derived channel name: {channel.name}"
            if channel.name in names or channel.name in derived_names:
                return f"Duplicate channel name: {channel.name}"
            derived_names.add(channel.name)
            if channel.enabled:
                try:
                    SafeExpression(channel.expression, names)
                except ValueError as e:
                    return f"{channel.name}: {e}"
        return ""

    def _on_stop(self):
        self.request_stop.emit()
        self.set_status("Stopping...")
