"""OpenStation CLI — manage the Open Station task vault."""

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("openstation")
except Exception:
    __version__ = "dev"
