# GRAVEYARD - one-command demo for video recording (Windows)
$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoDir

$Exports = if ($env:EXPORTS) { $env:EXPORTS } else { "examples/sample_exports" }
$V1 = if ($env:V1) { $env:V1 } else { "examples/findings_draft_v1_reject.json" }
$V2 = if ($env:V2) { $env:V2 } else { "examples/findings_draft_v2_pass.json" }
$Report = if ($env:REPORT) { $env:REPORT } else { "reports/report.md" }
$PauseSec = if ($env:PAUSE) { [int]$env:PAUSE } else { 4 }

function Pause-Step {
    Write-Host ""
    Write-Host ">>> Continuing in ${PauseSec}s (Ctrl+C to stop)..." -ForegroundColor Yellow
    Start-Sleep -Seconds $PauseSec
    Write-Host ""
}

Write-Host "=============================================="
Write-Host " GRAVEYARD Demo - ghost correlate + verifier"
Write-Host " Repo: $RepoDir"
Write-Host "=============================================="
Pause-Step

Write-Host "=== Step 1/4: graveyard_correlate ===" -ForegroundColor Cyan
python graveyard_correlate.py --exports $Exports
Pause-Step

Write-Host "=== Step 2/4: verify_findings v1 (expect REJECT) ===" -ForegroundColor Cyan
python verify_findings.py $V1 --exports $Exports --json-out 2>&1 | Write-Host
$V1Exit = $LASTEXITCODE
Write-Host "Exit code: $V1Exit (expect 1)" -ForegroundColor $(if ($V1Exit -ne 0) { "Green" } else { "Red" })
Pause-Step

Write-Host "=== Step 3/4: verify_findings v2 (expect PASS) ===" -ForegroundColor Cyan
python verify_findings.py $V2 --exports $Exports --report $Report
$V2Exit = $LASTEXITCODE
Write-Host "Exit code: $V2Exit (expect 0)" -ForegroundColor $(if ($V2Exit -eq 0) { "Green" } else { "Red" })
Pause-Step

Write-Host "=== Step 4/4: verified report ===" -ForegroundColor Cyan
Write-Host "--- $Report ---"
Get-Content $Report
Write-Host ""
Write-Host "=============================================="
Write-Host " Demo complete. Audit log: docs/execution_logs/"
Write-Host "=============================================="
