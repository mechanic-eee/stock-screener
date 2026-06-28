# Daily review routine — run the post-scan loop in one shot:
#   track.py  (how seeds/positions are doing) + monitor.py (held thesis-breaks).
# ASCII-only on purpose (no Korean here) so it needs no UTF-8 BOM; the Python
# scripts emit their own UTF-8 Korean output.
#
#   pwsh scripts/daily.ps1            # review
#   pwsh scripts/daily.ps1 -Telegram # also push monitor alerts to Telegram
param([switch]$Telegram)

$ErrorActionPreference = "Continue"
$py = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

Write-Host "=== TRACK (seeds / positions: return, days, stop distance) ===" -ForegroundColor Cyan
& $py (Join-Path $PSScriptRoot "track.py")

Write-Host "`n=== MONITOR (held positions: stop breach / new distress) ===" -ForegroundColor Cyan
$mon = @((Join-Path $PSScriptRoot "monitor.py"))
if ($Telegram) { $mon += "--telegram" }
& $py $mon

Write-Host "`n=== REMINDER ===" -ForegroundColor Yellow
Write-Host " - Curate WATCHLIST 보류 rows (fill thesis/stop/catalyst, set 관심)."
Write-Host " - Record buys/exits:  decide.py --ticker <T> [--action 청산 --exit <px>]"
Write-Host " - Deploy when the index is above its 200DMA (see the daily alert 시장: line)."
