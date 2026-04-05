"""Stable filenames inside the ephemeral workspace."""

ASM_SOURCE = "asm.s"
ASM_BINARY = "bench_asm"

REF_C = "ref.c"
REF_CPP = "ref.cpp"

OPT_LEVELS = ("O0", "O1", "O2", "O3")

RUN_SCRIPT = "hyperfine_bench_run.sh"
PHASE_CORRECTNESS_SCRIPT = "phase_correctness.sh"
PHASE_BENCHMARK_SCRIPT = "phase_benchmark.sh"
TESTS_DIR = "tests"
TIMING_INPUT = "timing.in"


def timing_json_for_label(label: str) -> str:
    """label is 'asm' or 'O0' ... 'O3'."""
    if label == "asm":
        return "timing_asm.json"
    return f"timing_{label}.json"
