from collections.abc import Sequence

from pipython import GCSDevice, pitools


def _as_int_list(value: int | Sequence[int], name: str) -> list[int]:
    """Return one or more integer command arguments as a list."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must contain integers, not bool values")
    if isinstance(value, int):
        return [value]
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an integer or a sequence of integers")

    values = list(value)
    if not values:
        raise ValueError(f"{name} must not be empty")
    if any(isinstance(item, bool) or not isinstance(item, int) for item in values):
        raise TypeError(f"{name} must contain only integers")
    return values


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

    def config_wave_generators(
        self,
        wave_generator_ids: int | Sequence[int],
        wave_table_ids: int | Sequence[int],
        num_periods: int | Sequence[int],
    ) -> None:
        """Configure one or more wave generators in two controller commands.

        A scalar ``num_periods`` is applied to every generator. When sequences
        are provided, their items correspond by position.
        """
        generator_ids = _as_int_list(wave_generator_ids, "wave_generator_ids")
        table_ids = _as_int_list(wave_table_ids, "wave_table_ids")

        if len(generator_ids) != len(table_ids):
            raise ValueError(
                "wave_generator_ids and wave_table_ids must have the same length"
            )
        if len(set(generator_ids)) != len(generator_ids):
            raise ValueError("wave_generator_ids must not contain duplicates")

        if isinstance(num_periods, int) and not isinstance(num_periods, bool):
            periods = [num_periods] * len(generator_ids)
        else:
            periods = _as_int_list(num_periods, "num_periods")
            if len(generator_ids) != len(periods):
                raise ValueError(
                    "num_periods must be a scalar or have the same length as "
                    "wave_generator_ids"
                )

        self.pidevice.WSL(generator_ids, table_ids)
        self.pidevice.WGC(generator_ids, periods)

    def start_wave_generator(self, wave_generator_id: int):
        self.pidevice.WGO(wave_generator_id, 1)

    def start_wave_generators(
        self, wave_generator_ids: int | Sequence[int]
    ) -> None:
        """Start all specified generators synchronously in one WGO command."""
        generator_ids = _as_int_list(wave_generator_ids, "wave_generator_ids")
        if len(set(generator_ids)) != len(generator_ids):
            raise ValueError("wave_generator_ids must not contain duplicates")
        self.pidevice.WGO(generator_ids, [1] * len(generator_ids))

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
