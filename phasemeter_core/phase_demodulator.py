# phase_demodulation.py

import numpy as np

from . import config

class PhaseDemodulator:
    def __init__(self):
        self.phase_offsets = np.zeros(config.NUM_CHANNELS)  # 相位的偏移量, 是 2 pi 的整数倍
        self.last_phases = np.zeros(config.NUM_CHANNELS)  # 存储上一组相位解缠后的值

    def demodulate_phase(self, data: np.ndarray):
        '''相位解调算法.

        解缠算法有效的前提是相位的变化速率小于 F_PHASE * pi / s.

        参数:
            data: 矩阵, 尺寸为 NUM_CHANNELS * N_PER_PHASE.

        返回值:
            phases: 数组, 长度为 NUM_CHANNELS.
        '''
        # 相位解调, SBDFT 算法
        z = np.dot(data, config.REF)
        phases = np.angle(z)

        # 相位解缠
        delta_phases = phases + self.phase_offsets - self.last_phases  # 用上一组偏移量解缠, 比较得到的结果与上一组解缠后的相位, 若有跳变则更新偏移量的值
        for n in range(config.NUM_CHANNELS):
            if delta_phases[n] > np.pi:
                self.phase_offsets[n] -= 2*np.pi
            elif delta_phases[n] < -np.pi:
                self.phase_offsets[n] += 2*np.pi
        phases += self.phase_offsets
        self.last_phases = phases.copy()

        return phases