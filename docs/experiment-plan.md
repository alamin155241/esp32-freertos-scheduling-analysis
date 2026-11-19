# Experimental Plan

## Objective

Compare application-level FCFS, fixed-priority, and EDF dispatch policies under identical periodic workloads, first in simulation and later on ESP32 hardware.

## Policy definitions

1. **FCFS:** jobs enter a FIFO ready queue and execute non-preemptively in arrival order.
2. **Fixed priority:** the ready job with the highest configured static task priority executes; a newly ready higher-priority job may preempt the current job.
3. **EDF:** the ready job with the earliest absolute deadline executes; a newly ready earlier-deadline job may preempt the current job.

Tie-breaking must be deterministic and documented. The simulator uses release time and job number for FCFS and stable secondary keys for the preemptive policies.

## Hardware platform record

Before collecting data, record:
- Exact ESP32 board/module and revision
- ESP-IDF version (or Arduino-ESP32 core version)
- Compiler/toolchain version and optimization level
- CPU frequency and power-management settings
- FreeRTOS tick rate and relevant configuration
- Serial logging configuration and timestamp source
- Ambient/environmental conditions if relevant

## Measurements

For every job, log:
- Policy, task ID, and job sequence number
- Release timestamp
- First-start timestamp
- Completion timestamp
- Relative and absolute deadline
- Execution demand or measured execution duration
- Completion status and deadline-miss flag

Use a monotonic high-resolution timer. Avoid heavy serial output inside timing-critical sections; buffer records and print them after a run where practical.

## Experimental controls

- Keep task periods, execution workload, deadlines, and hardware configuration identical across policies.
- Run a warm-up period, then collect multiple independent repetitions.
- Test several utilization levels, including feasible and overloaded workloads.
- Report mean, median, standard deviation, and maximum response time, plus deadline-miss and unfinished-job counts.
- Preserve raw CSV files; never replace raw data with aggregated values.
- Distinguish simulated results from measured hardware results in every table and figure.

## Limitations to discuss

- Discrete-time simulator granularity and scheduling overhead assumptions
- Dispatcher and instrumentation overhead on the microcontroller
- Interrupts, Wi-Fi/Bluetooth activity, and background system tasks
- The difference between application-level dispatch and FreeRTOS's native fixed-priority scheduler
- Any assumptions about preemption, blocking, shared resources, and task execution demand
