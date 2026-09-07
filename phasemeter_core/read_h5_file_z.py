import h5py
import numpy as np


def read_h5_file_z(filename: str):
    with h5py.File(filename, "r") as f:
        data = np.array(f["z"])
        print(f'File "{filename}" z dataset shape is {data.shape}.')
    return data
