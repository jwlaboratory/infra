"""Run the generated bash script locally or inside Docker (single invocation)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_local_script(
    work_dir: Path,
    script_name: str,
    *,
    timeout_s: float | None,
) -> subprocess.CompletedProcess[str]:
    script = work_dir / script_name
    return subprocess.run(
        ["bash", str(script)],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def run_docker_script(
    work_dir: Path,
    script_name: str,
    *,
    image: str,
    platform: str,
    timeout_s: float | None,
) -> subprocess.CompletedProcess[str]:
    """Mount work_dir at /work and execute the script once."""
    inner = f"/work/{script_name}"
    return subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--platform",
            platform,
            "-v",
            f"{work_dir.resolve()}:/work",
            "-w",
            "/work",
            image,
            "bash",
            inner,
        ],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def docker_daemon_reachable() -> tuple[bool, str]:
    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return True, ""
    detail = (result.stderr or result.stdout or "").strip() or "docker info failed"
    return False, detail
