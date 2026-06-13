import tempfile
import unittest
from pathlib import Path

from calculator_layout_demo import (
    LayoutMetrics,
    assert_layout,
    detect_calculator_layout,
    generate_synthetic_calculator,
)


class CalculatorLayoutDemoTests(unittest.TestCase):
    def test_detects_grid_from_synthetic_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "screen.png"
            generate_synthetic_calculator(image_path)
            metrics = detect_calculator_layout(image_path)

            self.assertGreaterEqual(metrics.button_count, 16)
            self.assertGreaterEqual(metrics.columns, 4)
            self.assertGreaterEqual(metrics.rows, 4)

    def test_assert_layout_raises_on_insufficient_metrics(self):
        with self.assertRaises(AssertionError):
            assert_layout(LayoutMetrics(button_count=4, columns=2, rows=2))


if __name__ == "__main__":
    unittest.main()
