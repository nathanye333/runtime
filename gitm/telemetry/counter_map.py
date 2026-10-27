"""DCGM / NVML → canonical Sample field map (Ampere, Hopper, Blackwell).

Lives inside the collector schema package (ENG-83) so generation-specific
producer IDs do not fork a second schema beside :class:`gitm.telemetry.schema.Sample`.

Rule: every top-level canonical ``Sample`` field (except ``extra``,
``diagnostics``, and ``labels``) must have an entry for **ampere**, **hopper**,
and **blackwell**. A metric that exists on only one generation must not become a
top-level ``Sample`` field until all three generations have a mapping; put it in
``extra`` with an explicit map entry instead.

Producer keys:
  - ``nvml``: pynvml / nvml.h symbol (or short call description)
  - ``dcgm``: DCGM field ID symbol from dcgm_fields.h (same FID across gens
    unless noted)
  - ``host``: process/host derived (not a GPU counter)

``NvidiaBackend`` today reads NVML only; DCGM columns document the agreed
alternate producer for the same canonical names.
"""

from __future__ import annotations

from typing import Final, TypedDict

# Generations covered by this map. Ada (L40S) and others reuse the Ampere
# NVML/DCGM surface for the canonical fields below.
GENERATIONS: Final[tuple[str, ...]] = ("ampere", "hopper", "blackwell")

# Sample fields that are schema bookkeeping, not counters.
_EXCLUDED_SAMPLE_FIELDS: Final[frozenset[str]] = frozenset(
    {"extra", "diagnostics", "labels"}
)


class GenerationProducer(TypedDict):
    nvml: str
    dcgm: str | None
    host: str | None


CounterMap = dict[str, dict[str, GenerationProducer]]


def _same(nvml: str, dcgm: str | None = None, host: str | None = None) -> dict[str, GenerationProducer]:
    """Identical producer for ampere / hopper / blackwell."""
    entry: GenerationProducer = {"nvml": nvml, "dcgm": dcgm, "host": host}
    return {gen: entry for gen in GENERATIONS}


# Canonical Sample field → per-generation producers.
# Keep in sync with gitm.telemetry.schema.Sample; tests enforce coverage.
COUNTER_MAP: CounterMap = {
    "ts_ns": _same(
        nvml="n/a — sample wall clock",
        dcgm=None,
        host="time.time_ns()",
    ),
    "node": _same(
        nvml="n/a — hostname",
        dcgm=None,
        host="socket.gethostname()",
    ),
    "gpu_uuid": _same(
        nvml="nvmlDeviceGetUUID",
        dcgm="DCGM_FI_DEV_UUID",
    ),
    "gpu_index": _same(
        nvml="nvmlDeviceGetHandleByIndex / enumerator index",
        dcgm="DCGM_FI_DEV_GPU_ID",
        host="sampler gpu_index argument",
    ),
    "vendor": _same(
        nvml="n/a — constant \"nvidia\"",
        dcgm=None,
        host="Backend.vendor",
    ),
    "driver_version": _same(
        nvml="nvmlSystemGetDriverVersion",
        dcgm="DCGM_FI_DRIVER_VERSION",
    ),
    "util_pct": _same(
        nvml="nvmlDeviceGetUtilizationRates.gpu",
        dcgm="DCGM_FI_DEV_GPU_UTIL",
    ),
    "mem_used_bytes": _same(
        nvml="nvmlDeviceGetMemoryInfo.used",
        dcgm="DCGM_FI_DEV_FB_USED",  # MiB in DCGM; convert × 1024**2 at ingest
    ),
    "mem_total_bytes": _same(
        nvml="nvmlDeviceGetMemoryInfo.total",
        dcgm="DCGM_FI_DEV_FB_TOTAL",  # MiB in DCGM; convert × 1024**2 at ingest
    ),
    "power_w": _same(
        nvml="nvmlDeviceGetPowerUsage (mW → W / 1000)",
        dcgm="DCGM_FI_DEV_POWER_USAGE",
    ),
    "temp_c": _same(
        nvml="nvmlDeviceGetTemperature(NVML_TEMPERATURE_GPU)",
        dcgm="DCGM_FI_DEV_GPU_TEMP",
    ),
    "sm_clock_mhz": _same(
        nvml="nvmlDeviceGetClockInfo(NVML_CLOCK_SM)",
        dcgm="DCGM_FI_DEV_SM_CLOCK",
    ),
    "mem_clock_mhz": _same(
        nvml="nvmlDeviceGetClockInfo(NVML_CLOCK_MEM)",
        dcgm="DCGM_FI_DEV_MEM_CLOCK",
    ),
    "throttle_reasons": _same(
        nvml="nvmlDeviceGetCurrentClocksThrottleReasons → _NVML_THROTTLE_MAP",
        dcgm="DCGM_FI_DEV_CLOCK_THROTTLE_REASONS",
    ),
    "per_process": _same(
        nvml="nvmlDeviceGetComputeRunningProcesses",
        dcgm="DCGM_FI_PROCESS_NAME + accounting (process util via DCGM prof optional)",
    ),
    "interconnect_bytes_per_s": _same(
        nvml="nvmlDeviceGetNvLinkState / nvmlDeviceGetNvLinkThroughputCounter (per link)",
        dcgm="DCGM_FI_DEV_NVLINK_BANDWIDTH_TOTAL",
    ),
    "ecc_volatile_sbe": _same(
        nvml="nvmlDeviceGetTotalEccErrors(CORRECTED, VOLATILE)",
        dcgm="DCGM_FI_DEV_ECC_SBE_VOL_TOTAL",
    ),
    "ecc_volatile_dbe": _same(
        nvml="nvmlDeviceGetTotalEccErrors(UNCORRECTED, VOLATILE)",
        dcgm="DCGM_FI_DEV_ECC_DBE_VOL_TOTAL",
    ),
}


def required_sample_fields() -> frozenset[str]:
    """Canonical Sample field names that must appear in COUNTER_MAP."""
    from gitm.telemetry.schema import Sample

    return frozenset(Sample.model_fields) - _EXCLUDED_SAMPLE_FIELDS


def unmapped_sample_fields() -> frozenset[str]:
    """Sample fields missing from COUNTER_MAP (should be empty)."""
    return required_sample_fields() - frozenset(COUNTER_MAP)


def generations_missing(field: str) -> frozenset[str]:
    """Which of ampere/hopper/blackwell lack a mapping for ``field``."""
    row = COUNTER_MAP.get(field, {})
    return frozenset(GENERATIONS) - frozenset(row)
