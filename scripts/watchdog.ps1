# Watchdog for the 08:10 daily review task. Runs weekday evenings (20:00) and
# alerts Telegram if the most recent due weekday's daily.ps1 left no trace in
# monitor-log.txt.
#
# Postmortem 2026-08-07: the 08:10 task died silently for 10 days (pwsh Store
# path vanished on auto-update) and nothing watched the watcher. This script is
# the second, INDEPENDENT failure domain: registered against the always-present
# System32 powershell.exe and speaking to Telegram directly (no python/venv).
#
# Target-day logic (audit 2026-08-08 F1): StartWhenAvailable catch-up can fire
# past midnight (e.g. Fri 06:30 for a missed Thu 20:00 trigger). Judging
# "today's log" at execution time then false-alarms before 08:10, and a
# Saturday catch-up would hide a real Friday failure behind a weekend skip.
# So: pre-noon runs verify YESTERDAY, and weekends roll back to Friday.
# ASCII-only on purpose (PS 5.1 safe without BOM).
#
#   powershell -File scripts\watchdog.ps1          # check now
param([switch]$Quiet)

$ErrorActionPreference = "Continue"

$log = Join-Path $PSScriptRoot "..\..\stock-investing\monitor-log.txt"
$envFile = Join-Path $PSScriptRoot "..\.env"
$selfLog = Join-Path $PSScriptRoot "..\..\stock-investing\watchdog-log.txt"

function Write-SelfLog([string]$state) {
    # the watcher leaves its own trace (audit F6) - bounded to ~50KB
    try {
        if ((Test-Path $selfLog) -and ((Get-Item $selfLog).Length -gt 50KB)) {
            Get-Content $selfLog -Tail 200 | Set-Content $selfLog
        }
        "$(Get-Date -Format s) watchdog: $state" | Add-Content $selfLog
    } catch {}
}

# Which day's run must exist? Evening run (>=12:00) verifies today; a pre-noon
# catch-up verifies yesterday (today's 08:10 may not be due yet). Weekend
# targets roll back to Friday instead of skipping (a Sat catch-up must still
# verify Friday).
$now = Get-Date
$target = $now.Date
if ($now.Hour -lt 12) { $target = $target.AddDays(-1) }
while ($target.DayOfWeek -eq "Saturday" -or $target.DayOfWeek -eq "Sunday") {
    $target = $target.AddDays(-1)
}

$ok = (Test-Path $log) -and ((Get-Item $log).LastWriteTime.Date -ge $target)
if ($ok) {
    if (-not $Quiet) { Write-Host "watchdog: OK (log covers $($target.ToString('yyyy-MM-dd')))" }
    Write-SelfLog "OK target=$($target.ToString('yyyy-MM-dd'))"
    exit 0
}

$msg = "[watchdog] daily review left no trace for $($target.ToString('yyyy-MM-dd')) - the 08:10 task may be dead. " +
       "Check: Get-ScheduledTask StockScreener-DailyReview / monitor-log.txt / register-daily-task.ps1"

# Parse TELEGRAM_* straight from .env (no python dependency). Trim spaces,
# then quotes, then spaces again ('" abc "' cases - audit F5).
$token = $null; $chat = $null
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*TELEGRAM_BOT_TOKEN\s*=\s*(.+)$') { $token = $Matches[1].Trim().Trim('"', "'").Trim() }
        if ($line -match '^\s*TELEGRAM_CHAT_ID\s*=\s*(.+)$')  { $chat  = $Matches[1].Trim().Trim('"', "'").Trim() }
    }
}
if ($token -and $chat) {
    try {
        Invoke-RestMethod -Method Post -Uri "https://api.telegram.org/bot$token/sendMessage" `
            -Body @{ chat_id = $chat; text = $msg } -TimeoutSec 15 | Out-Null
        Write-Host "watchdog: ALERT sent"
        Write-SelfLog "ALERT-sent target=$($target.ToString('yyyy-MM-dd'))"
    } catch {
        Write-Host "watchdog: telegram send failed - $_"
        Write-SelfLog "send-failed: $_"
    }
} else {
    Write-Host "watchdog: no telegram creds in .env - console only"
    Write-Host $msg
    Write-SelfLog "no-creds target=$($target.ToString('yyyy-MM-dd'))"
}
exit 1
