from pipython import GCSDevice, pitools


class HexapodController:
    """Control a PI hexapod controller."""

    def __init__(self):
        self.pidevice = None

    def connect(self):
        self.pidevice = GCSDevice()
        self.pidevice.ConnectRS232(comport=16, baudrate=115200)
        print("Controller connected.")
        pitools.startup(self.pidevice, refmodes="FRF")
        print("Controller initialized.")

    def disconnect(self):
        if self.pidevice and self.pidevice.IsConnected():
            pitools.stopall(self.pidevice)
        self.pidevice.CloseConnection()
        print("Controller disconnected.")

    def config_wave_generator(
        self, wave_generator_id: int, wave_table_id: int, num_periods: int
    ):
        self.pidevice.WSL(wave_generator_id, wave_table_id)
        self.pidevice.WGC(wave_generator_id, num_periods)

    def start_wave_generator(self, wave_generator_id: int):
        self.pidevice.WGO(wave_generator_id, 1)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
