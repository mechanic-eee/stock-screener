# Daily review routine — run the post-scan loop in one shot:
#   track.py  (how seeds/positions are doing) + monitor.py (held thesis-breaks).
# ASCII-only on purpose (no Korean here) so it needs no UTF-8 BOM; the Python
# scripts emit their own UTF-8 Korean output.
#
#   pwsh scripts/daily.ps1            # review
#   pwsh scripts/daily.ps1 -Telegram # also push monitor alerts to Telegram
param([switch]$Telegram)

$ErrorActionPreference = "Continue"

# Python prints UTF-8 Korean; a hidden scheduled window decodes it as cp949 and
# the transcript ends up unreadable ("?????"), hiding even the sent/failed line.
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$env:PYTHONIOENCODING = "utf-8"

# Append a transcript so a scheduled (hidden-window) run is diagnosable; keep
# the log bounded (~200KB) so it never grows unattended.
$logPath = Join-Path $PSScriptRoot "..\..\stock-investing\monitor-log.txt"
try {
    if ((Test-Path $logPath) -and ((Get-Item $logPath).Length -gt 200KB)) {
        Get-Content $logPath -Tail 500 | Set-Content $logPath -Encoding utf8
    }
    Start-Transcript -Path $logPath -Append | Out-Null
} catch {}

$py = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

# Track failures so the scheduled task shows a real result instead of always 0
# (audit finding 12: swallowed failures made 'Last Run Result' always success).
$fail = 0

# Native exe stdout bypasses Start-Transcript unless routed through the host —
# the log had empty TRACK/MONITOR sections until 2026-07-19 (audit finding).

# REVIEW runs FIRST: it is the only daily heartbeat (writes data/last_heartbeat.json
# after a successful send), so it must not sit behind track+monitor inside the
# 30-minute ExecutionTimeLimit (observed 11-15 min total).
Write-Host "=== REVIEW (personal holdings: discipline dashboard) ===" -ForegroundColor Cyan
$rev = @((Join-Path $PSScriptRoot "review.py"))
if ($Telegram) { $rev += "--telegram" }
& $py $rev 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { $fail = 1 }

Write-Host "`n=== TRACK (seeds / positions: return, days, stop distance) ===" -ForegroundColor Cyan
& $py (Join-Path $PSScriptRoot "track.py") 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { $fail = 1 }

Write-Host "`n=== MONITOR (system positions: stop breach / distress / weekly report) ===" -ForegroundColor Cyan
$mon = @((Join-Path $PSScriptRoot "monitor.py"))
# review.py provides the daily heartbeat; keep monitor's alerts + Monday weekly report
if ($Telegram) { $mon += "--telegram"; $mon += "--no-heartbeat" }
& $py $mon 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { $fail = 1 }

Write-Host "`n=== REMINDER ===" -ForegroundColor Yellow
Write-Host " - Curate WATCHLIST 보류 rows (fill thesis/stop/catalyst, set 관심)."
Write-Host " - Record buys/exits:  decide.py --ticker <T> [--action 청산 --exit <px>]"
Write-Host " - Deploy when the index is above its 200DMA (see the daily alert 시장: line)."

try { Stop-Transcript | Out-Null } catch {}
if ($fail -ne 0) { exit 1 }   # surface any step failure to Task Scheduler
