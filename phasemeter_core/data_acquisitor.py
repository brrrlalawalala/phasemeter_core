# data_acquisitor.py

import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogMultiChannelReader
import numpy as np
from queue import Queue

from . import config
from .phase_demodulator import PhaseDemodulator

class DataAcquisitor:
    def __init__(self, output_queue: Queue):
        self.output_queue = output_queue  # 相位序列将输出到队列 output_queue
        self.phase_demodulator = PhaseDemodulator()
        self.voltages = np.zeros((config.NUM_CHANNELS, config.N_PER_PHASE), dtype=np.float64)  # 缓冲区
        self.task = nidaqmx.Task()  # 创建 DAQmx 任务
        for ch in config.CHANNELS:  # 添加通道
            self.task.ai_channels.add_ai_voltage_chan(ch)
        self.task.timing.cfg_samp_clk_timing(rate=config.F_SAMP, sample_mode=AcquisitionType.CONTINUOUS)  # 设置采样率; 设置采样模式为连续采集
        self.reader = AnalogMultiChannelReader(self.task.in_stream)

    def read_and_process(self):
        '''读取电压信号, 处理后输出一次相位.'''
        self.reader.read_many_sample(self.voltages, number_of_samples_per_channel=config.N_PER_PHASE, timeout=1)  # 读取电压信号, 存储到 self.voltages
        phases = self.phase_demodulator.demodulate_phase(self.voltages)
        self.output_queue.put(phases.copy())  # 相位数组 (长度为 NUM_CHANNELS) 整体作为单个元素添加到 output_queue 末尾

    def start(self):
        self.task.start()

    def close(self):
        self.task.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()