# Register a ONE-TIME Windows scheduled task that runs scripts/brief.ps1 -Kind <kind>
# at a local date-time (wakes the PC from sleep, catches up if missed). Re-running
# with the same -Kind replaces the task.
#
#   powershell -File scripts\register-brief-task.ps1 -Kind paper8w -At "2026-09-12 09:00"
#   powershell -File scripts\register-brief-task.ps1 -Kind paper8w -Unregister
param(
    [Parameter(Mandatory=$true)][string]$Kind,
    [string]$At,
    [switch]$Unregister
)

$TaskName = "StockScreener-Brief-$Kind"
if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "unregistered: $TaskName"
    exit 0
}
if (-not $At) { Write-Error "-At 'YYYY-MM-DD HH:mm' required"; exit 1 }
$when = [datetime]::ParseExact($At, "yyyy-MM-dd HH:mm", $null)
if ($when -le (Get-Date)) { Write-Error "-At must be in the future: $when"; exit 1 }

$brief = Join-Path $PSScriptRoot "brief.ps1"
if (-not (Test-Path $brief)) { Write-Error "brief.ps1 not found: $brief"; exit 1 }

# stable shell paths only (see register-daily-task.ps1 postmortem 2026-08-07)
$shell = "C:\Program Files\PowerShell\7\pwsh.exe"
if (-not (Test-Path $shell)) { $shell = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\pwsh.exe" }
if (-not (Test-Path $shell)) { $shell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe" }

$action = New-ScheduledTaskAction -Execute $shell -Argument (
    "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$brief`" -Kind $Kind")
$trigger = New-ScheduledTaskTrigger -Once -At $when
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 40)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "Stock screener briefing ($Kind): read-only headless Claude -> Telegram" -Force | Out-Null
Write-Host "registered: $TaskName at $($when.ToString('yyyy-MM-dd HH:mm')) (wake-to-run, catch-up)"
Write-Host "log: ..\stock-investing\brief-log.txt  |  remove: -Kind $Kind -Unregister"
