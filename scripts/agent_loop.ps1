# GRAVEYARD — deterministic autonomous self-correction loop (Windows)
# correlate → draft → verify → auto-correct from engine facts → verify again
param(
    [string]$Exports = "examples/sample_exports",
    [string]$Timeline = "",
    [string]$CaseDir = $PSScriptRoot
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$RepoDir/graveyard_engine.py")) { $RepoDir = $PSScriptRoot }
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
if ($CaseDir -eq $PSScriptRoot) { $CaseDir = $RepoDir }
Set-Location $CaseDir

New-Item -ItemType Directory -Force -Path analysis, reports, docs/execution_logs | Out-Null

Write-Host "=== GRAVEYARD Agent Loop (deterministic self-correction) ==="
Write-Host "Exports: $Exports"
Write-Host "Case:    $CaseDir"
Write-Host ""

Write-Host "[1/5] graveyard_engine"
$engineArgs = @("--exports", $Exports, "--output", "analysis/graveyard_engine_$Ts.json")
if ($Timeline -and (Test-Path $Timeline)) { $engineArgs += @("--timeline", $Timeline) }
python "$RepoDir/graveyard_engine.py" @engineArgs

Write-Host "[2/5] draft findings (with demo attribution violation)"
python "$RepoDir/scripts/auto_correct_findings.py" `
    --exports $Exports `
    --engine-report "analysis/graveyard_engine_$Ts.json" `
    --output "findings_draft_v1_$Ts.json" `
    --inject-bad

Write-Host "[3/5] verify v1 (expect REJECT)"
python "$RepoDir/verify_findings.py" "findings_draft_v1_$Ts.json" `
    --exports $Exports `
    --audit-log "docs/execution_logs/agent_loop_$Ts.jsonl" `
    --json-out 2>&1 | Write-Host
$V1Exit = $LASTEXITCODE
Write-Host "v1 exit code: $V1Exit (expect 1)"

if ($V1Exit -eq 0) {
    Write-Host "WARNING: v1 passed unexpectedly"
    Copy-Item "findings_draft_v1_$Ts.json" "findings_draft_corrected_$Ts.json"
} else {
    Write-Host "[4/5] auto_correct_findings (engine facts only, no LLM)"
    python "$RepoDir/scripts/auto_correct_findings.py" `
        --exports $Exports `
        --engine-report "analysis/graveyard_engine_$Ts.json" `
        --output "findings_draft_corrected_$Ts.json"
}

Write-Host "[5/5] verify corrected (expect PASS)"
python "$RepoDir/verify_findings.py" "findings_draft_corrected_$Ts.json" `
    --exports $Exports `
    --report "reports/report_$Ts.md" `
    --audit-log "docs/execution_logs/agent_loop_$Ts.jsonl"
$V2Exit = $LASTEXITCODE

Write-Host ""
Write-Host "=== Agent Loop Complete ==="
Write-Host "  Engine report: analysis/graveyard_engine_$Ts.json"
Write-Host "  v1 exit: $V1Exit | corrected exit: $V2Exit"

if ($V1Exit -ne 0 -and $V2Exit -eq 0) {
    Write-Host "RESULT: PASS - deterministic self-correction demonstrated" -ForegroundColor Green
    exit 0
} elseif ($V2Exit -eq 0) {
    Write-Host "RESULT: PASS - findings verified" -ForegroundColor Green
    exit 0
} else {
    Write-Host "RESULT: FAIL - corrected findings still rejected" -ForegroundColor Red
    exit 1
}
