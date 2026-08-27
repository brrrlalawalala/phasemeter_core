from queue import Queue

import numpy as np
from PySide6.QtCore import QThread, Signal

from .. import config as cfg
from ..derived_channels import DerivedChannelSet
from ..phase_demodulator import PhaseDemodulator
from .settings import Settings


class AcquisitionThread(QThread):
    phase_ready = Signal(np.ndarray)
    voltage_ready = Signal(np.ndarray)
    completed = Signal()
    error_occurred = Signal(str)

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._running = False
        self._failed = False

    def stop(self):
        self._running = False

    def run(self):
        self._apply_settings()

        import nidaqmx
        from nidaqmx.constants import AcquisitionType
        from nidaqmx.stream_readers import AnalogMultiChannelReader

        task = None
        writer = None
        try:
            task = nidaqmx.Task()
            for channel in cfg.CHANNELS:
                task.ai_channels.add_ai_voltage_chan(channel)
            task.timing.cfg_samp_clk_timing(
                rate=cfg.F_SAMP,
                sample_mode=AcquisitionType.CONTINUOUS,
                samps_per_chan=cfg.F_SAMP,
            )
            reader = AnalogMultiChannelReader(task.in_stream)
            voltages = np.zeros((cfg.NUM_CHANNELS, cfg.N_PER_PHASE), dtype=np.float64)
            demodulator = PhaseDemodulator()
            derived_channels = DerivedChannelSet(
                self._settings.derived_channels,
                self._settings.channel_names,
            )

            if self._settings.filename:
                from ..data_writer import DataWriter

                writer = DataWriter(
                    Queue(),
                    filename=self._settings.filename,
                    time=self._settings.duration if self._settings.duration > 0 else None,
                )
                writer.start()

            task.start()
            self._running = True

            elapsed_frames = 0
            max_frames = (
                self._settings.duration * cfg.F_PHASE
                if self._settings.duration > 0
                else None
            )

            while self._running:
                try:
                    reader.read_many_sample(
                        voltages,
                        number_of_samples_per_channel=cfg.N_PER_PHASE,
                        timeout=0.5,
                    )
                except nidaqmx.errors.DaqError as e:
                    if e.error_code != -200299:
                        raise
                    continue

                self.voltage_ready.emit(voltages.copy())
                real_phases = demodulator.demodulate_phase(voltages)
                derived_phases = derived_channels.evaluate(real_phases)
                phases = np.concatenate((real_phases, derived_phases))
                self.phase_ready.emit(phases.copy())

                if writer is not None:
                    writer.input_queue.put(phases.copy())

                elapsed_frames += 1
                if max_frames is not None and elapsed_frames >= max_frames:
                    break

        except Exception as e:
            self._failed = True
            self.error_occurred.emit(str(e))
        finally:
            self._running = False
            if task is not None:
                try:
                    task.close()
                except Exception:
                    pass
            if writer is not None:
                writer.close()
            if not self._failed:
                self.completed.emit()

    def _apply_settings(self):
        cfg.F_SAMP = self._settings.f_samp
        cfg.F_PHASE = self._settings.f_phase
        cfg.F_HET = self._settings.f_het
        cfg.N_PER_PHASE = int(cfg.F_SAMP / cfg.F_PHASE)
        cfg.REF = np.exp(
            -1j * 2 * np.pi * np.arange(cfg.N_PER_PHASE)
            / int(cfg.F_SAMP / cfg.F_HET)
        )
        cfg.DEVICE_NAME = self._settings.device_name
        cfg.CHANNEL_NAMES = self._settings.channel_names.copy()
        cfg.CHANNELS_NAME = cfg.CHANNEL_NAMES
        cfg.CHANNELS = [f"{cfg.DEVICE_NAME}/{channel}" for channel in cfg.CHANNEL_NAMES]
        cfg.NUM_CHANNELS = len(cfg.CHANNELS)
        cfg.NUM_OUTPUTS = cfg.NUM_CHANNELS + len(
            [channel for channel in self._settings.derived_channels if channel.enabled]
        )
