#!/usr/bin/env python3
"""Android calculator UI layout automation demo using Maestro + OpenCV."""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import cv2
import numpy as np


@dataclass
class LayoutMetrics:
    button_count: int
    columns: int
    rows: int


def _cluster_positions(values: Sequence[float], tolerance: float) -> list[float]:
    if not values:
        return []
    sorted_values = sorted(values)
    clusters: list[list[float]] = [[sorted_values[0]]]
    for value in sorted_values[1:]:
        if abs(value - np.mean(clusters[-1])) <= tolerance:
            clusters[-1].append(value)
        else:
            clusters.append([value])
    return [float(np.mean(cluster)) for cluster in clusters]


def detect_calculator_layout(image_path: Path) -> LayoutMetrics:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = gray.shape
    min_area = (width * height) * 0.002

    centers: list[tuple[float, float]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < min_area:
            continue
        aspect_ratio = w / max(h, 1)
        if 0.45 <= aspect_ratio <= 2.2:
            centers.append((x + w / 2, y + h / 2))

    x_centers = [center[0] for center in centers]
    y_centers = [center[1] for center in centers]

    columns = len(_cluster_positions(x_centers, tolerance=width * 0.08))
    rows = len(_cluster_positions(y_centers, tolerance=height * 0.06))

    return LayoutMetrics(button_count=len(centers), columns=columns, rows=rows)


def assert_layout(metrics: LayoutMetrics, min_buttons: int = 16, min_columns: int = 4, min_rows: int = 4) -> None:
    if metrics.button_count < min_buttons:
        raise AssertionError(f"Expected at least {min_buttons} button-like regions, got {metrics.button_count}")
    if metrics.columns < min_columns:
        raise AssertionError(f"Expected at least {min_columns} columns, got {metrics.columns}")
    if metrics.rows < min_rows:
        raise AssertionError(f"Expected at least {min_rows} rows, got {metrics.rows}")


def run_maestro(flow_file: Path, app_id: str) -> None:
    command = [
        "maestro",
        "test",
        str(flow_file),
        "-e",
        f"CALCULATOR_APP_ID={app_id}",
    ]
    subprocess.run(command, check=True)


def capture_adb_screenshot(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["adb", "exec-out", "screencap", "-p"], check=True, stdout=subprocess.PIPE)
    output.write_bytes(result.stdout)


def generate_synthetic_calculator(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = np.full((1920, 1080, 3), 245, dtype=np.uint8)
    start_x, start_y = 130, 650
    btn_w, btn_h = 180, 180
    gap_x, gap_y = 50, 38
    for row in range(4):
        for col in range(4):
            x1 = start_x + col * (btn_w + gap_x)
            y1 = start_y + row * (btn_h + gap_y)
            x2, y2 = x1 + btn_w, y1 + btn_h
            cv2.rectangle(img, (x1, y1), (x2, y2), (80, 80, 80), 4)
    if not cv2.imwrite(str(path), img):
        raise ValueError(f"Unable to write synthetic image to: {path}")


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calculator UI layout demo using Maestro + OpenCV")
    parser.add_argument("--app-id", default="com.google.android.calculator", help="Calculator package name")
    parser.add_argument(
        "--flow-file",
        type=Path,
        default=Path("maestro/calculator_layout_demo.yaml"),
        help="Maestro flow that opens the calculator app",
    )
    parser.add_argument(
        "--screenshot",
        type=Path,
        default=Path("artifacts/calculator_screen.png"),
        help="Screenshot file for OpenCV layout verification",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Use a generated synthetic calculator screenshot instead of device interaction",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    if args.self_test:
        generate_synthetic_calculator(args.screenshot)
    else:
        run_maestro(args.flow_file, args.app_id)
        capture_adb_screenshot(args.screenshot)

    metrics = detect_calculator_layout(args.screenshot)
    assert_layout(metrics)

    print(
        "Layout check passed:",
        f"buttons={metrics.button_count}",
        f"columns={metrics.columns}",
        f"rows={metrics.rows}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
