import unittest

from phasemeter_core.hexapod_controller import HexapodController


class FakePIDevice:
    def __init__(self):
        self.calls = []

    def WSL(self, wave_generators, wave_tables):
        self.calls.append(("WSL", wave_generators, wave_tables))

    def WGC(self, wave_generators, num_periods):
        self.calls.append(("WGC", wave_generators, num_periods))

    def WGO(self, wave_generators, modes):
        self.calls.append(("WGO", wave_generators, modes))


class HexapodControllerTest(unittest.TestCase):
    def setUp(self):
        self.controller = HexapodController()
        self.controller.pidevice = FakePIDevice()

    def test_configures_multiple_generators_in_single_commands(self):
        self.controller.config_wave_generators([1, 3], [4, 5], [100, 200])

        self.assertEqual(
            self.controller.pidevice.calls,
            [
                ("WSL", [1, 3], [4, 5]),
                ("WGC", [1, 3], [100, 200]),
            ],
        )

    def test_broadcasts_period_count_to_all_generators(self):
        self.controller.config_wave_generators([1, 2, 3], [4, 5, 6], 10)

        self.assertEqual(
            self.controller.pidevice.calls[-1],
            ("WGC", [1, 2, 3], [10, 10, 10]),
        )

    def test_starts_multiple_generators_in_one_wgo_command(self):
        self.controller.start_wave_generators([1, 3, 5])

        self.assertEqual(
            self.controller.pidevice.calls,
            [("WGO", [1, 3, 5], [1, 1, 1])],
        )

    def test_existing_single_generator_api_remains_compatible(self):
        self.controller.config_wave_generator(1, 4, 100)
        self.controller.start_wave_generator(1)

        self.assertEqual(
            self.controller.pidevice.calls,
            [
                ("WSL", 1, 4),
                ("WGC", 1, 100),
                ("WGO", 1, 1),
            ],
        )

    def test_rejects_mismatched_generator_and_table_counts(self):
        with self.assertRaisesRegex(ValueError, "same length"):
            self.controller.config_wave_generators([1, 2], [4], 10)

        self.assertEqual(self.controller.pidevice.calls, [])

    def test_rejects_duplicate_generators(self):
        with self.assertRaisesRegex(ValueError, "duplicates"):
            self.controller.config_wave_generators([1, 1], [4, 5], 10)

        self.assertEqual(self.controller.pidevice.calls, [])


if __name__ == "__main__":
    unittest.main()
