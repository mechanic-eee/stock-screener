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

# prefer pwsh, fall back to Windows PowerShell
$shell = (Get-Command pwsh -ErrorAction SilentlyContinue).Source
if (-not $shell) { $shell = (Get-Command powershell).Source }

$action = New-ScheduledTaskAction -Execute $shell -Argument (
    "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$daily`" -Telegram")
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday, Tuesday, Wednesday, Thursday, Friday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 30)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Stock screener daily review: track + monitor (thesis-break telegram)" -Force | Out-Null
Write-Host "registered: $TaskName (weekdays $Time, catch-up on wake, telegram on)"
Write-Host "log: ..\stock-investing\monitor-log.txt  |  remove: -Unregister"
