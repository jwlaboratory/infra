"""Optional static throughput hint via `llvm-mca` inside Docker (spike / correlation)."""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LlvmMcaDockerConfig:
    """
    Image must be Debian/Ubuntu-based so ``apt-get install llvm`` works.
    First run installs LLVM inside the container (slow); bake a derived image for CI.
    """

    image: str = "ubuntu:22.04"
    platform: str = "linux/arm64"
    mcpu: str = "generic"
    timeout_s: float = 600.0


def run_llvm_mca_via_docker(
    assembly_path: Path,
    cfg: LlvmMcaDockerConfig | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run ``llvm-mca`` on an assembly file using a one-shot Docker container.

    Mounts the file's parent at ``/work`` read-only and points llvm-mca at ``/work/<name>``.
    """
    cfg = cfg or LlvmMcaDockerConfig()
    path = assembly_path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    parent = path.parent
    name = path.name
    inner_cmd = (
        "apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq llvm "
        f"&& llvm-mca -mcpu={shlex.quote(cfg.mcpu)} /work/{shlex.quote(name)}"
    )
    return subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            cfg.platform,
            "-v",
            f"{parent}:/work:ro",
            "-w",
            "/work",
            cfg.image,
            "bash",
            "-lc",
            inner_cmd,
        ],
        capture_output=True,
        text=True,
        timeout=cfg.timeout_s,
        check=False,
    )


def run_llvm_mca_via_docker_simple(assembly_path: Path) -> str:
    """Return human-readable output; includes stderr when non-zero exit."""
    proc = run_llvm_mca_via_docker(assembly_path)
    parts = [proc.stdout or "", proc.stderr or ""]
    text = "\n".join(p for p in parts if p.strip())
    if proc.returncode != 0:
        return f"llvm-mca exit {proc.returncode}\n{text}"
    return text.strip()
