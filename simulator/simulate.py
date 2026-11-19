#!/usr/bin/env python3
"""Discrete-time simulator for FCFS, fixed-priority, and EDF scheduling.

Time unit: milliseconds. Each simulation step executes one millisecond of CPU
demand. FCFS is non-preemptive; fixed-priority and EDF are preemptive.
This is a policy simulator, not an implementation of the native FreeRTOS
scheduler and not an ESP32 hardware benchmark.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Job:
    task_id: str
    job_number: int
    release: int
    execution: int
    deadline: int
    priority: int
    remaining: int
    first_start: int | None = None
    completion: int | None = None

    @property
    def absolute_deadline(self) -> int:
        return self.release + self.deadline


def load_tasks(path: Path) -> list[dict[str, int | str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("The task configuration is empty.")
    tasks = []
    seen = set()
    for row in rows:
        task_id = row["task_id"].strip()
        if not task_id or task_id in seen:
            raise ValueError(f"Missing or duplicate task_id: {task_id!r}")
        seen.add(task_id)
        task = {
            "task_id": task_id,
            "period_ms": int(row["period_ms"]),
            "execution_ms": int(row["execution_ms"]),
            "deadline_ms": int(row["deadline_ms"]),
            "priority": int(row["priority"]),
        }
        if min(task["period_ms"], task["execution_ms"], task["deadline_ms"]) <= 0:
            raise ValueError(f"Period, execution, and deadline must be positive: {task_id}")
        if task["execution_ms"] <= 0:
            raise ValueError(f"Execution time must be positive: {task_id}")
        tasks.append(task)
    return tasks


def simulate(tasks: list[dict[str, int | str]], policy: str, duration: int) -> list[Job]:
    jobs: list[Job] = []
    ready: list[Job] = []
    active: Job | None = None
    next_release = {str(t["task_id"]): 0 for t in tasks}
    job_counts = {str(t["task_id"]): 0 for t in tasks}

    for now in range(duration):
        # Release all jobs scheduled for this instant.
        for task in tasks:
            task_id = str(task["task_id"])
            if now == next_release[task_id]:
                job_counts[task_id] += 1
                job = Job(
                    task_id=task_id,
                    job_number=job_counts[task_id],
                    release=now,
                    execution=int(task["execution_ms"]),
                    deadline=int(task["deadline_ms"]),
                    priority=int(task["priority"]),
                    remaining=int(task["execution_ms"]),
                )
                jobs.append(job)
                ready.append(job)
                next_release[task_id] += int(task["period_ms"])

        # FCFS runs the current job to completion; other policies reselect
        # the highest-ranked ready job at every millisecond (preemptive).
        if policy == "fcfs":
            if active is None and ready:
                active = min(ready, key=lambda j: (j.release, j.job_number))
                ready.remove(active)
        else:
            candidates = ready + ([active] if active is not None else [])
            if candidates:
                if policy == "fixed_priority":
                    chosen = max(candidates, key=lambda j: (j.priority, -j.release, -j.job_number))
                elif policy == "edf":
                    chosen = min(candidates, key=lambda j: (j.absolute_deadline, j.release, j.task_id, j.job_number))
                else:
                    raise ValueError(f"Unknown policy: {policy}")
                if active is not chosen:
                    if active is not None:
                        ready.append(active)
                    ready.remove(chosen)
                    active = chosen

        if active is not None:
            if active.first_start is None:
                active.first_start = now
            active.remaining -= 1
            if active.remaining == 0:
                active.completion = now + 1
                active = None

    return jobs


def write_outputs(jobs: list[Job], policy: str, output: Path, duration: int,
                  tasks: list[dict[str, int | str]]) -> dict[str, int | float | str]:
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{policy}_jobs.csv"
    fields = [
        "policy", "task_id", "job_number", "release_ms", "first_start_ms",
        "completion_ms", "execution_ms", "absolute_deadline_ms",
        "response_time_ms", "waiting_time_ms", "deadline_miss", "status",
    ]
    completed = 0
    misses = 0
    responses = []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            done = job.completion is not None
            response = job.completion - job.release if done else ""
            waiting = response - job.execution if done else ""
            missed = bool(done and job.completion > job.absolute_deadline)
            completed += int(done)
            misses += int(missed)
            if done:
                responses.append(int(response))
            writer.writerow({
                "policy": policy,
                "task_id": job.task_id,
                "job_number": job.job_number,
                "release_ms": job.release,
                "first_start_ms": job.first_start if job.first_start is not None else "",
                "completion_ms": job.completion if done else "",
                "execution_ms": job.execution,
                "absolute_deadline_ms": job.absolute_deadline,
                "response_time_ms": response,
                "waiting_time_ms": waiting,
                "deadline_miss": int(missed),
                "status": "completed" if done else "unfinished_at_horizon",
            })

    total_jobs = len(jobs)
    utilization = sum(float(t["execution_ms"]) / float(t["period_ms"]) for t in tasks)
    summary = {
        "policy": policy,
        "simulation_duration_ms": duration,
        "jobs_released": total_jobs,
        "jobs_completed": completed,
        "unfinished_jobs": total_jobs - completed,
        "deadline_misses_completed_jobs": misses,
        "completion_rate_percent": round(100 * completed / total_jobs, 2) if total_jobs else 0.0,
        "deadline_miss_rate_of_completed_percent": round(100 * misses / completed, 2) if completed else 0.0,
        "mean_response_time_ms": round(sum(responses) / len(responses), 3) if responses else "",
        "max_response_time_ms": max(responses) if responses else "",
        "theoretical_utilization": round(utilization, 4),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/tasks.csv"))
    parser.add_argument("--policy", choices=["fcfs", "fixed_priority", "edf", "all"], default="all")
    parser.add_argument("--duration", type=int, default=5000, help="Simulation horizon in milliseconds")
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    if args.duration <= 0:
        parser.error("--duration must be positive")

    tasks = load_tasks(args.config)
    policies = ["fcfs", "fixed_priority", "edf"] if args.policy == "all" else [args.policy]
    summaries = []
    for policy in policies:
        jobs = simulate(tasks, policy, args.duration)
        summaries.append(write_outputs(jobs, policy, args.output, args.duration, tasks))
        print(f"{policy}: released={len(jobs)} completed={sum(j.completion is not None for j in jobs)}")

    summary_path = args.output / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].keys()))
        writer.writeheader()
        writer.writerows(summaries)
    print(f"Wrote results to: {args.output.resolve()}")


if __name__ == "__main__":
    main()
