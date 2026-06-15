"""GRAVEYARD spoliation and evidence-protection checks."""

from __future__ import annotations

import os
import re
from pathlib import Path

# Paths that must never receive writes during triage (pattern substrings)
EVIDENCE_PATH_PATTERNS = (
    "/cases/",
    "/mnt/",
    "evidence/",
    ".raw",
    ".vmem",
    ".dmp",
)

# Allowed write roots for GRAVEYARD tooling
ALLOWED_WRITE_ROOTS = (
    "exports",
    "analysis",
    "reports",
    "docs",
)


def is_evidence_path(path: str | Path) -> bool:
    """Return True if path matches evidence protection patterns."""
    normalized = str(path).replace("\\", "/").lower()
    return any(pat.lower() in normalized for pat in EVIDENCE_PATH_PATTERNS)


def is_allowed_write_path(path: str | Path) -> bool:
    """Return True if path is under an allowed GRAVEYARD write root."""
    parts = Path(path).parts
    if not parts:
        return False
    for i, part in enumerate(parts):
        if part in ALLOWED_WRITE_ROOTS:
            return True
    return False


def check_path_write_policy(path: str | Path) -> tuple[bool, str]:
    """
    Validate a proposed write path.
    Returns (allowed, reason).
    """
    p = Path(path)
    if is_evidence_path(p):
        return False, f"EVIDENCE_PATH_BLOCKED: {p}"
    if is_allowed_write_path(p):
        return True, "ALLOWED_WRITE_ROOT"
    return False, f"WRITE_OUTSIDE_ALLOWED_ROOTS: {p}"


def evidence_path_patterns_in_script(script_text: str) -> bool:
    """Check that a triage script documents evidence path protection."""
    return "EVIDENCE" in script_text or "evidence" in script_text.lower()


def export_dir_writable(exports_dir: Path) -> bool:
    """Check if exports directory is writable (expected during triage)."""
    return os.access(exports_dir, os.W_OK)


def export_dir_exists_readonly(exports_dir: Path) -> bool:
    """Check exports exists and is NOT writable (post-capture freeze mode)."""
    return exports_dir.is_dir() and not os.access(exports_dir, os.W_OK)


def parse_reject_codes(errors: list[str]) -> set[str]:
    codes: set[str] = set()
    for err in errors:
        for code in (
            "ATTRIBUTION_GUARD",
            "CITATION_MISMATCH",
            "CITATION_MISSING",
            "PHANTOM_ARTIFACT",
            "CONFIDENCE_GUARD",
            "EXPORT_PATH_TRAVERSAL",
        ):
            if code in err:
                codes.add(code)
    return codes


def is_export_path_traversal(path: str | Path) -> bool:
    """
    Reject path traversal or absolute paths outside exports context.
    Used before reading cited export files.
    """
    raw = str(path).replace("\\", "/")
    if ".." in raw:
        return True
    if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
        # Absolute paths only allowed if they stay under an exports root segment
        parts = Path(raw).parts
        if "exports" not in parts and "sample_exports" not in parts:
            return True
    return False


def validate_export_read(path: str | Path, exports_dir: Path | None = None) -> tuple[bool, str]:
    """Validate a proposed export read path."""
    if is_export_path_traversal(path):
        return False, f"EXPORT_PATH_TRAVERSAL: {path}"
    if exports_dir is not None:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = exports_dir / candidate
        try:
            resolved = candidate.resolve()
            base = exports_dir.resolve()
            if base not in resolved.parents and resolved != base:
                return False, f"EXPORT_PATH_TRAVERSAL: {path} outside {exports_dir}"
        except OSError:
            return False, f"EXPORT_PATH_INVALID: {path}"
    return True, "ALLOWED_EXPORT_READ"


def spoliation_check(path: str | Path, operation: str = "write") -> dict[str, object]:
    """
    Unified spoliation policy check for MCP tool and tests.
    operation: 'write' | 'read'
    """
    if operation == "write":
        allowed, reason = check_path_write_policy(path)
    else:
        allowed, reason = validate_export_read(path)
    return {
        "path": str(path),
        "operation": operation,
        "allowed": allowed,
        "reason": reason,
        "is_evidence_path": is_evidence_path(path),
    }
