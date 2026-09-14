import unittest
from unittest.mock import patch

from phasemeter_core.drive_and_daq import drive_and_daq


class AlreadyStoppedEvent:
    def is_set(self):
        return True


class FakeContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class FakeDataAcquisitor(FakeContextManager):
    def __init__(self, *args, **kwargs):
        self.started = False

    def start(self):
        self.started = True


class FakeDataWriter(FakeContextManager):
    def __init__(self, *args, **kwargs):
        self.stop_event = AlreadyStoppedEvent()
        self.is_interrupted = False


class FakeHexapodController(FakeContextManager):
    def __init__(self):
        self.config_calls = []
        self.start_calls = []

    def config_wave_generators(self, **kwargs):
        self.config_calls.append(kwargs)

    def start_wave_generators(self, **kwargs):
        self.start_calls.append(kwargs)


class DriveAndDaqTest(unittest.TestCase):
    @patch("phasemeter_core.drive_and_daq.HexapodController")
    @patch("phasemeter_core.drive_and_daq.DataWriter", FakeDataWriter)
    @patch("phasemeter_core.drive_and_daq.DataAcquisitor", FakeDataAcquisitor)
    def test_passes_all_dofs_to_one_synchronous_start(self, controller_class):
        controller = FakeHexapodController()
        controller_class.return_value = controller

        drive_and_daq(
            filename="unused",
            time=1,
            wave_generator_id=[1, 3, 5],
            wave_table_id=[4, 5, 6],
            num_periods=100,
        )

        self.assertEqual(
            controller.config_calls,
            [
                {
                    "wave_generator_ids": [1, 3, 5],
                    "wave_table_ids": [4, 5, 6],
                    "num_periods": 100,
                }
            ],
        )
        self.assertEqual(
            controller.start_calls,
            [{"wave_generator_ids": [1, 3, 5]}],
        )


if __name__ == "__main__":
    unittest.main()
