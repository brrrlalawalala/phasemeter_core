# read_h5_file.py

'''读取 h5 文件中的数据, 存为 ndarray.'''

import h5py
import numpy as np

def read_h5_file(filename: str):
    with h5py.File(filename, 'r') as f:
        data = np.array(f['dataset'])
        print(f'文件 "{filename}" 中数据的形状是 {data.shape}.')
    return data