#requires -Version 5.1
<#
.SYNOPSIS
    VOYAGE-CONTROL-LOOP-3 - read-only handoff protocol helper.

.DESCRIPTION
    Prints expected handoff paths, UTF-8 rules, and safe clipboard commands.
    Default mode does not write files and does not copy to clipboard.
#>

[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$ReportPath = "",
    [string]$NextActionPath = ""
)

$ErrorActionPreference = "Continue"

function Write-Section { param([string]$Text) Write-Host ""; Write-Host $Text -ForegroundColor White }
function Write-Info { param([string]$Text) Write-Host "  [INFO] $Text" -ForegroundColor Gray }
function Write-Ok { param([string]$Text) Write-Host "  [OK]   $Text" -ForegroundColor Green }
function Write-WarnLine { param([string]$Text) Write-Host "  [WARN] $Text" -ForegroundColor Yellow }

function Resolve-LocalPath {
    param([Parameter(Mandatory)][string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " VOYAGE CONTROL LOOP - HANDOFF PROTOCOL" -ForegroundColor Cyan
Write-Host " Phase: VOYAGE-CONTROL-LOOP-3   Mode: READ-ONLY" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$RepoPath = Resolve-LocalPath -Path $RepoPath
if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $ReportPath = "docs\handoff\LATEST_AGENT_REPORT.md"
}
if ([string]::IsNullOrWhiteSpace($NextActionPath)) {
    $NextActionPath = "docs\handoff\NEXT_ACTION.md"
}

$copyLatest = Join-Path $RepoPath "tools\copy_latest_report.ps1"
$copyAny = Join-Path $RepoPath "tools\copy_report_to_clipboard.ps1"

Write-Info "Repo path: $RepoPath"
Write-Info "No files will be written."
Write-Info "Clipboard copying will not be executed by this helper."

Write-Section "--- Expected handoff files ---"
Write-Host "  Report:      $ReportPath"
Write-Host "  Next action: $NextActionPath"

Write-Section "--- UTF-8 rules ---"
Write-Info "Write handoff reports as UTF-8."
Write-Info "Read report files as UTF-8 when copying or relaying content."
Write-Info "Avoid legacy Windows encodings for multilingual text."

Write-Section "--- Secrets policy ---"
Write-Info "Do not read or paste .env files."
Write-Info "Do not include tokens, credentials, auth URLs, API keys, or personal data."
Write-Info "Keep terminal output short when report files are available."

Write-Section "--- Clipboard helpers ---"
if (Test-Path -LiteralPath $copyLatest) {
    Write-Ok "Found: tools\copy_latest_report.ps1"
    Write-Host "  powershell -ExecutionPolicy Bypass -File tools\copy_latest_report.ps1"
} else {
    Write-WarnLine "Missing: tools\copy_latest_report.ps1"
}

if (Test-Path -LiteralPath $copyAny) {
    Write-Ok "Found: tools\copy_report_to_clipboard.ps1"
    Write-Host "  powershell -ExecutionPolicy Bypass -File tools\copy_report_to_clipboard.ps1 -Path $ReportPath"
} else {
    Write-WarnLine "Missing: tools\copy_report_to_clipboard.ps1"
}

Write-Section "--- Next action rule ---"
Write-Info "NEXT_ACTION.md must contain one explicit next action."
Write-Info "Any executor task requires a new exact human-approved prompt."
Write-Host ""
Write-Host "VERDICT: HANDOFF PROTOCOL PRINTED - READ-ONLY" -ForegroundColor Green
exit 0
