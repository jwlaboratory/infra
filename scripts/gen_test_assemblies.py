#!/usr/bin/env python3
"""
Generate test assemblies for the batch noise study.

Compiles C++ source files at multiple optimization levels via Docker (gcc:13,
linux/arm64) to produce .s assembly files, then copies in existing hand-written
assemblies. Output goes to `generated_assemblies/` by default.

Usage (from repo root):
  python3 scripts/gen_test_assemblies.py \\
    --out-dir generated_assemblies \\
    --docker-platform linux/arm64

Sources compiled:
  - examples/abc_ref.cpp      → abc_ref_{O0,O1,O2,O2_marcharmv8a,O3,O3_marcharmv8a,Os}.s  (7)
  - examples/example2.cpp     → example2_{O0,O1,O2,O2_marcharmv8a,O3,O3_marcharmv8a,Os}.s (7)

Hand-written assemblies copied:
  - examples/abc_user_arm64.s          → abc_user_arm64.s
  - examples/example2_deepseek.s       → example2_deepseek.s
  - examples/example2_deepseek_speed.s → example2_deepseek_speed.s
  - examples/example2_gemma.s          → example2_gemma.s
  - examples/example2_gemma_speed.s    → example2_gemma_speed.s
  - examples/example2_sonnet4.6.s      → example2_sonnet4.6.s

Total: 20 assembly files.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple


REPO_ROOT = Path(__file__).parent.parent


class CompileVariant(NamedTuple):
    source: Path
    opt_flag: str
    extra_flags: list[str]
    out_stem: str  # stem for the output .s file


def _compile_to_asm_via_docker(
    source: Path,
    opt_flag: str,
    extra_flags: list[str],
    out_path: Path,
    docker_image: str,
    docker_platform: str,
    timeout_s: float = 120.0,
) -> bool:
    """
    Compile `source` to assembly using Docker, write to `out_path`.
    Returns True on success.
    """
    with tempfile.TemporaryDirectory(prefix="gen-asm-") as tmp_str:
        tmp = Path(tmp_str)
        src_in = tmp / source.name
        shutil.copy(source, src_in)

        out_name = "output.s"
        cmd_parts = [
            "g++",
            "-std=c++20",
            opt_flag,
            *extra_flags,
            "-S",           # compile to assembly only
            "-o", out_name,
            source.name,
        ]
        script_body = "#!/usr/bin/env bash\nset -e\ncd /work\n" + " ".join(cmd_parts) + "\n"
        script_path = tmp / "compile.sh"
        script_path.write_text(script_body, encoding="utf-8")
        script_path.chmod(0o755)

        proc = subprocess.run(
            [
                "docker", "run", "--rm",
                "--platform", docker_platform,
                "-v", f"{tmp.resolve()}:/work",
                "-w", "/work",
                docker_image,
                "bash", "/work/compile.sh",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        if proc.returncode != 0:
            print(f"    FAILED (exit {proc.returncode}): {proc.stderr[:500]}", file=sys.stderr)
            return False

        generated = tmp / out_name
        if not generated.is_file():
            print(f"    FAILED: output file not found", file=sys.stderr)
            return False

        shutil.copy(generated, out_path)
        return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate test assemblies for noise study.")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO_ROOT / "generated_assemblies",
        help="Output directory for .s files (default: generated_assemblies/).",
    )
    ap.add_argument(
        "--docker-image",
        default="gcc:13",
        help="Docker image (default: gcc:13).",
    )
    ap.add_argument(
        "--docker-platform",
        default="linux/arm64",
        help="Docker --platform (default: linux/arm64).",
    )
    ap.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker compilation; only copy hand-written assemblies.",
    )
    args = ap.parse_args()

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    sources = [
        (REPO_ROOT / "examples" / "abc_ref.cpp", "abc_ref"),
        (REPO_ROOT / "examples" / "example2.cpp", "example2"),
    ]

    opt_variants: list[tuple[str, str, list[str]]] = [
        ("O0", "-O0", []),
        ("O1", "-O1", []),
        ("O2", "-O2", []),
        ("O2_marcharmv8a", "-O2", ["-march=armv8-a"]),
        ("O3", "-O3", []),
        ("O3_marcharmv8a", "-O3", ["-march=armv8-a"]),
        ("Os", "-Os", []),
    ]

    compiled_ok = 0
    compiled_fail = 0

    if not args.skip_docker:
        print(f"Compiling assemblies via Docker ({args.docker_platform}, {args.docker_image})...", file=sys.stderr)
        for src_path, prefix in sources:
            if not src_path.is_file():
                print(f"  WARNING: source not found: {src_path}", file=sys.stderr)
                continue
            for opt_name, opt_flag, extra_flags in opt_variants:
                out_stem = f"{prefix}_{opt_name}"
                out_path = out_dir / f"{out_stem}.s"
                print(f"  {out_stem}.s ...", end=" ", flush=True, file=sys.stderr)
                ok = _compile_to_asm_via_docker(
                    src_path, opt_flag, extra_flags, out_path,
                    docker_image=args.docker_image,
                    docker_platform=args.docker_platform,
                )
                if ok:
                    compiled_ok += 1
                    print("OK", file=sys.stderr)
                else:
                    compiled_fail += 1
    else:
        print("Skipping Docker compilation (--skip-docker).", file=sys.stderr)

    # Copy hand-written assemblies
    hand_written = [
        "abc_user_arm64.s",
        "example2_deepseek.s",
        "example2_deepseek_speed.s",
        "example2_gemma.s",
        "example2_gemma_speed.s",
        "example2_sonnet4.6.s",
    ]

    copied_ok = 0
    copied_missing = 0
    print("\nCopying hand-written assemblies...", file=sys.stderr)
    examples_dir = REPO_ROOT / "examples"
    for name in hand_written:
        src = examples_dir / name
        dst = out_dir / name
        if src.is_file():
            shutil.copy(src, dst)
            copied_ok += 1
            print(f"  {name} ... OK", file=sys.stderr)
        else:
            copied_missing += 1
            print(f"  {name} ... MISSING ({src})", file=sys.stderr)

    total = compiled_ok + copied_ok
    print(f"\nDone. {total} assemblies in {out_dir}/", file=sys.stderr)
    print(f"  Compiled: {compiled_ok} OK, {compiled_fail} failed", file=sys.stderr)
    print(f"  Copied:   {copied_ok} OK, {copied_missing} missing\n", file=sys.stderr)

    return 0 if compiled_fail == 0 and copied_missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
