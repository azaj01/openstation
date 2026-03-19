"""OpenStation CLI — manage the Open Station task vault."""


def _resolve_version() -> str:
    # 1. Build-time baked version (used by zipapp)
    try:
        from openstation._version import __version__ as _baked
        return _baked
    except ImportError:
        pass

    # 2. Package metadata (used by pip install)
    try:
        from importlib.metadata import version as _pkg_version
        return _pkg_version("openstation")
    except Exception:
        pass

    return "dev"


__version__ = _resolve_version()
