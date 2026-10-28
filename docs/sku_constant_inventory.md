# H200 constant inventory (ceiling / collector / levers)

Snapshot of every H200-specific number in the ceiling model, the telemetry
collector, and the lever ranges. Companion empty schema:
[`gitm/planner/catalogue.yaml`](../gitm/planner/catalogue.yaml).

Field provenance for that schema: ticket Spec table (FP16/FP8/FP4, HBM, link,
SM, L2, `source`) plus what [`HardwareSpec`](../gitm/planner/roofline.py) /
[`context.py`](../gitm/planner/context.py) actually consume today (adds fp32 and
`arch`; SM/L2 are stubs unused by roofline).

Roadmap after this file (not implemented here): fill the catalogue from
datasheets, calibrate measured peaks, derive lever ranges from the table + GPU
count, and add a DCGM/NVML counter map per generation.

---

## Units (two layers — do not mix)

| Layer | Unit | Examples |
|---|---|---|
| Ceiling / roofline | rates **per second**; wall times in **seconds** | `peak_flops_*_per_s`, `*_bytes_per_s`, `t_pred_s` |
| Traces / qualify / signal contracts | timestamps and durations in **nanoseconds** | `start_ns`, `duration_ns`, `expected_sample_period_ns` |

Comparing a measured kernel to `t_pred_s` is `ns / 1e9` → s. That conversion
does not belong in the SKU datasheet table.

---

## Ceiling model — source of truth

All H200 peak / capacity / link numbers live in
[`gitm/planner/context.py`](../gitm/planner/context.py). Consumed via
`hardware_spec_for` → `HardwareSpec` and HFU/MBU denominators.

| File | Line | Symbol | Value | Meaning |
|---|---:|---|---|---|
| `gitm/planner/context.py` | 47 | `_PEAKS["H200"]` | `989e12`, `4800e9` | Dense fp16/bf16 FLOP/s; HBM bandwidth B/s |
| `gitm/planner/context.py` | 96 | `_QUANT_PEAKS["H200"]` | fp8 `1979e12`, fp32 `67e12` | Tensor / vector peaks (no fp4 key on Hopper) |
| `gitm/planner/context.py` | 114 | `_INTERCONNECT["H200"]` | `900e9` | NVLink 4 bidirectional B/s per GPU |
| `gitm/planner/context.py` | 131 | `_ARCH["H200"]` | `"hopper"` | Execution-path tag (not a gain number) |
| `gitm/planner/context.py` | 149 | `_MEMORY["H200"]` | `141e9` | HBM capacity bytes per GPU (SXM) |

Wiring: `hardware_spec_for` at `context.py` ~389–420.

No SM count or L2 capacity appears in the planner today.

---

## Collector — no H200-specific numbers

[`gitm/telemetry/collector.py`](../gitm/telemetry/collector.py) and
[`gitm/telemetry/backends/nvidia.py`](../gitm/telemetry/backends/nvidia.py) are
SKU-agnostic NVML. There is no DCGM field-ID table and no H200 branch.

| File | Line | Symbol | Value | Note |
|---|---:|---|---|---|
| `gitm/telemetry/collector.py` | 20 | `CollectorConfig.interval_s` | `1.0` | Global 1 Hz default, not H200-specific |

---

## Lever ranges — no H200 numeric bounds

[`gitm/kernels/library.yaml`](../gitm/kernels/library.yaml) uses shared relative
grids (e.g. `_relative_sweep: [0.5, 2.0, 4.0]`). Max batch / KV / TP / PP are not
derived from SKU peaks.

| File | Line | Entry | Value | Note |
|---|---:|---|---|---|
| `gitm/kernels/library.yaml` | 495 | `enable_expert_parallel` → `requires_hardware` | `[A100, H100, H200]` | Only H200-tagged lever gate (string list, not a numeric range) |

---

## Restatements (not second sources)

Same H200 figures hardcoded in tests/docs that mirror `context.py`:

| File | Lines | What |
|---|---|---|
| `tests/test_moe_graph.py` | 756–761 | `HardwareSpec` with 989e12 / 4.8e12 / 900e9 |
| `tests/test_catalogue_gqa_moe_new.py` | 41–46 | same |
| `tests/test_quant_arithmetic.py` | 233–236 | ridges vs 989e12, 1979e12, 67e12, 4.8e12, 900e9 |
| `tests/test_catalogue_glm_new.py` | 124 | `per_gpu_h200 = 141e9` |
| `tests/test_glm_graph.py` | 747 | `per_gpu_h200 = 141e9` |
| `tests/test_hypotheses.py` | 102, 125 | HBM `4.8e12` in `_ATTN_H200`; launch `2e-6` in `_EXTRA_H200` |
| `docs/glm-5.2/DESIGN-NOTE.md` | ~29–36 | H200 hardware assumption table |
| `docs/deepseek-v4.1-flash/DESIGN-NOTE.md` | ~47–56 | same family of peaks |
| `docs/quant-arithmetic.md` | ~67–71 | H200 ridge table |

---

## Adjacent (out of this inventory)

[`deploy/h200/gitm-node-health`](../deploy/h200/gitm-node-health) and
[`docs/h200_node_health.md`](h200_node_health.md) hold Slurm pre/post health
thresholds (thermal °C, `/dev/shm` size, etc.). Those are deploy gates, not
ceiling peaks, collector counters, or lever ranges.
