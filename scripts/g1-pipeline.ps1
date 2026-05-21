# G1: lock structure → narrate → dual render (exportLayout=auto trip)
param(
    [Parameter(Mandatory = $true)]
    [string]$TripPath
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path $TripPath)) {
    Write-Error "trip not found: $TripPath"
}

$tripId = [System.IO.Path]::GetFileName((Split-Path $TripPath -Parent))
if ($TripPath -notmatch "trip\.json$") {
    $TripPath = Join-Path $TripPath "trip.json"
    $tripId = [System.IO.Path]::GetFileName((Split-Path $TripPath -Parent))
}

python -m travelogue lock $tripId structure
python -m travelogue narrate $tripId
python -m travelogue render $TripPath --dual
python -m travelogue validate $TripPath

Write-Host "OK G1 pipeline -> index.html + index-mobile.html"
