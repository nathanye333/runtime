"""Stack version snapshot for run records."""

from __future__ import annotations

import json
from pathlib import Path

from gitm.serve.artifacts import write_preflight
from gitm.serve.stack_versions import collect_stack_versions


def test_collect_stack_versions_shape(monkeypatch):
    import sys
    import types

    monkeypatch.setattr(
        "gitm.serve.stack_versions._run",
        lambda cmd, timeout=15: (
            "570.86.15\n"
            if cmd[:2] == ["nvidia-smi", "--query-gpu=driver_version"]
            else "CUDA Version: 12.8\n"
        ),
    )
    torch = types.ModuleType("torch")
    torch.version = types.SimpleNamespace(cuda="12.8")
    torch.cuda = types.SimpleNamespace(
        nccl=types.SimpleNamespace(version=lambda: (2, 21, 5))
    )
    monkeypatch.setitem(sys.modules, "torch", torch)
    versions = collect_stack_versions()
    assert versions["driver_version"] == "570.86.15"
    assert versions["cuda_version"] == "12.8"
    assert versions["torch_cuda_version"] == "12.8"
    assert versions["nccl_version"] == "2.21.5"


def test_write_preflight_records_stack_versions(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "gitm.serve.stack_versions.collect_stack_versions",
        lambda: {
            "driver_version": "570.86.15",
            "cuda_version": "12.8",
            "torch_cuda_version": "12.8",
            "nccl_version": "2.21.5",
        },
    )
    from dataclasses import dataclass

    @dataclass
    class Check:
        name: str
        status: str
        detail: str

    versions = write_preflight(tmp_path, [Check("gpus", "pass", "ok")])
    assert versions["nccl_version"] == "2.21.5"
    written = json.loads((tmp_path / "stack_versions.json").read_text())
    assert written == versions
    assert (tmp_path / "preflight.json").is_file()
