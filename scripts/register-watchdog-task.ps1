# Register (or remove) the evening watchdog task — the INDEPENDENT second
# failure domain for the 08:10 daily review (postmortem 2026-08-07).
# Uses the always-present System32 powershell.exe by absolute path so a pwsh
# auto-update can never kill BOTH tasks the same way.
#
#   powershell scripts/register-watchdog-task.ps1              # register
#   powershell scripts/register-watchdog-task.ps1 -Unregister  # remove
param(
    [switch]$Unregister,
    [string]$Time = "20:00"
)

$TaskName = "StockScreener-Watchdog"

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "unregistered: $TaskName"
    exit 0
}

$wd = Join-Path $PSScriptRoot "watchdog.ps1"
if (-not (Test-Path $wd)) { Write-Error "watchdog.ps1 not found: $wd"; exit 1 }

# deliberately NOT pwsh — independent failure domain (see watchdog.ps1 header)
$shell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

$action = New-ScheduledTaskAction -Execute $shell -Argument (
    "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$wd`"")
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Alerts Telegram if the 08:10 daily review left no trace today" -Force | Out-Null
Write-Host "registered: $TaskName (weekdays $Time, System32 powershell, catch-up on wake)"
