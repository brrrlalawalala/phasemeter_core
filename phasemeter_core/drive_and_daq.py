from queue import Queue

from .data_acquisitor import DataAcquisitor
from .data_writer import DataWriter
from .hexapod_controller import HexapodController


def drive_and_daq(
    filename: str,
    time: int,
    wave_generator_id: int,
    wave_table_id: int,
    num_periods: int,
):
    q = Queue()
    with (
        DataAcquisitor(q) as data_acquisitor,
        DataWriter(q, filename=filename, time=time) as data_writer,
        HexapodController() as hexapod_controller,
    ):
        print(
            "Preparing synchronized wave generation and acquisition. "
            f"Planned acquisition time: {time} s. Press Ctrl+C to stop."
        )
        hexapod_controller.config_wave_generator(
            wave_generator_id=wave_generator_id,
            wave_table_id=wave_table_id,
            num_periods=num_periods,
        )
        hexapod_controller.start_wave_generator(wave_generator_id=wave_generator_id)
        data_acquisitor.start()
        try:
            while not data_writer.stop_event.is_set():
                data_acquisitor.read_and_process()
        except KeyboardInterrupt:
            print("Acquisition interrupted by user.")
            data_writer.is_interrupted = True

    if not data_writer.is_interrupted:
        print(f'{time} s acquisition completed. Data saved to "{filename}".')
