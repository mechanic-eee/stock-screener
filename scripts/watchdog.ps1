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
# Evidence (2026-09-05 P0-3): the transcript is written BEFORE python runs, so
# "log touched today" only proved pwsh started. Now the primary evidence is
# data\last_heartbeat.json, which review.py writes ONLY after Telegram accepted
# the message. The transcript is kept as a secondary hint for triage.
#
#   powershell -File scripts\watchdog.ps1          # check now
#   powershell -File scripts\watchdog.ps1 -DryRun  # decide, print, never send
param([switch]$Quiet, [switch]$DryRun)

$ErrorActionPreference = "Continue"

$log = Join-Path $PSScriptRoot "..\..\stock-investing\monitor-log.txt"
$hb = Join-Path $PSScriptRoot "..\data\last_heartbeat.json"
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

# Primary: heartbeat date (ISO yyyy-MM-dd, string-comparable) on/after target.
$hbDate = $null
if (Test-Path $hb) {
    try { $hbDate = (Get-Content $hb -Raw | ConvertFrom-Json).date } catch { $hbDate = $null }
}
$targetStr = $target.ToString('yyyy-MM-dd')
$ok = ($hbDate -ne $null) -and ([string]$hbDate -ge $targetStr)
if ($ok) {
    if (-not $Quiet) { Write-Host "watchdog: OK (heartbeat $hbDate covers $targetStr)" }
    Write-SelfLog "OK target=$targetStr heartbeat=$hbDate"
    exit 0
}

# Secondary hint for triage: did daily.ps1 start at all that day?
$started = (Test-Path $log) -and ((Get-Item $log).LastWriteTime.Date -ge $target)
$why = if ($started) { "daily.ps1 STARTED but no successful Telegram send was recorded (venv/token/timeout?)" }
       else { "daily.ps1 never started (task disabled, PC off/asleep, shell path?)" }
$msg = "[watchdog] no heartbeat for $targetStr - $why " +
       "Check: Get-ScheduledTask StockScreener-DailyReview / data\last_heartbeat.json / monitor-log.txt"
if ($DryRun) {
    Write-Host "watchdog(dry-run): would ALERT - $msg"
    Write-SelfLog "DRYRUN-alert target=$targetStr heartbeat=$hbDate started=$started"
    exit 1
}

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
