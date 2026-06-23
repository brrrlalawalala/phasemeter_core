# data_writer.py

import os
import h5py
import numpy as np
from queue import Queue, Empty
import threading

from . import config

class DataWriter:
    '''在子线程中把 input_queue 中的数据写入指定文件.'''

    def __init__(self, input_queue: Queue, filename: str, time: int = None):
        self.input_queue = input_queue  # 从 input_queue 读取相位数据
        self.max_time = time  # 读取时长, 单位为秒, 到达后停止读取
        assert self.max_time is None or self.max_time >= 1, '读数时长至少为 1 秒.'
        self.time = 0  # 计时器
        self.filename = filename if filename.endswith('.h5') else filename + '.h5'  # 文件名, 后缀为 .h5
        self.buffer = np.zeros((config.NUM_CHANNELS, config.F_PHASE), dtype=np.float64)  # 用于暂存数据, 每隔 1 s 批量写入一次
        self.buffer_index = 0
        self.is_interrupted = False
        self.thread = None
        self.stop_event = threading.Event()
        self.init_h5_file()

    def init_h5_file(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.filename)), exist_ok=True)
        with h5py.File(self.filename, 'w') as f:
            max_shape = (config.NUM_CHANNELS, config.F_PHASE*self.max_time) if self.max_time else (config.NUM_CHANNELS, None)
            chunk_size = (config.NUM_CHANNELS, config.F_PHASE)
            f.create_dataset('dataset', shape=(config.NUM_CHANNELS, 0), maxshape=max_shape, chunks=chunk_size, dtype=np.float64)

    def write(self):
        '''从 input_queue 连续读取数据, 每秒一次存入目标文件.'''
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
            print(f'写入错误: {e}.')

    def flush_buffer(self, buffer):
        '''将 buffer 中的全部数据添加至目标文件末尾.'''
        with h5py.File(self.filename, 'a') as f:
            dataset = f['dataset']
            old_size = dataset.shape[1]
            new_size = old_size + config.F_PHASE
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