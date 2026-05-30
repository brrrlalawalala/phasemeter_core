# daq.py

'''读取来自采集卡的电压数据, 处理得到相位数据, 然后保存到指定文件.'''

from queue import Queue

from .data_acquisitor import DataAcquisitor
from .data_writer import DataWriter

def daq(filename: str, time: int):
    q = Queue()  # 用于存放相位数据
    with DataAcquisitor(q) as data_acquisitor, DataWriter(q, filename=filename, time=time) as data_writer:
        data_acquisitor.start()
        print(f'开始连续采集. 计划采集时间 {time} 秒. 按 Ctrl+C 停止.')
        try:
            while not data_writer.stop_event.is_set():
                data_acquisitor.read_and_process()
        except KeyboardInterrupt:
            print('用户中断采集.')
            data_writer.is_interrupted = True
    if not data_writer.is_interrupted:
        print(f'{time} 秒采集完成. 数据已保存至文件 "{filename}".')