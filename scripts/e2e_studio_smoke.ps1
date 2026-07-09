# P5-10.4 · Studio zero-edit smoke: import → longshot (HTTP job API)
# Usage: .\scripts\e2e_studio_smoke.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "e2e smoke: studio import job..."
python -m pytest tests/integration/studio/test_studio_server.py::test_studio_import_job -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "e2e smoke: studio longshot job (requires playwright)..."
python -m pytest tests/integration/studio/test_studio_server.py::test_studio_longshot_job -q
exit $LASTEXITCODE
