# Register (or remove) a Windows Scheduled Task that runs the daily review
# (track + monitor --telegram) on weekday mornings — the "exit door" of the
# loop runs even when the human forgets.
#
#   pwsh scripts/register-daily-task.ps1              # register / update
#   pwsh scripts/register-daily-task.ps1 -Unregister  # remove
#
# Notes (the parts that make this insurance instead of theater):
#  - StartWhenAvailable: fires after laptop wake if the trigger time was missed.
#  - Output is captured by daily.ps1's transcript (monitor-log.txt), so a
#    silently dying task is diagnosable.
# ASCII-only on purpose (no UTF-8 BOM needed).
param(
    [switch]$Unregister,
    [string]$Time = "08:10"   # after the 07:00 KST telegram alert
)

$TaskName = "StockScreener-DailyReview"

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "unregistered: $TaskName"
    exit 0
}

$daily = Join-Path $PSScriptRoot "daily.ps1"
if (-not (Test-Path $daily)) { Write-Error "daily.ps1 not found: $daily"; exit 1 }

# prefer STABLE shell paths only. Get-Command pwsh can resolve to a Store
# versioned path (WindowsApps\Microsoft.PowerShell_<ver>__...) that VANISHES on
# auto-update — killed this task with 0x80070002 silently for 10 days
# (2026-07-28 ~ 08-07 postmortem: no morning telegram, incl. a stop-breach alert).
$shell = "C:\Program Files\PowerShell\7\pwsh.exe"                                # MSI install (stable)
if (-not (Test-Path $shell)) { $shell = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\pwsh.exe" }  # Store alias (stable across updates)
if (-not (Test-Path $shell)) { $shell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe" }  # always exists

$action = New-ScheduledTaskAction -Execute $shell -Argument (
    "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$daily`" -Telegram")
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Stock screener daily review: track + monitor (thesis-break telegram)" -Force | Out-Null
Write-Host "registered: $TaskName (weekdays $Time, catch-up on wake, telegram on)"
Write-Host "log: ..\stock-investing\monitor-log.txt  |  remove: -Unregister"
