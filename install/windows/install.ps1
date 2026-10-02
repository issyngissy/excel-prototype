# Registers the soil agent as a Scheduled Task that starts when you log in
# and restarts if it crashes. Run from the repo root in PowerShell:
#   powershell -ExecutionPolicy Bypass -File install\windows\install.ps1
# Remove with:
#   Unregister-ScheduledTask -TaskName SoilTestAgent -Confirm:$false

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$Config = Join-Path $RepoRoot "config.toml"

if (-not (Test-Path $Config)) {
    Copy-Item (Join-Path $RepoRoot "config.example.toml") $Config
    Write-Host "Created $Config. Edit the paths in it, then run this script again."
    exit 1
}

# pythonw runs without a console window.
$Python = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $Python) { throw "pythonw.exe not found. Install Python 3.11+ from python.org and tick 'Add to PATH'." }

& ($Python -replace "pythonw.exe$", "python.exe") -m pip install --user -r (Join-Path $RepoRoot "requirements.txt")

$Action = New-ScheduledTaskAction -Execute $Python -Argument "-m soil_agent --config `"$Config`"" -WorkingDirectory $RepoRoot
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName "SoilTestAgent" -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
Start-ScheduledTask -TaskName "SoilTestAgent"
Write-Host "SoilTestAgent installed and running. Log file path is set in config.toml."
