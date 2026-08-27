import json
from dataclasses import dataclass, field

from PySide6.QtCore import QSettings

from .. import config as cfg
from ..derived_channels import DerivedChannel


@dataclass
class Settings:
    device_name: str = cfg.DEVICE_NAME
    channel_names: list[str] = field(default_factory=lambda: cfg.CHANNEL_NAMES.copy())
    derived_channels: list[DerivedChannel] = field(default_factory=list)
    f_samp: int = cfg.F_SAMP
    f_phase: int = cfg.F_PHASE
    f_het: int = cfg.F_HET
    filename: str = ""
    duration: int = 60

    @classmethod
    def load(cls) -> "Settings":
        settings = QSettings("phasemeter_core", "phasemeter_core")
        return cls(
            device_name=settings.value("device_name", cfg.DEVICE_NAME),
            channel_names=_load_channel_names(settings),
            derived_channels=_load_derived_channels(settings),
            f_samp=int(settings.value("f_samp", cfg.F_SAMP)),
            f_phase=int(settings.value("f_phase", cfg.F_PHASE)),
            f_het=int(settings.value("f_het", cfg.F_HET)),
            filename=settings.value("filename", ""),
            duration=int(settings.value("duration", 60)),
        )

    def save(self):
        settings = QSettings("phasemeter_core", "phasemeter_core")
        settings.setValue("device_name", self.device_name)
        settings.setValue("channel_names", self.channel_names)
        settings.setValue("derived_channels", json.dumps([
            {
                "name": channel.name,
                "expression": channel.expression,
                "enabled": channel.enabled,
            }
            for channel in self.derived_channels
        ]))
        settings.setValue("f_samp", self.f_samp)
        settings.setValue("f_phase", self.f_phase)
        settings.setValue("f_het", self.f_het)
        settings.setValue("filename", self.filename)
        settings.setValue("duration", self.duration)


def _load_channel_names(settings: QSettings) -> list[str]:
    raw = settings.value("channel_names", cfg.CHANNEL_NAMES)
    if isinstance(raw, str):
        return [channel.strip() for channel in raw.split(",") if channel.strip()]
    return list(raw or cfg.CHANNEL_NAMES)


def _load_derived_channels(settings: QSettings) -> list[DerivedChannel]:
    raw = settings.value("derived_channels", "[]")
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return [
        DerivedChannel(
            name=str(item.get("name", "")).strip(),
            expression=str(item.get("expression", "")).strip(),
            enabled=bool(item.get("enabled", True)),
        )
        for item in data
        if item.get("name") and item.get("expression")
    ]
