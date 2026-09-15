import unittest
from unittest.mock import patch

from phasemeter_core.start_wave_generator import start_wave_generator


class FakeHexapodController:
    def __init__(self, fail_during_config=False):
        self.fail_during_config = fail_during_config
        self.calls = []

    def connect(self):
        self.calls.append(("connect",))

    def config_wave_generators(self, **kwargs):
        self.calls.append(("config_wave_generators", kwargs))
        if self.fail_during_config:
            raise RuntimeError("configuration failed")

    def start_wave_generators(self, **kwargs):
        self.calls.append(("start_wave_generators", kwargs))

    def disconnect(self):
        self.calls.append(("disconnect",))


class StartWaveGeneratorTest(unittest.TestCase):
    @patch("phasemeter_core.start_wave_generator.HexapodController")
    def test_connects_configures_and_starts_all_generators(self, controller_class):
        controller = FakeHexapodController()
        controller_class.return_value = controller

        result = start_wave_generator(
            wave_generator_ids=[1, 3],
            wave_table_ids=[4, 5],
            num_periods=100,
        )

        self.assertIs(result, controller)
        self.assertEqual(
            controller.calls,
            [
                ("connect",),
                (
                    "config_wave_generators",
                    {
                        "wave_generator_ids": [1, 3],
                        "wave_table_ids": [4, 5],
                        "num_periods": 100,
                    },
                ),
                ("start_wave_generators", {"wave_generator_ids": [1, 3]}),
            ],
        )

    @patch("phasemeter_core.start_wave_generator.HexapodController")
    def test_disconnects_if_configuration_fails(self, controller_class):
        controller = FakeHexapodController(fail_during_config=True)
        controller_class.return_value = controller

        with self.assertRaisesRegex(RuntimeError, "configuration failed"):
            start_wave_generator([1, 3], [4, 5], 100)

        self.assertEqual(controller.calls[-1], ("disconnect",))


if __name__ == "__main__":
    unittest.main()
