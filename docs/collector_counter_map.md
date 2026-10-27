# Collector counter map (Ampere / Hopper / Blackwell)

Canonical state samples are defined once in
[`gitm/telemetry/schema.py`](../gitm/telemetry/schema.py) (`Sample`).
Producer IDs (NVML API symbols and DCGM field IDs) live in
[`gitm/telemetry/counter_map.py`](../gitm/telemetry/counter_map.py) so the map
lands **in** the collector schema package (ENG-83), not beside it.

## Pass rule

Every top-level `Sample` field except `extra`, `diagnostics`, and `labels` must
have a mapping for **ampere**, **hopper**, and **blackwell**. A counter that
exists on only one generation must not be promoted to a top-level `Sample`
field until all three generations are mapped; keep it in `extra`.

Enforced by `tests/test_collector_counter_map.py`.

## Today

`NvidiaBackend` reads **NVML** only. DCGM columns document the agreed alternate
producer for the same canonical names (Pamela / ENG-83). Filling
`interconnect_bytes_per_s` from NVML is still a follow-up; the field is mapped
for all three generations so the schema stays legal.

## Agreeing changes

Do not add a generation-specific top-level `Sample` field without updating
`COUNTER_MAP` and getting schema sign-off (ENG-83). AMD / amd-smi is ENG-128
(second backend, same canonical names).
