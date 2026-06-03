"""Basic tests for parse-totals."""

from src import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ == "2.0.5"


def test_version_format():
    """Test that version follows semver format."""
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
