"""Load and validate the agent's TOML config."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


def _path(value: str, base: Path) -> Path:
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base / p).resolve()


@dataclass
class Config:
    watch_folder: Path
    master_file: Path
    master_sheet: str = "Soil Tests"
    processed_folder: Path | None = None
    failed_folder: Path | None = None
    log_file: Path | None = None
    source_sheet: str | None = None
    add_new_columns: bool = True
    rescan_seconds: int = 60
    # Master column name -> list of incoming header spellings that mean the same thing.
    columns: dict[str, list[str]] = field(default_factory=dict)

    @property
    def ledger_file(self) -> Path:
        return self.master_file.with_name(f".{self.master_file.stem}.imported.json")


def load_config(path: str | Path) -> Config:
    path = Path(path).expanduser().resolve()
    with path.open("rb") as f:
        raw = tomllib.load(f)

    base = path.parent
    for key in ("watch_folder", "master_file"):
        if key not in raw:
            raise ValueError(f"config is missing required key: {key}")

    watch = _path(raw["watch_folder"], base)
    cfg = Config(
        watch_folder=watch,
        master_file=_path(raw["master_file"], base),
        master_sheet=raw.get("master_sheet", "Soil Tests"),
        processed_folder=_path(raw.get("processed_folder", str(watch / "Processed")), base),
        failed_folder=_path(raw.get("failed_folder", str(watch / "Failed")), base),
        log_file=_path(raw["log_file"], base) if raw.get("log_file") else None,
        source_sheet=raw.get("source_sheet") or None,
        add_new_columns=bool(raw.get("add_new_columns", True)),
        rescan_seconds=int(raw.get("rescan_seconds", 60)),
        columns={str(k): [str(a) for a in v] for k, v in raw.get("columns", {}).items()},
    )
    return cfg
