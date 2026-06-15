# GRAVEYARD — deterministic autonomous self-correction loop (Windows)
# engine → draft findings from facts → verify → auto-correct → verify (max 3 iter)
param(
    [string]$Exports = "examples/sample_exports",
    [string]$Timeline = "",
    [string]$CaseDir = "",
    [int]$MaxIter = 3,
    [switch]$NoDemoInject
)

$ErrorActionPreference = "Stop"
$RepoDir = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$RepoDir/graveyard_engine.py")) { $RepoDir = $PSScriptRoot }
if (-not $CaseDir) { $CaseDir = $RepoDir }
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
Set-Location $CaseDir

New-Item -ItemType Directory -Force -Path analysis, reports, docs/execution_logs | Out-Null

Write-Host "=== GRAVEYARD Agent Loop (deterministic self-correction) ==="
Write-Host "Exports:  $Exports"
Write-Host "Timeline: $(if ($Timeline) { $Timeline } else { 'none' })"
Write-Host "Max iter: $MaxIter"
Write-Host ""

Write-Host "[1] graveyard_engine"
$engineOut = "analysis/graveyard_engine_$Ts.json"
$engineArgs = @("--exports", $Exports, "--output", $engineOut)
if ($Timeline -and (Test-Path $Timeline)) { $engineArgs += @("--timeline", $Timeline) }
python "$RepoDir/graveyard_engine.py" @engineArgs

$draft = "findings_draft_$Ts.json"
Write-Host "[2] generate findings from engine facts"
$draftArgs = @("--exports", $Exports, "--engine-report", $engineOut, "--output", $draft)
if ($Timeline -and (Test-Path $Timeline)) { $draftArgs += @("--timeline", $Timeline) }
if (-not $NoDemoInject) {
    Write-Host "      (demo mode: injecting attribution violation for self-correction proof)"
    $draftArgs += "--inject-bad"
}
python "$RepoDir/scripts/auto_correct_findings.py" @draftArgs

$auditLog = "docs/execution_logs/agent_loop_$Ts.jsonl"
$current = $draft
$finalExit = 1

for ($iter = 1; $iter -le $MaxIter; $iter++) {
    Write-Host ""
    Write-Host "[verify $iter/$MaxIter] $current"
    $verifyArgs = @($current, "--exports", $Exports, "--audit-log", $auditLog, "--report", "reports/report_$Ts.md")
    $ErrorActionPreference = "Continue"
    python "$RepoDir/verify_findings.py" @verifyArgs 2>&1 | Write-Host
    $vExit = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    Write-Host "      exit code: $vExit"

    if ($vExit -eq 0) {
        $finalExit = 0
        Write-Host ""
        Write-Host "=== Agent Loop Complete — PASS on iteration $iter ===" -ForegroundColor Green
        break
    }

    if ($iter -ge $MaxIter) {
        Write-Host ""
        Write-Host "=== Agent Loop Complete — FAIL after $MaxIter iteration(s) ===" -ForegroundColor Red
        break
    }

    $corrected = "findings_corrected_iter${iter}_$Ts.json"
    Write-Host "[auto-correct $iter/$MaxIter] rebuild from engine facts (no LLM)"
    $correctArgs = @("--exports", $Exports, "--engine-report", $engineOut, "--output", $corrected)
    if ($Timeline -and (Test-Path $Timeline)) { $correctArgs += @("--timeline", $Timeline) }
    python "$RepoDir/scripts/auto_correct_findings.py" @correctArgs
    $current = $corrected
}

Write-Host ""
Write-Host "  Engine report:  $engineOut"
Write-Host "  Final findings: $current"
Write-Host "  Audit log:      $auditLog"
if ($finalExit -eq 0) {
    Write-Host "  Report:         reports/report_$Ts.md"
    Write-Host ""
    Write-Host "RESULT: PASS — deterministic self-correction demonstrated" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "RESULT: FAIL — findings still rejected after $MaxIter iteration(s)" -ForegroundColor Red
}
exit $finalExit
