from pathlib import Path

DATA_DIR = None


def set_data_dir(path: Path):
    """Set the runtime data directory loaded from configuration."""
    global DATA_DIR
    DATA_DIR = path


def get_data_dir() -> Path:
    """Return the configured data directory, raising if unset."""
    if DATA_DIR is None:
        raise RuntimeError(
            "DATA_DIR is not configured. Load config and call setup_data_dir first."
        )
    return DATA_DIR
