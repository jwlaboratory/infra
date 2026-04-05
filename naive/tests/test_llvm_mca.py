"""llvm-mca Docker helper tests (no Docker required for path checks)."""

from __future__ import annotations

import unittest
from pathlib import Path

from naive_bench.llvm_mca import run_llvm_mca_via_docker


class TestLlvmMca(unittest.TestCase):
    def test_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_llvm_mca_via_docker(Path("/nonexistent/asm.s"))


if __name__ == "__main__":
    unittest.main()
