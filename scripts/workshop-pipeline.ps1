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

$args = @(
    "-m", "travelogue", "from-album", $AlbumPath,
    "--title", $Title,
    "--layout", "auto",
    "--no-render",
    "--publish:$(if ($Export) { 'true' } else { 'false' })"
)
if ($TripId) { $args += @("--trip-id", $TripId) }
if ($Place) { $args += @("--place", $Place) }
if ($Force) { $args += "--force" }
if ($Export -and $ConfirmPrivacy) { $args += "--confirm-privacy" }

python @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$tripRoot = if ($TripId) { "trips\$TripId" } else { Get-ChildItem trips -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName }
$tripJson = Join-Path $tripRoot "trip.json"
$id = [System.IO.Path]::GetFileName($tripRoot)

python -m travelogue lock $id structure
python -m travelogue narrate $id
python -m travelogue render $tripJson --dual
python -m travelogue validate $tripJson

Write-Host ""
Write-Host "OK workshop -> $tripRoot"
Write-Host "  index.html · index-mobile.html"
if ($Export) { Write-Host "  trip-$id.zip (if publish succeeded)" }
Write-Host "  python -m http.server 8766  (cd $tripRoot)"
