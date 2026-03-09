"""OpenStation CLI — manage the Open Station task vault."""


def _read_version():
    try:
        from pathlib import Path
        vfile = Path(__file__).resolve().parent.parent.parent / ".version"
        return vfile.read_text(encoding="utf-8").strip()
    except Exception:
        return "dev"


__version__ = _read_version()
