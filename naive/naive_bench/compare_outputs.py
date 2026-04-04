"""Compare program stdout to expected judge output."""


def outputs_match(actual: str, expected: str, *, strict: bool) -> bool:
    if strict:
        return actual == expected
    # Common judge behavior: ignore trailing newlines on both sides.
    return actual.rstrip("\n") == expected.rstrip("\n")
