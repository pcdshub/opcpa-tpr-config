"""Plotting utilities for XPM sequence visualization."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from PyQt5 import QtWidgets

from opcpa_tpr_config.tests.test_sequences import simulate_laser_case


class SequencePlotter:
    """Collects multiple sequence traces and plots them overlaid.

    Overlapping y values are offset slightly so all traces remain visible.
    """

    def __init__(self, is_sc: bool, y_offset: float = 0.25):
        self._traces: list[tuple[np.ndarray, np.ndarray, str, str]] = []
        self._y_offset = y_offset
        self._is_sc = is_sc

    def add(self, data: tuple, label: str, color: str = "blue"):
        """Add a sequence trace to be plotted."""
        xdata = np.array(data[0], dtype=float) + 1
        ydata = np.array(data[1], dtype=float)
        self._traces.append((xdata, ydata, label, color))

    def show(self, title: str = "Sequence Comparison"):
        """Display all collected traces on a single plot."""
        if not self._traces:
            return

        fig, ax = plt.subplots(figsize=(14, 6))

        # Apply incremental y-offset per trace so overlapping points separate
        for idx, (xdata, ydata, label, color) in enumerate(self._traces):
            offset = idx * self._y_offset
            ax.bar(
                xdata, height=0.1, bottom=ydata-offset + 0.2,
                width=0.4, label=label, color=color, alpha=0.7,
            )

        # Clock gridlines: 120Hz (period=3 in AC frames) or 35kHz (period=26 in 910k frames)
        all_x = np.concatenate([t[0] for t in self._traces])
        x_min, x_max = all_x.min(), all_x.max()
        if self._is_sc:
            clock_period = 26  # 910000 / 35000 frames per 35kHz tick
        else:
            clock_period = 3  # 360/120 = 3 AC frames per 120Hz tick
        ticks = np.arange(
            clock_period * np.ceil(x_min / clock_period),
            x_max + 1,
            clock_period,
        )
        for t in ticks:
            ax.axvline(t, color="gray", alpha=0.15, linewidth=0.5)

        ax.set_xlabel("Frame")
        ax.set_ylabel("Event Code")
        ax.set_title(title)
        ax.legend(fontsize="small", loc="upper right")
        plt.tight_layout()
        plt.show()


def plot_case(
    plotter: SequencePlotter,
    label: str,
    color: str,
    is_sc: bool,
    rate: int,
    goose_rate: int | None,
    goose_len: int = 1,
    goose_start: int = 1,
    start_ts1: bool = True,
):
    """Simulate a case and add it to the plotter."""
    data, _ = simulate_laser_case(
        is_sc=is_sc,
        rate=rate,
        goose_rate=goose_rate,
        goose_len=goose_len,
        goose_start=goose_start,
        start_ts1=start_ts1,
    )
    plotter.add(data, label=label, color=color)


if __name__ == "__main__":
    # Collect cases into one plot
    plotter = SequencePlotter(is_sc=False, y_offset=0.15)
    plot_case(plotter, "120Hz no goose", "blue",
             is_sc=False, rate=120, goose_rate=None)
    plot_case(plotter, "120Hz goose 24Hz, start 2", "red",
             is_sc=False, rate=120, goose_rate=24, goose_start=2)
    plot_case(plotter, "60Hz goose 10Hz", "black",
             is_sc=False, rate=60, goose_rate=10, goose_start=1)
    plot_case(plotter, "120Hz goose 24Hz len=3", "green",
             is_sc=False, rate=120, goose_rate=24, goose_len=3)
    plotter.show(title="NC 120Hz Sequence Comparison")
