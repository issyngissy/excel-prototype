"""CLI: `python -m soil_agent --config config.toml [--once]`."""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from .config import load_config
from .importer import process_file
from .watcher import run, scan_inbox


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="soil_agent", description=__doc__)
    parser.add_argument("--config", default="config.toml", help="path to config.toml")
    parser.add_argument("--once", action="store_true", help="import what's in the inbox now, then exit")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if cfg.log_file:
        cfg.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(cfg.log_file, maxBytes=1_000_000, backupCount=3))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)

    if args.once:
        cfg.watch_folder.mkdir(parents=True, exist_ok=True)
        for path in scan_inbox(cfg):
            process_file(path, cfg)
        return 0

    try:
        run(cfg)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
