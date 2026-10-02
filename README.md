# excel-prototype

Soil test import agent. It watches a folder on Windows or macOS and, whenever a
lab spreadsheet (`.xlsx` / `.xlsm`) lands there, appends every result row to a
master workbook.

## How it works

1. A background process watches `watch_folder` (OS file events, plus a rescan every 60s).
2. When a new spreadsheet appears, it waits until the copy/download finishes.
3. It finds the header row (title rows above the table are fine) and maps lab
   column names to master columns using the aliases in `config.toml`.
4. Rows are appended to `master_file`, with `Source File` and `Imported At` columns.
   Columns the master doesn't have yet are added (set `add_new_columns = false` to stop that).
5. The incoming file moves to `Processed/` (or `Failed/` if it can't be read).

Safety:
- The same file dropped twice is only imported once (SHA-256 ledger next to the master).
- The master is written via temp file + rename, and the previous version is kept as `.bak`.
- If the master is open in Excel (Windows locks it), the file stays in the inbox
  and is retried on the next rescan.

## Setup

```bash
cp config.example.toml config.toml   # then edit paths and column aliases
pip install -r requirements.txt
python -m soil_agent --config config.toml          # run in foreground
python -m soil_agent --config config.toml --once   # import what's in the inbox, then exit
```

Run automatically at login:

- **Windows**: `powershell -ExecutionPolicy Bypass -File install\windows\install.ps1` (Scheduled Task)
- **macOS**: `bash install/macos/install.sh` (launchd agent)

## Known limits

- openpyxl rewrites the master on save. Charts, images and pivot tables in the
  master workbook are **not preserved**. Keep those on a separate workbook that
  links to the master.
- Only the first sheet of each incoming file is read (or `source_sheet`).
- Cells are read as their last calculated values, not formulas.

## Tests

```bash
pip install pytest
python -m pytest
```
