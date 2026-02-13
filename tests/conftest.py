"""Shared test fixtures for the AnyCost Generator test suite."""

import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EXAMPLES_DIR = Path(__file__).parent.parent / "config" / "examples"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def examples_dir():
    return EXAMPLES_DIR


@pytest.fixture
def minimal_class1_path():
    return FIXTURES_DIR / "minimal_class1.yaml"


@pytest.fixture
def full_class2_path():
    return FIXTURES_DIR / "full_class2.yaml"


@pytest.fixture
def complex_class3_path():
    return FIXTURES_DIR / "complex_class3.yaml"


@pytest.fixture
def tmp_output(tmp_path):
    """Provide a temporary output directory."""
    out = tmp_path / "output"
    out.mkdir()
    return out
