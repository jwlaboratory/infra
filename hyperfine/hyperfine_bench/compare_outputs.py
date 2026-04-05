"""Compare program stdout to expected judge output."""


def _normalize_newlines(text: str) -> str:
    # Normalize CRLF/CR to LF so Windows-vs-Unix endings don't fail comparisons.
    return text.replace("\r\n", "\n").replace("\r", "\n")


def outputs_match(actual: str, expected: str, *, strict: bool) -> bool:
    if strict:
        return actual == expected
    # Common judge behavior: tolerate newline style + trailing newline differences.
    return _normalize_newlines(actual).rstrip("\n") == _normalize_newlines(expected).rstrip("\n")
