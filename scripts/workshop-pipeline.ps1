# 本地工坊一条龙：相册 → ingest → curate → G1 → dual render → validate [→ export]
param(
    [Parameter(Mandatory = $true)]
    [string]$AlbumPath,
    [string]$TripId = "",
    [string]$Title = "我的游记",
    [string]$Place = "",
    [switch]$Force,
    [switch]$Export,
    [switch]$ConfirmPrivacy
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path $AlbumPath)) {
    Write-Error "album not found: $AlbumPath"
}

if ($Export -and -not $ConfirmPrivacy) {
    Write-Error "-Export requires -ConfirmPrivacy (sets privacy.confirmedAt, strips EXIF in zip)"
}

$fromAlbumArgs = @(
    "-m", "travelogue", "from-album", $AlbumPath,
    "--title", $Title,
    "--layout", "auto",
    "--no-render"
)
if ($TripId) { $fromAlbumArgs += @("--trip-id", $TripId) }
if ($Place) { $fromAlbumArgs += @("--place", $Place) }
if ($Force) { $fromAlbumArgs += "--force" }

python @fromAlbumArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$tripRoot = if ($TripId) { "trips\$TripId" } else { Get-ChildItem trips -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName }
$tripJson = Join-Path $tripRoot "trip.json"
$id = [System.IO.Path]::GetFileName($tripRoot)

python -m travelogue lock $id structure
python -m travelogue narrate $id
python -m travelogue render $tripJson --dual
python -m travelogue validate $tripJson

if ($Export) {
    python -m travelogue lock $id copy
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    python -m travelogue export $id --confirm-privacy
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "OK workshop -> $tripRoot"
Write-Host "  index.html · index-mobile.html"
if ($Export) { Write-Host "  trip-$id.zip" }
Write-Host "  python -m http.server 8766  (cd $tripRoot)"
