"""Runtime constants shared across the application."""

from pathlib import Path

_state: dict = {"data_dir": None}


def set_data_dir(path: Path):
    """Set the runtime data directory loaded from configuration."""
    _state["data_dir"] = path


def get_data_dir() -> Path:
    """Return the configured data directory, raising if unset."""
    if _state["data_dir"] is None:
        raise RuntimeError(
            "DATA_DIR is not configured. Load config and call setup_data_dir first."
        )
    return _state["data_dir"]
