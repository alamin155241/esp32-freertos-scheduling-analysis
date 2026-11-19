# ESP32 FreeRTOS Scheduling Analysis

An experimental study of scheduling policies for periodic workloads on an ESP32-class IoT node.

> **Status:** Initial research scaffold. The Python simulator is the first reproducible component. ESP32/FreeRTOS hardware measurements have not yet been collected; no hardware performance claims or measured results are reported here.

## Research question

How do FCFS, fixed-priority, and earliest-deadline-first (EDF) policies affect response time, deadline misses, and CPU utilization for the same periodic workload?

## Important implementation distinction

FreeRTOS provides a preemptive, fixed-priority task scheduler. It does **not** provide native EDF scheduling. This project compares policies at the application level:

- **FCFS:** non-preemptive, first-ready-first-served dispatch.
- **Fixed priority:** preemptive dispatch using each task's configured static priority.
- **EDF:** preemptive dispatch using the absolute deadline of each released job.

The Python simulator models these policies independently. A later ESP32 experiment must implement the application-level dispatch policy explicitly and document its interaction with FreeRTOS.

## Repository structure

```text
.
├── README.md
├── requirements.txt
├── config/
│   └── tasks.csv
├── simulator/
│   └── simulate.py
├── analysis/
│   └── analyze.py
├── results/
│   └── .gitkeep
└── docs/
    └── experiment-plan.md
```

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python simulator/simulate.py --config config/tasks.csv --policy all --duration 5000 --output results
python analysis/analyze.py --input results --output results/figures
```

The simulator writes one job-level CSV per policy and a summary CSV. The analysis script creates comparison charts from those generated CSV files.

## Workload format

`config/tasks.csv` defines periodic tasks with:
- `task_id`: unique task label
- `period_ms`: release interval
- `execution_ms`: simulated CPU execution demand per job
- `deadline_ms`: relative deadline from release
- `priority`: static priority; larger number means higher priority

The included values are example workload parameters for testing the simulator, not measurements from an ESP32.

## Metrics

- Response time = completion time − release time
- Waiting time = response time − execution demand
- Absolute deadline = release time + relative deadline
- Deadline miss = completion time later than absolute deadline
- Simulated utilization = sum(C_i / T_i)

## Next experimental stages

1. Validate the simulator against hand-worked small schedules.
2. Port the workload generator and policy dispatcher to an ESP32 using ESP-IDF/FreeRTOS.
3. Record actual release/start/finish timestamps using a monotonic hardware timer.
4. Repeat each workload and report mean, median, maximum, and variation.
5. Compare simulation and hardware results, documenting overhead and limitations.

Do not describe simulator output as hardware results. Record board model, ESP-IDF/Arduino core version, clock settings, compiler options, and measurement method before publishing hardware findings.

## Research integrity

The repository currently contains no measured ESP32 results. Add raw measurement files and experiment conditions before making empirical claims.
