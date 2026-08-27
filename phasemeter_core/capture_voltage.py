import argparse
import os

import h5py
import numpy as np
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogMultiChannelReader

from . import config


def capture_voltage(filename: str, time: int, fs: int = 10000):
    """Capture raw voltage signals and save them to an HDF5 file."""
    if time < 1:
        raise ValueError("Capture time must be at least 1 second.")
    if fs < 1:
        raise ValueError("Sampling rate must be positive.")

    filename = filename if filename.endswith(".h5") else filename + ".h5"
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    n_per_block = fs

    with h5py.File(filename, "w") as h5_file:
        h5_file.create_dataset(
            "dataset",
            shape=(config.NUM_CHANNELS, 0),
            maxshape=(config.NUM_CHANNELS, None),
            chunks=(config.NUM_CHANNELS, n_per_block),
            dtype=np.float64,
        )

        with nidaqmx.Task() as task:
            for channel in config.CHANNELS:
                task.ai_channels.add_ai_voltage_chan(channel)
            task.timing.cfg_samp_clk_timing(
                rate=fs,
                sample_mode=AcquisitionType.CONTINUOUS,
                samps_per_chan=fs,
            )
            reader = AnalogMultiChannelReader(task.in_stream)
            task.start()
            print(
                f"Capturing voltage for {time} s at {fs} Hz "
                f"from {config.NUM_CHANNELS} channels. Press Ctrl+C to stop."
            )

            buffer = np.zeros((config.NUM_CHANNELS, n_per_block), dtype=np.float64)
            try:
                for _ in range(time):
                    reader.read_many_sample(
                        buffer,
                        number_of_samples_per_channel=n_per_block,
                        timeout=1,
                    )
                    dataset = h5_file["dataset"]
                    old_size = dataset.shape[1]
                    new_size = old_size + n_per_block
                    dataset.resize((dataset.shape[0], new_size))
                    dataset[:, old_size:new_size] = buffer
                    h5_file.flush()
            except KeyboardInterrupt:
                print("Capture interrupted by user.")
            else:
                print(f'Captured {time} s of voltage data to "{filename}".')


def main():
    parser = argparse.ArgumentParser(
        description="Capture raw voltage signals and save them to an HDF5 file."
    )
    parser.add_argument("filename", help="Output HDF5 filename.")
    parser.add_argument("time", type=int, help="Capture duration in seconds.")
    parser.add_argument(
        "--fs",
        type=int,
        default=10000,
        help="Sampling rate in Hz. Defaults to 10000.",
    )
    args = parser.parse_args()
    capture_voltage(args.filename, args.time, fs=args.fs)


if __name__ == "__main__":
    main()
