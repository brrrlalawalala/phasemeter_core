import os
import threading
from queue import Empty, Queue

import h5py
import numpy as np

from . import config


class DataWriter:
    """Write phase samples from a queue into an HDF5 file."""

    def __init__(self, input_queue: Queue, filename: str, time: int = None):
        self.input_queue = input_queue
        self.max_time = time
        assert self.max_time is None or self.max_time >= 1, (
            "Acquisition time must be at least 1 second."
        )
        self.time = 0
        self.filename = filename if filename.endswith(".h5") else filename + ".h5"
        self.num_outputs = getattr(config, "NUM_OUTPUTS", config.NUM_CHANNELS)
        self.buffer = np.zeros((self.num_outputs, config.F_PHASE), dtype=np.float64)
        self.buffer_index = 0
        self.is_interrupted = False
        self.thread = None
        self.stop_event = threading.Event()
        self.init_h5_file()

    def init_h5_file(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
        with h5py.File(self.filename, "w") as h5_file:
            max_shape = (
                (self.num_outputs, config.F_PHASE * self.max_time)
                if self.max_time
                else (self.num_outputs, None)
            )
            chunk_size = (self.num_outputs, config.F_PHASE)
            h5_file.create_dataset(
                "dataset",
                shape=(self.num_outputs, 0),
                maxshape=max_shape,
                chunks=chunk_size,
                dtype=np.float64,
            )

    def write(self):
        try:
            while not self.stop_event.is_set():
                try:
                    data = self.input_queue.get(timeout=0.1)
                    self.buffer[:, self.buffer_index] = data
                    self.buffer_index += 1
                    if self.buffer_index >= config.F_PHASE:
                        self.flush_buffer(self.buffer)
                        self.buffer_index = 0
                        self.time += 1
                    if self.max_time and self.time >= self.max_time:
                        self.stop_event.set()
                except Empty:
                    continue
        except Exception as e:
            print(f"Write error: {e}.")
        finally:
            if self.buffer_index:
                self.flush_buffer(self.buffer[:, : self.buffer_index])
                self.buffer_index = 0

    def flush_buffer(self, buffer):
        with h5py.File(self.filename, "a") as h5_file:
            dataset = h5_file["dataset"]
            old_size = dataset.shape[1]
            new_size = old_size + buffer.shape[1]
            dataset.resize((dataset.shape[0], new_size))
            dataset[:, old_size:new_size] = buffer

    def start(self):
        self.thread = threading.Thread(target=self.write)
        self.thread.start()

    def close(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
