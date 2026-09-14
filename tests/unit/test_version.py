from importlib.metadata import version

from ai_systems import __version__


def test_package_version_matches_installed_metadata() -> None:
    assert __version__ == version("ai-systems-engineering") == "0.1.0"
