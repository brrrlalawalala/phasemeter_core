from collections.abc import Sequence

from .hexapod_controller import HexapodController


def start_wave_generator(
    wave_generator_ids: int | Sequence[int],
    wave_table_ids: int | Sequence[int],
    num_periods: int | Sequence[int],
) -> HexapodController:
    """Connect, configure, and synchronously start one or more generators.

    The returned controller remains connected so that wave output is not
    stopped immediately. Call ``controller.disconnect()`` when the motion
    should be stopped and the connection released.
    """
    controller = HexapodController()
    try:
        controller.connect()
        controller.config_wave_generators(
            wave_generator_ids=wave_generator_ids,
            wave_table_ids=wave_table_ids,
            num_periods=num_periods,
        )
        controller.start_wave_generators(wave_generator_ids=wave_generator_ids)
    except BaseException:
        controller.disconnect()
        raise
    return controller
