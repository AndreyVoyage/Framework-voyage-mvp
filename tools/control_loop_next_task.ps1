#requires -Version 5.1
<#
.SYNOPSIS
    VOYAGE-CONTROL-LOOP-3 - read-only task spec lister.

.DESCRIPTION
    Inspects tracked control-loop task specs and prints the next manual step.
    This helper is read-only by default and has no live mode. It does not edit
    files, stage, commit, push, read .env, touch .voyage, invoke bridges, or
    execute tasks.
#>

[CmdletBinding()]
param(
    [string]$RepoPath = (Get-Location).Path,
    [string]$WorktreePath = ""
)

$ErrorActionPreference = "Continue"

function Write-Section { param([string]$Text) Write-Host ""; Write-Host $Text -ForegroundColor White }
function Write-Info { param([string]$Text) Write-Host "  [INFO] $Text" -ForegroundColor Gray }
function Write-Ok { param([string]$Text) Write-Host "  [OK]   $Text" -ForegroundColor Green }
function Write-StopLine { param([string]$Text) Write-Host "  [STOP] $Text" -ForegroundColor Yellow }

function Resolve-LocalPath {
    param([Parameter(Mandatory)][string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Resolve-Path -LiteralPath $Path).Path
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " VOYAGE CONTROL LOOP - NEXT TASK INSPECTION" -ForegroundColor Cyan
Write-Host " Phase: VOYAGE-CONTROL-LOOP-3   Mode: READ-ONLY" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$RepoPath = Resolve-LocalPath -Path $RepoPath
if ([string]::IsNullOrWhiteSpace($WorktreePath)) {
    $WorktreePath = $RepoPath
} else {
    $WorktreePath = Resolve-LocalPath -Path $WorktreePath
}

Write-Info "Repo path:     $RepoPath"
Write-Info "Worktree path: $WorktreePath"
Write-Info "No files will be modified."

$taskDir = Join-Path $RepoPath "docs\control-loop"
if (-not (Test-Path -LiteralPath $taskDir)) {
    Write-StopLine "Task directory not found: $taskDir"
    exit 1
}

Write-Section "--- Known control-loop task specs ---"
$taskFiles = Get-ChildItem -LiteralPath $taskDir -Filter "*.yaml" -File | Sort-Object Name

if ($taskFiles.Count -eq 0) {
    Write-StopLine "No task specs found under docs\control-loop."
    exit 1
}

$seenIds = @{}
$duplicates = @()
$pending = @()

foreach ($file in $taskFiles) {
    $content = Get-Content -LiteralPath $file.FullName
    $id = ""
    $title = ""
    $status = ""
    $track = ""

    foreach ($line in $content) {
        if ($line -match "^\s*id:\s*(.+?)\s*$") { $id = $Matches[1].Trim(" `"'") }
        if ($line -match "^\s*title:\s*(.+?)\s*$") { $title = $Matches[1].Trim(" `"'") }
        if ($line -match "^\s*status:\s*(.+?)\s*$") { $status = $Matches[1].Trim(" `"'") }
        if ($line -match "^\s*track:\s*(.+?)\s*$") { $track = $Matches[1].Trim(" `"'") }
    }

    if ([string]::IsNullOrWhiteSpace($id)) {
        Write-StopLine "$($file.Name): missing id"
        continue
    }

    if ($seenIds.ContainsKey($id)) {
        $duplicates += $id
    } else {
        $seenIds[$id] = $file.Name
    }

    if ($status -eq "pending") {
        $pending += [pscustomobject]@{ Id = $id; File = $file.Name; Title = $title; Track = $track }
    }

    Write-Host ("  {0,-8} {1,-10} {2,-30} {3}" -f $id, $status, $track, $file.Name)
}

if ($duplicates.Count -gt 0) {
    Write-Section "--- Recommendation ---"
    Write-StopLine "Duplicate task IDs found: $($duplicates -join ', ')"
    Write-StopLine "Human decision required before selecting the next task."
    exit 1
}

Write-Section "--- Recommendation ---"

$cl3 = @($pending | Where-Object { $_.Id -eq "VF-902" -or $_.Track -eq "VOYAGE-CONTROL-LOOP-3" })
if ($cl3.Count -gt 0) {
    Write-Ok "CONTROL-LOOP-3 task spec is present."
    Write-Info "Next manual step: run a diff audit for the CONTROL-LOOP-3 artifacts."
    Write-Info "Do not execute development tasks or invoke a bridge."
} else {
    Write-StopLine "CONTROL-LOOP-3 task spec not found."
    Write-StopLine "Human approval required before continuing."
    exit 1
}

Write-Section "--- Safety reminder ---"
Write-Info "Allowed now: inspect specs, write handoff reports after approved work."
Write-Info "Forbidden now: push, merge, deploy, .env, .voyage mutation, bridge invocation, task execution."
Write-Host ""
Write-Host "VERDICT: READ-ONLY INSPECTION COMPLETE" -ForegroundColor Green
exit 0
