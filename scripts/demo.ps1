# Travelogue unified demo helper (Windows)
# Usage:
#   .\scripts\demo.ps1 "D:\Photos\album" -Title "雨后京都"
#   .\scripts\demo.ps1 "D:\Photos\album" -Title "雨后京都" -Publish -Force
#   .\scripts\demo.ps1 -Verify
#   .\scripts\demo.ps1 -Golden

param(
    [Parameter(Position = 0)]
    [string]$Album,
    [string]$Title = "我的旅途",
    [string]$Place = "旅途",
    [ValidateSet("mobile", "web", "auto")]
    [string]$Layout = "mobile",
    [switch]$Force,
    [switch]$Publish,
    [switch]$Verify,
    [switch]$Golden,
    [switch]$FullVerify,
    [switch]$SyncReference
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Invoke-Travelogue {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$CliArgs)
    python -m travelogue @CliArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if ($Verify) {
    $vargs = @("demo", "verify")
    if ($Album) { $vargs += @("--album", $Album) }
    if ($FullVerify) { $vargs += "--full" }
    if ($SyncReference) { $vargs += "--sync-reference" }
    Invoke-Travelogue @vargs
    exit $LASTEXITCODE
}

if ($Golden) {
    $gargs = @("demo", "golden")
    if ($SyncReference) { $gargs += "--sync-reference" }
    Invoke-Travelogue @gargs
    exit $LASTEXITCODE
}

if (-not $Album) {
    Write-Host "Usage: .\scripts\demo.ps1 <album> [-Title ...] [-Publish] [-Force] | -Verify | -Golden"
    exit 1
}

$cliArgs = @(
    "from-album", $Album,
    "--title", $Title,
    "--place", $Place,
    "--layout", $Layout
)
if ($Force) { $cliArgs += "--force" }
if ($Publish) { $cliArgs += "--publish" }
Invoke-Travelogue @cliArgs
