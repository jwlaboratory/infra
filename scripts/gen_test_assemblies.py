#!/usr/bin/env python3
"""
Generate 20 test assembly files for the noise study.

Uses Docker (gcc:13, linux/arm64) to cross-compile existing C++ sources at
different optimization levels, producing assembly (.s) files via ``gcc -S``.
Also copies the 6 existing hand-written assembly files from examples/.

This gives Team 1 the 20 binaries needed to run the batch noise study and
demonstrate < 5% CV across a diverse set of programs.

Strategy for 20 files:
  Group A: abc_ref.cpp at -O0, -O1, -O2, -O3                          → 4 files
  Group B: example2.cpp at -O0, -O1, -O2, -O3                         → 4 files
  Group C: abc_ref.cpp at -O2 -march=armv8-a, -O3 -march=armv8-a      → 2 files
  Group D: example2.cpp at -O2 -march=armv8-a, -O3 -march=armv8-a     → 2 files
  Group E: abc_ref.cpp at -Os (size optimize)                          → 1 file
  Group F: example2.cpp at -Os                                         → 1 file
  Group G: Existing hand-written .s files from examples/               → 6 files
  TOTAL:                                                               = 20 files

Usage (from repo root):

  python3 scripts/gen_test_assemblies.py --output-dir generated_assemblies

  # Custom Docker image or platform:
  python3 scripts/gen_test_assemblies.py \\
    --output-dir /tmp/asm_test \\
    --docker-image gcc:13 \\
    --docker-platform linux/arm64

Prerequisites:
  - Docker daemon running (Team 1's first priority to resolve if not)
  - gcc:13 image available (script pulls it automatically)
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Configuration: which C++ sources to compile and at what optimization levels.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompileSpec:
    """One assembly file to generate from a C++ source."""
    source: Path          # Path to C++ source (relative to repo root)
    opt_flag: str         # e.g. "-O2"
    extra_cflags: tuple[str, ...] = ()  # e.g. ("-march=armv8-a",)
    output_name: str = ""  # If empty, auto-generated from source + flags

    def derive_output_name(self) -> str:
        """Generate a descriptive .s filename from the source and flags."""
        if self.output_name:
            return self.output_name
        stem = self.source.stem  # e.g. "abc_ref"
        # Turn "-O2" into "O2", "-Os" into "Os"
        opt_suffix = self.opt_flag.lstrip("-")
        # Turn extra flags like "-march=armv8-a" into "armv8a"
        extra = ""
        for flag in self.extra_cflags:
            # Strip leading dash, replace non-alphanum with nothing
            clean = flag.lstrip("-").replace("=", "").replace("-", "")
            extra += f"_{clean}"
        return f"{stem}_{opt_suffix}{extra}.s"


def _build_compile_specs(examples_dir: Path) -> list[CompileSpec]:
    """Build the list of 14 compile specs (Groups A–F from the strategy)."""
    abc = examples_dir / "abc_ref.cpp"
    ex2 = examples_dir / "example2.cpp"

    specs: list[CompileSpec] = []

    # Group A: abc_ref.cpp at O0, O1, O2, O3
    for opt in ["-O0", "-O1", "-O2", "-O3"]:
        specs.append(CompileSpec(source=abc, opt_flag=opt))

    # Group B: example2.cpp at O0, O1, O2, O3
    for opt in ["-O0", "-O1", "-O2", "-O3"]:
        specs.append(CompileSpec(source=ex2, opt_flag=opt))

    # Group C: abc_ref.cpp with -march=armv8-a at O2, O3
    for opt in ["-O2", "-O3"]:
        specs.append(
            CompileSpec(source=abc, opt_flag=opt, extra_cflags=("-march=armv8-a",))
        )

    # Group D: example2.cpp with -march=armv8-a at O2, O3
    for opt in ["-O2", "-O3"]:
        specs.append(
            CompileSpec(source=ex2, opt_flag=opt, extra_cflags=("-march=armv8-a",))
        )

    # Group E: abc_ref.cpp at -Os (size optimization)
    specs.append(CompileSpec(source=abc, opt_flag="-Os"))

    # Group F: example2.cpp at -Os
    specs.append(CompileSpec(source=ex2, opt_flag="-Os"))

    return specs


def _find_existing_asm(examples_dir: Path) -> list[Path]:
    """Find existing hand-written .s files in examples/ (Group G)."""
    return sorted(examples_dir.glob("*.s"))


# ---------------------------------------------------------------------------
# Docker-based cross-compilation: gcc -S inside the container.
# ---------------------------------------------------------------------------

def _docker_pull(image: str) -> bool:
    """Pull the Docker image (idempotent).  Returns True on success."""
    print(f"  Pulling Docker image: {image}...", end="", flush=True)
    result = subprocess.run(
        ["docker", "pull", image],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(" done")
        return True
    else:
        print(f" FAILED\n  {result.stderr[:300]}")
        return False


def compile_to_asm(
    source: Path,
    output: Path,
    *,
    opt_flag: str,
    extra_cflags: tuple[str, ...] = (),
    std_flag: str = "-std=c++20",
    docker_image: str,
    docker_platform: str,
    docker_timeout_s: float = 120.0,
) -> bool:
    """Compile a C++ source to assembly inside Docker using gcc -S.

    Mounts the source's parent directory at /src (read-only) and the output
    directory at /out (writable).  Runs:
      g++ -S -fverbose-asm {opt_flag} {extra_cflags} {std_flag} /src/{name} -o /out/{name}

    Returns True on success, False on failure.
    """
    src_dir = source.resolve().parent
    out_dir = output.resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build the gcc command that will run inside the container.
    gcc_cmd = [
        "g++",
        "-S",                  # Produce assembly instead of object code.
        "-fverbose-asm",       # Add comments showing C++ source lines.
        opt_flag,              # Optimization level (e.g. -O2, -Os).
        *extra_cflags,         # Extra flags (e.g. -march=armv8-a).
        std_flag,              # Language standard (e.g. -std=c++20).
        f"/src/{source.name}",
        "-o",
        f"/out/{output.name}",
    ]

    docker_cmd = [
        "docker", "run", "--rm",
        "--platform", docker_platform,
        "-v", f"{src_dir}:/src:ro",
        "-v", f"{out_dir}:/out",
        "-w", "/src",
        docker_image,
        *gcc_cmd,
    ]

    try:
        result = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=docker_timeout_s,
        )
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT compiling {source.name} with {opt_flag}")
        return False

    if result.returncode != 0:
        print(f"    FAILED compiling {source.name} with {opt_flag}")
        if result.stderr:
            # Show first few lines of error for debugging.
            for line in result.stderr.strip().splitlines()[:5]:
                print(f"      {line}")
        return False

    return output.is_file()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description=(
            "Generate 20 test assembly files for the batch noise study.  "
            "Compiles C++ sources at multiple optimization levels using Docker "
            "and copies existing hand-written assembly files."
        ),
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated_assemblies"),
        help="Directory to write generated .s files (default: generated_assemblies/).",
    )
    ap.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("examples"),
        help="Directory containing C++ sources and existing .s files (default: examples/).",
    )
    ap.add_argument(
        "--docker-image",
        default="gcc:13",
        help="Docker image with gcc/g++ (default: gcc:13).",
    )
    ap.add_argument(
        "--docker-platform",
        default="linux/arm64",
        help="Docker --platform for cross-compilation (default: linux/arm64).",
    )
    ap.add_argument(
        "--docker-timeout",
        type=float,
        default=120.0,
        help="Timeout per compilation in seconds (default: 120).",
    )
    args = ap.parse_args()

    examples_dir = args.examples_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Verify source files exist.
    for name in ["abc_ref.cpp", "example2.cpp"]:
        if not (examples_dir / name).is_file():
            print(f"error: {examples_dir / name} not found", file=sys.stderr)
            return 2

    # -----------------------------------------------------------------------
    # Check Docker availability — this is the #1 blocker for Team 1.
    # -----------------------------------------------------------------------
    docker_check = subprocess.run(
        ["docker", "info"], capture_output=True, text=True
    )
    if docker_check.returncode != 0:
        print(
            "error: Docker daemon is not reachable.\n"
            "  Team 1 action: ensure Docker Desktop is running, or use colima/podman.\n"
            f"  docker info stderr: {docker_check.stderr[:200]}",
            file=sys.stderr,
        )
        return 2

    # Pull the Docker image once before the batch.
    if not _docker_pull(args.docker_image):
        print("error: failed to pull Docker image", file=sys.stderr)
        return 2

    # -----------------------------------------------------------------------
    # Phase 1: Compile C++ sources at multiple optimization levels (Groups A–F).
    # -----------------------------------------------------------------------
    specs = _build_compile_specs(examples_dir)
    print(f"\n  Compiling {len(specs)} assembly variants...\n")

    compiled_count = 0
    failed_count = 0

    for spec in specs:
        out_name = spec.derive_output_name()
        out_path = output_dir / out_name
        print(f"  [{compiled_count + failed_count + 1}/{len(specs)}] "
              f"{spec.source.name} {spec.opt_flag} "
              f"{' '.join(spec.extra_cflags)} → {out_name}",
              end="  ", flush=True)

        ok = compile_to_asm(
            spec.source,
            out_path,
            opt_flag=spec.opt_flag,
            extra_cflags=spec.extra_cflags,
            docker_image=args.docker_image,
            docker_platform=args.docker_platform,
            docker_timeout_s=args.docker_timeout,
        )
        if ok:
            print("OK")
            compiled_count += 1
        else:
            failed_count += 1

    # -----------------------------------------------------------------------
    # Phase 2: Copy existing hand-written .s files (Group G).
    # -----------------------------------------------------------------------
    existing = _find_existing_asm(examples_dir)
    print(f"\n  Copying {len(existing)} existing assembly files...\n")

    copied_count = 0
    for asm in existing:
        dest = output_dir / asm.name
        shutil.copy2(asm, dest)
        print(f"  {asm.name} → {dest.name}")
        copied_count += 1

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    total = compiled_count + copied_count
    all_files = sorted(output_dir.glob("*.s"))

    print(f"\n{'='*60}")
    print(f"  GENERATION COMPLETE")
    print(f"  Compiled:  {compiled_count} (failed: {failed_count})")
    print(f"  Copied:    {copied_count}")
    print(f"  Total:     {total} assembly files in {output_dir}/")
    print(f"{'='*60}\n")

    if total < 20:
        print(
            f"  WARNING: Only {total} files generated (target: 20).\n"
            f"  Check compilation failures above.",
            file=sys.stderr,
        )

    # List all generated files.
    print("  Generated files:")
    for f in all_files:
        size = f.stat().st_size
        print(f"    {f.name:<40} {size:>8} bytes")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
