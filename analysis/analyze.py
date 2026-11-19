#!/usr/bin/env python3
"""Create comparison charts from simulator job CSVs or measured CSVs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/figures"))
    args = parser.parse_args()

    summary_path = args.input / "summary.csv"
    if not summary_path.exists():
        raise SystemExit(f"Missing {summary_path}. Run simulator/simulate.py first.")

    summary = pd.read_csv(summary_path)
    args.output.mkdir(parents=True, exist_ok=True)

    charts = [
        ("mean_response_time_ms", "Mean response time (ms)", "mean_response_time.png"),
        ("deadline_miss_rate_of_completed_percent", "Deadline miss rate (%)", "deadline_miss_rate.png"),
        ("completion_rate_percent", "Completion rate (%)", "completion_rate.png"),
    ]
    for column, ylabel, filename in charts:
        values = pd.to_numeric(summary[column], errors="coerce")
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(summary["policy"], values)
        ax.set_xlabel("Scheduling policy")
        ax.set_ylabel(ylabel)
        ax.set_title(ylabel + " by policy")
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        fig.savefig(args.output / filename, dpi=160)
        plt.close(fig)

    print(f"Charts saved to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
