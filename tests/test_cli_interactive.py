"""Tests for the CLI commands (non-interactive parts).

Interactive prompts are not tested here since they require TTY input.
Instead we test the generate and validate subcommands.
"""

import subprocess
import sys

import pytest


class TestCliValidate:

    def test_validate_minimal_tier1(self, minimal_tier1_path):
        result = subprocess.run(
            [sys.executable, "-m", "anycost_generator", "validate", "--config", str(minimal_tier1_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Config is valid" in result.stdout

    def test_validate_full_tier2(self, full_tier2_path):
        result = subprocess.run(
            [sys.executable, "-m", "anycost_generator", "validate", "--config", str(full_tier2_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Config is valid" in result.stdout

    def test_validate_complex_tier3(self, complex_tier3_path):
        result = subprocess.run(
            [sys.executable, "-m", "anycost_generator", "validate", "--config", str(complex_tier3_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_validate_nonexistent_file(self):
        result = subprocess.run(
            [sys.executable, "-m", "anycost_generator", "validate", "--config", "/tmp/nonexistent.yaml"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0


class TestCliGenerate:

    def test_generate_from_fixture(self, minimal_tier1_path, tmp_output):
        result = subprocess.run(
            [sys.executable, "-m", "anycost_generator", "generate",
             "--config", str(minimal_tier1_path),
             "--output", str(tmp_output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Successfully generated" in result.stdout
        assert (tmp_output / "anycost.py").exists()

    def test_generate_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "anycost_generator", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout
