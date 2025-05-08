"""Logging configuration for the Seplan project.

To use this logging configuration, set the environment variable
SEPLAN_LOG_CFG to the path of the logging configuration file.
The repo has a sample configuration file in the root directory.

"""

import os
import logging
import logging.config
from pathlib import Path
import tomli


def setup_logging():
    cfg_path = os.getenv("SEPLAN_LOG_CFG")
    if not cfg_path:
        return  # or call basicConfig()

    cfg_file = Path(cfg_path).expanduser()
    if not cfg_file.is_file():
        raise FileNotFoundError(f"Logging config not found at {cfg_file}")

    with cfg_file.open("rb") as f:
        cfg = tomli.load(f)

    logging.config.dictConfig(cfg)
