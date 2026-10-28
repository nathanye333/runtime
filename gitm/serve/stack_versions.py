"""Driver / CUDA / NCCL versions for the run record (re-baseline visibility).

Written next to ``preflight.json`` as ``stack_versions.json`` and copied into
``run_manifest.json``. Best-effort: missing tools become null, never raise.
"""

from __future__ import annotations

import re
import subprocess
from typing import Any


def _run(cmd: list[str], timeout: float = 15) -> str:
    try:
        return subprocess.check_output(
            cmd, text=True, stderr=subprocess.DEVNULL, timeout=timeout
        )
    except Exception:
        return ""


def collect_stack_versions() -> dict[str, Any]:
    """Snapshot host/container stack versions (vLLM collect-env equivalent subset)."""
    versions: dict[str, Any] = {
        "driver_version": None,
        "cuda_version": None,  # driver-reported CUDA (nvidia-smi banner)
        "torch_cuda_version": None,
        "nccl_version": None,
    }

    driver = _run(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"]
    ).strip().splitlines()
    if driver:
        versions["driver_version"] = driver[0].strip() or None

    smi = _run(["nvidia-smi"])
    m = re.search(r"CUDA Version:\s*([\d.]+)", smi)
    if m:
        versions["cuda_version"] = m.group(1)

    try:
        import torch

        raw = getattr(torch.version, "cuda", None)
        if raw:
            versions["torch_cuda_version"] = str(raw)
        nccl = torch.cuda.nccl.version()
        if isinstance(nccl, tuple):
            versions["nccl_version"] = ".".join(str(x) for x in nccl)
        elif nccl is not None:
            versions["nccl_version"] = str(nccl)
    except Exception:
        pass

    return versions
