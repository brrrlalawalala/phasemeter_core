from collections.abc import Sequence
from queue import Queue

from .data_acquisitor import DataAcquisitor
from .data_writer import DataWriter
from .hexapod_controller import HexapodController


def drive_and_daq(
    filename: str,
    time: int,
    wave_generator_id: int | Sequence[int],
    wave_table_id: int | Sequence[int],
    num_periods: int | Sequence[int],
    save_z: bool = False,
):
    """Drive one or more wave generators while acquiring phase data.

    For multi-DOF motion, pass corresponding sequences for
    ``wave_generator_id`` and ``wave_table_id``. All generators are started in
    one WGO command so their output begins in the same controller servo cycle.
    ``num_periods`` may be a scalar shared by every generator or a matching
    sequence.
    """
    q = Queue()
    with (
        DataAcquisitor(q, save_z=save_z) as data_acquisitor,
        DataWriter(q, filename=filename, time=time, save_z=save_z) as data_writer,
        HexapodController() as hexapod_controller,
    ):
        print(
            "Preparing synchronized wave generation and acquisition. "
            f"Planned acquisition time: {time} s. Press Ctrl+C to stop."
        )
        hexapod_controller.config_wave_generators(
            wave_generator_ids=wave_generator_id,
            wave_table_ids=wave_table_id,
            num_periods=num_periods,
        )
        hexapod_controller.start_wave_generators(
            wave_generator_ids=wave_generator_id
        )
        data_acquisitor.start()
        try:
            while not data_writer.stop_event.is_set():
                data_acquisitor.read_and_process()
        except KeyboardInterrupt:
            print("Acquisition interrupted by user.")
            data_writer.is_interrupted = True

    if not data_writer.is_interrupted:
        print(f'{time} s acquisition completed. Data saved to "{filename}".')
