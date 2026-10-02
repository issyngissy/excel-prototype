"""Watch the inbox folder and import each spreadsheet that lands in it."""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config import Config
from .importer import is_candidate, process_file

log = logging.getLogger(__name__)


class _Handler(FileSystemEventHandler):
    def __init__(self, cfg: Config, work: queue.Queue):
        self.cfg = cfg
        self.work = work

    def _enqueue(self, raw_path) -> None:
        path = Path(raw_path if isinstance(raw_path, str) else raw_path.decode())
        if is_candidate(path, self.cfg):
            self.work.put(path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._enqueue(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        # Browsers and Excel write to a temp name then rename into place.
        if not event.is_directory:
            self._enqueue(event.dest_path)


def scan_inbox(cfg: Config) -> list[Path]:
    """Files already sitting in the inbox (dropped while the agent was off, or retries)."""
    return sorted(p for p in cfg.watch_folder.iterdir() if p.is_file() and is_candidate(p, cfg))


def run(cfg: Config, stop: threading.Event | None = None) -> None:
    stop = stop or threading.Event()
    cfg.watch_folder.mkdir(parents=True, exist_ok=True)
    work: queue.Queue[Path] = queue.Queue()

    observer = Observer()
    observer.schedule(_Handler(cfg, work), str(cfg.watch_folder), recursive=False)
    observer.start()
    log.info("Watching %s -> %s", cfg.watch_folder, cfg.master_file)

    for p in scan_inbox(cfg):
        work.put(p)

    # One worker thread so writes to the master never overlap.
    pending: set[Path] = set()
    next_scan = time.monotonic() + cfg.rescan_seconds
    try:
        while not stop.is_set():
            if time.monotonic() >= next_scan:
                for p in scan_inbox(cfg):
                    work.put(p)
                next_scan = time.monotonic() + cfg.rescan_seconds
            try:
                path = work.get(timeout=1)
            except queue.Empty:
                continue
            if path in pending:
                continue
            pending.add(path)
            try:
                process_file(path, cfg)
            finally:
                pending.discard(path)
    finally:
        observer.stop()
        observer.join()
