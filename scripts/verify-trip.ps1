# 验收单个 trip：validate + 可选本地预览
param(
    [Parameter(Mandatory = $true)]
    [string]$TripPath,
    [switch]$Serve
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($TripPath -notmatch "trip\.json$") {
    $TripPath = Join-Path $TripPath "trip.json"
}
if (-not (Test-Path $TripPath)) {
    Write-Error "trip not found: $TripPath"
}

$tripRoot = Split-Path $TripPath -Parent
python -m travelogue validate $TripPath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -m pytest tests/test_chapter_items_screens_sync.py tests/test_validate_vr_p05.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$html = Join-Path $tripRoot "index.html"
$mobile = Join-Path $tripRoot "index-mobile.html"
Write-Host "OK validate $TripPath"
if (Test-Path $html) { Write-Host "  Web: $html" }
if (Test-Path $mobile) { Write-Host "  Mobile: $mobile" }

if ($Serve) {
    Push-Location $tripRoot
    Write-Host "http://127.0.0.1:8766/index.html"
    python -m http.server 8766
    Pop-Location
}
