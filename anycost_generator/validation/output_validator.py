"""Post-generation validation.

Checks the generated output for:
- All expected files exist
- Python files are syntactically valid
- No unresolved template placeholders remain
- .env.example contains all required env vars
"""

from __future__ import annotations

import ast
from pathlib import Path


class OutputValidationError:
    def __init__(self, file: str, message: str, severity: str = "error"):
        self.file = file
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity.upper()}] {self.file}: {self.message}"


def validate_output(
    output_dir: str | Path,
    provider_name: str,
    required_env_vars: list[str],
) -> list[OutputValidationError]:
    """Validate a generated adaptor project.

    Returns a list of validation errors/warnings. Empty list means valid.
    """
    output = Path(output_dir)
    errors: list[OutputValidationError] = []

    # Expected files
    expected_files = [
        "anycost.py",
        "pyproject.toml",
        "README.md",
        ".gitignore",
        "env/.env.example",
        f"src/{provider_name}_config.py",
        f"src/{provider_name}_client.py",
        f"src/{provider_name}_transform.py",
        f"src/{provider_name}_anycost_adaptor.py",
        "src/cloudzero.py",
    ]

    for expected in expected_files:
        path = output / expected
        if not path.exists():
            errors.append(OutputValidationError(expected, "Expected file is missing"))

    # Check Python syntax
    for py_file in output.rglob("*.py"):
        rel = py_file.relative_to(output)
        try:
            source = py_file.read_text()
            ast.parse(source)
        except SyntaxError as e:
            errors.append(OutputValidationError(
                str(rel),
                f"Python syntax error: {e.msg} (line {e.lineno})",
            ))

    # Check for unresolved Jinja2 placeholders
    for text_file in list(output.rglob("*.py")) + list(output.rglob("*.toml")) + list(output.rglob("*.md")):
        rel = text_file.relative_to(output)
        content = text_file.read_text()
        if "{{" in content and "}}" in content:
            errors.append(OutputValidationError(
                str(rel),
                "Unresolved template placeholder found (contains {{ }})",
            ))
        if "{%" in content and "%}" in content:
            errors.append(OutputValidationError(
                str(rel),
                "Unresolved Jinja2 block tag found (contains {% %})",
                severity="warning",
            ))

    # Check .env.example contains all required env vars
    env_example = output / "env" / ".env.example"
    if env_example.exists():
        env_content = env_example.read_text()
        for var in required_env_vars:
            if var not in env_content:
                errors.append(OutputValidationError(
                    "env/.env.example",
                    f"Missing required env var: {var}",
                ))

    return errors
