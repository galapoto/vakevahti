import argparse

import pytest

from app.cli import _source_code


def test_source_code_normalizes_registered_sources() -> None:
    assert _source_code("eura") == "EURA"
    assert _source_code("  haeavustuksia  ") == "HAEAVUSTUKSIA"


def test_source_code_rejects_unknown_sources() -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="Registered sources"):
        _source_code("unknown")
