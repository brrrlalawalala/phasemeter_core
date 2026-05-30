# config.py

import numpy as np

F_HET = 10_000  # 外差频率
F_SAMP = 500_000  # 每通道的采样频率
F_PHASE = 5_000  # 相位的输出频率
assert F_SAMP % F_PHASE == 0, 'F_SAMP 应是 F_PHASE 的整数倍.'
N_PER_PHASE = int(F_SAMP / F_PHASE)  # 每 N_PER_PHASE 点计算一次相位
REF = np.exp(-1j*2*np.pi * np.arange(int(F_SAMP/F_PHASE)) / int(F_SAMP/F_HET))  # 用于相位解调算法
DEVICE_NAME = 'USB-6453'
# CHANNEL_NAMES = ['ai0', 'ai16']
CHANNEL_NAMES = ['ai0', 'ai1', 'ai2', 'ai3', 'ai4', 'ai5', 'ai6', 'ai7', 'ai16']
CHANNELS = [f"{DEVICE_NAME}/{ch}" for ch in CHANNEL_NAMES]
NUM_CHANNELS = len(CHANNELS)