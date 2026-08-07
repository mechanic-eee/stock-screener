# Watchdog for the 08:10 daily review task. Runs weekday evenings (20:00) and
# alerts Telegram if today's daily.ps1 left no trace in monitor-log.txt.
#
# Postmortem 2026-08-07: the 08:10 task died silently for 10 days (pwsh Store
# path vanished on auto-update) and nothing watched the watcher. This script is
# the second, INDEPENDENT failure domain: registered against the always-present
# System32 powershell.exe and speaking to Telegram directly (no python/venv).
# ASCII-only on purpose (PS 5.1 safe without BOM).
#
#   powershell -File scripts\watchdog.ps1          # check now
param([switch]$Quiet)

$ErrorActionPreference = "Continue"

$log = Join-Path $PSScriptRoot "..\..\stock-investing\monitor-log.txt"
$envFile = Join-Path $PSScriptRoot "..\.env"

# Weekend: nothing scheduled, nothing to verify.
$dow = (Get-Date).DayOfWeek
if ($dow -eq "Saturday" -or $dow -eq "Sunday") { exit 0 }

$ok = (Test-Path $log) -and ((Get-Item $log).LastWriteTime.Date -eq (Get-Date).Date)
if ($ok) { if (-not $Quiet) { Write-Host "watchdog: OK (log written today)" }; exit 0 }

$msg = "[watchdog] daily review left no trace today - the 08:10 task may be dead. " +
       "Check: Get-ScheduledTask StockScreener-DailyReview / monitor-log.txt / register-daily-task.ps1"

# Parse TELEGRAM_* straight from .env (no python dependency).
$token = $null; $chat = $null
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*TELEGRAM_BOT_TOKEN\s*=\s*(.+)\s*$') { $token = $Matches[1].Trim('"', "'") }
        if ($line -match '^\s*TELEGRAM_CHAT_ID\s*=\s*(.+)\s*$')  { $chat  = $Matches[1].Trim('"', "'") }
    }
}
if ($token -and $chat) {
    try {
        Invoke-RestMethod -Method Post -Uri "https://api.telegram.org/bot$token/sendMessage" `
            -Body @{ chat_id = $chat; text = $msg } -TimeoutSec 15 | Out-Null
        Write-Host "watchdog: ALERT sent"
    } catch { Write-Host "watchdog: telegram send failed - $_" }
} else {
    Write-Host "watchdog: no telegram creds in .env - console only"
    Write-Host $msg
}
exit 1
