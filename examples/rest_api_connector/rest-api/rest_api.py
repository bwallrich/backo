"""REST API Connector example using Backoffice."""

# pylint: disable=logging-fstring-interpolation,duplicate-code

import sys
import logging
import argparse
from pathlib import Path
from flask import Flask
from flask_cors import CORS
import yaml

sys.path.insert(1, "../../../../stricto")
sys.path.insert(1, "../../../../backo")

import constants
from backo import Backoffice, log_system, LogLevel

log_system.add_handler(log_system.set_streamhandler())
log = log_system.get_or_create_logger("bubbles")


app = Flask("bubbles")


def load_config(config_path: str) -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def setup_data_dir(config: dict):
    """Set up the data directory from config."""
    data_dir = config.get("data_dir", "./data")
    data_path = Path(data_dir).resolve()
    data_path.mkdir(parents=True, exist_ok=True)
    constants.set_data_dir(data_path)
    return data_path


def main():
    """Entry point for the bubbles-back application."""
    parser = argparse.ArgumentParser(description="Bubbles Backend Server")
    parser.add_argument(
        "--config",
        "-c",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--host", "-H", help="Host to bind server to (overrides config)"
    )
    parser.add_argument(
        "--port", "-p", type=int, help="Port to bind server to (overrides config)"
    )
    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (overrides config)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
    except (FileNotFoundError, OSError, ValueError) as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

    # Set up data directory from config
    setup_data_dir(config)

    # Import collections only after DATA_DIR is configured from config.
    from collections_set import vms_coll  # pylint: disable=import-outside-toplevel

    # Override config with command line arguments
    if args.host:
        config["server"]["host"] = args.host
    if args.port:
        config["server"]["port"] = args.port
    if args.log_level:
        config["logging"]["level"] = args.log_level

    # Set up logging
    log_system.setLevel(LogLevel.get(config["logging"]["level"]))

    # My back office
    myback = Backoffice("hypervisor")

    # Add collections to backoffice
    myback.register_collection(vms_coll)

    myback.build_routes(app, "api/v1")

    # Check syntax
    myback.check_syntax()

    CORS(app, origins=["*"])

    host = config["server"]["host"]
    port = config["server"]["port"]

    logging.warning(f"Starting server on {host}:{port}")
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
