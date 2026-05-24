# Compare legacy vs screens Web layout for the same trip.json
# Usage:
#   .\scripts\compare-web-layout.ps1 trips\demo-kyoto-2025
#   .\scripts\compare-web-layout.ps1 trips\demo-kyoto-2025 -Serve
# Cross-platform: python scripts/compare_web_layout.py trips\<tripId>

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$TripPath,
    [int]$Port = 8766,
    [switch]$Serve
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Invoke-Travelogue {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)
    python -m travelogue @CliArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$TripJson = $TripPath
if (-not $TripJson.EndsWith("trip.json")) {
    $TripJson = Join-Path $TripPath "trip.json"
}
if (-not (Test-Path $TripJson)) {
    Write-Error "trip.json not found: $TripJson"
}

$Dir = Split-Path -Parent $TripJson
Write-Host "==> layout web + screens (writes screens[] to trip.json)"
Invoke-Travelogue layout $TripJson --layout web --web-layout screens

Write-Host "==> render legacy -> index-legacy.html"
Invoke-Travelogue render $TripJson --web-layout legacy --index-name index-legacy.html --out $Dir

Write-Host "==> render screens -> index-screens.html"
Invoke-Travelogue render $TripJson --web-layout screens --index-name index-screens.html --out $Dir

Write-Host ""
Write-Host "Open for A/B compare:"
Write-Host "  legacy:  $Dir\index-legacy.html"
Write-Host "  screens: $Dir\index-screens.html"
Write-Host ""
Write-Host "Tip: desktop width >= 1280px; screens uses 16:9 stage grids."

if ($Serve) {
    Push-Location $Dir
    try {
        Write-Host "Serving http://127.0.0.1:$Port/ (Ctrl+C to stop)"
        python -m http.server $Port
    } finally {
        Pop-Location
    }
}
