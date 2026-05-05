"""Lint .env files and vault secrets for common issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class LintIssue:
    key: str
    severity: str  # 'error' | 'warning' | 'info'
    message: str


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def summary(self) -> str:
        e, w = len(self.errors), len(self.warnings)
        return f"{e} error(s), {w} warning(s)"


_WEAK_PATTERNS = ("password", "secret", "token", "key", "api")
_MIN_SECRET_LEN = 8


def lint_env(env: Dict[str, str]) -> LintResult:
    """Analyse a dict of env vars and return a LintResult."""
    result = LintResult()

    for key, value in env.items():
        # Blank key
        if not key.strip():
            result.issues.append(LintIssue(key="(blank)", severity="error", message="Key must not be blank."))
            continue

        # Key contains spaces
        if " " in key:
            result.issues.append(LintIssue(key=key, severity="error", message="Key contains spaces."))

        # Lowercase key
        if key != key.upper():
            result.issues.append(LintIssue(key=key, severity="warning", message="Key is not uppercase."))

        # Empty value
        if value == "":
            result.issues.append(LintIssue(key=key, severity="warning", message="Value is empty."))

        # Weak secret value
        key_lower = key.lower()
        if any(pat in key_lower for pat in _WEAK_PATTERNS):
            if 0 < len(value) < _MIN_SECRET_LEN:
                result.issues.append(
                    LintIssue(
                        key=key,
                        severity="warning",
                        message=f"Secret value appears too short (< {_MIN_SECRET_LEN} chars).",
                    )
                )

        # Value contains unquoted newline literal
        if "\\n" in value and "\n" not in value:
            result.issues.append(
                LintIssue(key=key, severity="info", message="Value contains literal \\n — did you mean a newline?")
            )

    return result
