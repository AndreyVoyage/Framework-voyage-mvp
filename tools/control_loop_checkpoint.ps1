#requires -Version 5.1
<#
.SYNOPSIS
    VOYAGE-CONTROL-LOOP-2 - guarded checkpoint/worktree creation (dry-run by default).

.DESCRIPTION
    Creates a three-level checkpoint (tag + backup branch + sibling worktree) so the
    overnight loop has a safe, isolated surface to work in. By default this script
    runs in DRY-RUN mode: it validates all preconditions and prints the exact
    commands it would run, but performs zero mutations.

    Pass -Execute to create the real artifacts. DO NOT pass -Execute unless you have
    read the dry-run output and confirmed every line is safe.

    This script DOES NOT, under any circumstances:
      * push to any remote
      * merge into main
      * reset or clean the PRIMARY repo
      * deploy, docker, ssh, certbot
      * read .env or any secret file
      * modify .voyage runtime state (events.db, events.jsonl, tasks.db)
      * modify any source code or test
      * launch Claude or run tasks
      * auto-accept risky Claude permission prompts

    Exit codes:
      0 = DRY-RUN OK  (all preconditions met; print-only; no mutations)
      0 = LIVE OK     (checkpoint created successfully)
      1 = precondition failed or creation failed
      2 = cannot run  (preflight not found, not a git repo, etc.)

.PARAMETER RepoPath
    Path to the primary repository. Defaults to the current directory.

.PARAMETER WorktreePath
    Explicit path for the sibling worktree.
    Default: <repo-parent>/<repo-leaf>-auto-night.

.PARAMETER Timestamp
    Override the YYYYMMDD-HHmm timestamp used for tag/branch/worktree names.
    Default: computed at script start from Get-Date.

.PARAMETER Execute
    Switch: if present, perform the real mutations (create tag, branch, worktree).
    Omit this switch for dry-run (the safe default).

.EXAMPLE
    # Dry-run (default - safe to run any time):
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\control_loop_checkpoint.ps1 -RepoPath .

.EXAMPLE
    # Live run (creates real tag + branch + worktree; requires human decision):
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\control_loop_checkpoint.ps1 -RepoPath . -Execute
#>

[CmdletBinding()]
param(
    [string]$RepoPath     = (Get-Location).Path,
    [string]$WorktreePath = "",
    [string]$Timestamp    = "",
    [switch]$Execute
)

$ErrorActionPreference = "Continue"

# ---- helpers -----------------------------------------------------------------

function Write-Step { param([string]$Msg) Write-Host "  $Msg" -ForegroundColor Cyan }
function Write-Ok   { param([string]$Msg) Write-Host "  [OK]   $Msg" -ForegroundColor Green }
function Write-Fail { param([string]$Msg) Write-Host "  [FAIL] $Msg" -ForegroundColor Red }
function Write-Info { param([string]$Msg) Write-Host "  [INFO] $Msg" -ForegroundColor Gray }
function Write-Cmd  { param([string]$Cmd) Write-Host "    > $Cmd" -ForegroundColor DarkYellow }

# Read-only git probe; never mutates; never throws.
function Invoke-GitR {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    try {
        $out = & git -C $RepoPath @GitArgs 2>$null
        return @{ Ok = ($LASTEXITCODE -eq 0); Out = ($out | Out-String).Trim() }
    } catch {
        return @{ Ok = $false; Out = "" }
    }
}

# ---- banner ------------------------------------------------------------------

$modeLabel = if ($Execute) { "LIVE (creating real artifacts)" } else { "DRY-RUN (read-only simulation)" }
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " VOYAGE CONTROL LOOP - CHECKPOINT / WORKTREE CREATION" -ForegroundColor Cyan
Write-Host " Phase: VOYAGE-CONTROL-LOOP-2   Mode: $modeLabel" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# ---- 0. locate Phase 1 preflight -------------------------------------------

$scriptDir       = Split-Path -Parent $MyInvocation.MyCommand.Definition
$preflightScript = Join-Path $scriptDir "control_loop_preflight.ps1"

if (-not (Test-Path -LiteralPath $preflightScript)) {
    Write-Fail "control_loop_preflight.ps1 not found at: $preflightScript"
    Write-Host " Cannot continue without the Phase 1 preflight." -ForegroundColor Red
    exit 2
}

# ---- 1. re-run Phase 1 preflight as a hard gate ----------------------------

Write-Host ""
Write-Host "--- Phase 1 preflight gate ---" -ForegroundColor White
Write-Step "Running: powershell -NoProfile -ExecutionPolicy Bypass -File `"$preflightScript`" -RepoPath `"$RepoPath`""
Write-Host ""

powershell -NoProfile -ExecutionPolicy Bypass -File $preflightScript -RepoPath $RepoPath
$preflightExit = $LASTEXITCODE

Write-Host ""
if ($preflightExit -ne 0) {
    Write-Fail "Preflight returned exit $preflightExit (not GO). Aborting."
    Write-Host " Resolve all preflight blockers, then re-run this script." -ForegroundColor Red
    exit 1
}
Write-Ok "Preflight: GO (exit 0)"

# ---- 2. resolve repo path to absolute ---------------------------------------

if (-not [System.IO.Path]::IsPathRooted($RepoPath)) {
    $RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path
}
Write-Info "Repo path: $RepoPath"

# ---- 3. compute timestamp and artifact names --------------------------------

if ([string]::IsNullOrWhiteSpace($Timestamp)) {
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmm"
}

$checkpointTag    = "voyage-checkpoint-$Timestamp"
$checkpointBranch = "checkpoint/$Timestamp"
# Nightly branch uses date only (one branch per calendar day).
$nightlyBranch    = "auto/nightly-$($Timestamp.Substring(0, 8))"

if ([string]::IsNullOrWhiteSpace($WorktreePath)) {
    $parent       = Split-Path -Path $RepoPath -Parent
    $leaf         = Split-Path -Path $RepoPath -Leaf
    $WorktreePath = Join-Path $parent "$leaf-auto-night"
}

Write-Info "Timestamp:         $Timestamp"
Write-Info "Checkpoint tag:    $checkpointTag"
Write-Info "Checkpoint branch: $checkpointBranch"
Write-Info "Nightly branch:    $nightlyBranch"
Write-Info "Worktree path:     $WorktreePath"

# ---- 4. precondition checks (Phase 2-specific) ------------------------------

Write-Host ""
Write-Host "--- Precondition checks ---" -ForegroundColor White

$preconditionsFailed = $false

# 4a. on main branch
$branch = (Invoke-GitR @("rev-parse", "--abbrev-ref", "HEAD")).Out
if ($branch -ne "main") {
    Write-Fail "Not on 'main' branch (currently on '$branch'). Checkpoint must be taken from 'main'."
    $preconditionsFailed = $true
} else {
    Write-Ok "On branch: main"
}

# 4b. HEAD matches origin/main (re-verified independently of preflight)
$localSha = (Invoke-GitR @("rev-parse", "HEAD")).Out
$lsRemote = Invoke-GitR @("ls-remote", "origin", "refs/heads/main")
if (-not $lsRemote.Ok -or [string]::IsNullOrWhiteSpace($lsRemote.Out)) {
    Write-Fail "Cannot reach origin to verify HEAD sync."
    $preconditionsFailed = $true
} else {
    $remoteSha = ($lsRemote.Out -split "\s+")[0]
    if ($localSha -ne $remoteSha) {
        Write-Fail "HEAD ($($localSha.Substring(0,7))) differs from origin/main ($($remoteSha.Substring(0,7))). Sync before creating a checkpoint."
        $preconditionsFailed = $true
    } else {
        Write-Ok "HEAD synced with origin/main at $($localSha.Substring(0,7))"
    }
}

# 4c. working tree clean (belt-and-suspenders; preflight already checks this)
$porcelain = Invoke-GitR @("status", "--porcelain")
if (-not [string]::IsNullOrWhiteSpace($porcelain.Out)) {
    Write-Fail "Working tree is not clean. Commit or stash changes before creating a checkpoint."
    $preconditionsFailed = $true
} else {
    Write-Ok "Working tree clean"
}

# 4d. checkpoint tag must not already exist
$tagCheck = Invoke-GitR @("tag", "--list", $checkpointTag)
if (-not [string]::IsNullOrWhiteSpace($tagCheck.Out)) {
    Write-Fail "Checkpoint tag '$checkpointTag' already exists. Use a different -Timestamp."
    $preconditionsFailed = $true
} else {
    Write-Ok "Checkpoint tag '$checkpointTag' is free"
}

# 4e. checkpoint branch must not already exist
$branchCheck = Invoke-GitR @("branch", "--list", $checkpointBranch)
if (-not [string]::IsNullOrWhiteSpace($branchCheck.Out)) {
    Write-Fail "Checkpoint branch '$checkpointBranch' already exists."
    $preconditionsFailed = $true
} else {
    Write-Ok "Checkpoint branch '$checkpointBranch' is free"
}

# 4f. nightly branch must not already exist
$nightlyCheck = Invoke-GitR @("branch", "--list", $nightlyBranch)
if (-not [string]::IsNullOrWhiteSpace($nightlyCheck.Out)) {
    Write-Fail "Nightly branch '$nightlyBranch' already exists."
    $preconditionsFailed = $true
} else {
    Write-Ok "Nightly branch '$nightlyBranch' is free"
}

# 4g. worktree target path must not exist
if (Test-Path -LiteralPath $WorktreePath) {
    Write-Fail "Worktree path '$WorktreePath' already exists. Remove it or use a different path."
    $preconditionsFailed = $true
} else {
    Write-Ok "Worktree path '$WorktreePath' is free"
}

# 4h. worktree parent directory must exist
$worktreeParent = Split-Path -Path $WorktreePath -Parent
if (-not (Test-Path -LiteralPath $worktreeParent)) {
    Write-Fail "Worktree parent '$worktreeParent' does not exist."
    $preconditionsFailed = $true
} else {
    Write-Ok "Worktree parent '$worktreeParent' exists"
}

if ($preconditionsFailed) {
    Write-Host ""
    Write-Fail "One or more preconditions failed. Aborting before any mutation."
    exit 1
}

# ---- 5. dry-run: print execution plan ---------------------------------------

Write-Host ""
Write-Host "--- Execution plan ---" -ForegroundColor White

if (-not $Execute) {
    Write-Host ""
    Write-Host " MODE: DRY-RUN - no mutations will be performed." -ForegroundColor Yellow
    Write-Host " All preconditions passed. The following commands would run with -Execute:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host " Step 1 - Create checkpoint tag (immutable return point):" -ForegroundColor White
    Write-Cmd  "git -C `"$RepoPath`" tag `"$checkpointTag`""
    Write-Cmd  "git -C `"$RepoPath`" tag --list `"$checkpointTag`"   # verify"
    Write-Host ""
    Write-Host " Step 2 - Create backup branch (named safety copy):" -ForegroundColor White
    Write-Cmd  "git -C `"$RepoPath`" branch `"$checkpointBranch`""
    Write-Cmd  "git -C `"$RepoPath`" branch --list `"$checkpointBranch`"   # verify"
    Write-Host ""
    Write-Host " Step 3 - Create sibling worktree on nightly branch:" -ForegroundColor White
    Write-Cmd  "git -C `"$RepoPath`" worktree add -b `"$nightlyBranch`" `"$WorktreePath`" HEAD"
    Write-Cmd  "git -C `"$RepoPath`" worktree list   # verify"
    Write-Host ""
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host " VERDICT: DRY-RUN COMPLETE - all preconditions met." -ForegroundColor Green
    Write-Host " Re-run with -Execute to perform the real checkpoint creation." -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Cyan
    exit 0
}

# ---- 6. live execution: create checkpoint artifacts -------------------------

Write-Host ""
Write-Host " MODE: LIVE - creating real checkpoint artifacts." -ForegroundColor Red
Write-Host " Primary repo working tree: READ-ONLY for this script." -ForegroundColor Red
Write-Host " Mutations: additive only (tag + branch + worktree)." -ForegroundColor Red
Write-Host ""

$liveFailed = $false

# Step 1: checkpoint tag
Write-Step "Step 1 - Creating checkpoint tag: $checkpointTag"
& git -C $RepoPath tag $checkpointTag
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git tag returned non-zero exit. Tag '$checkpointTag' may not have been created."
    $liveFailed = $true
} else {
    $verify = (Invoke-GitR @("tag", "--list", $checkpointTag)).Out
    if ($verify -eq $checkpointTag) {
        Write-Ok "Tag '$checkpointTag' created and verified."
    } else {
        Write-Fail "Tag '$checkpointTag' not found after creation."
        $liveFailed = $true
    }
}

if ($liveFailed) {
    Write-Host ""
    Write-Fail "Step 1 failed. Aborting before further mutations."
    Write-Host " Partial state: no branch or worktree was created." -ForegroundColor Yellow
    Write-Host " Inspect with: git tag --list voyage-checkpoint-*" -ForegroundColor Yellow
    exit 1
}

# Step 2: backup branch
Write-Step "Step 2 - Creating backup branch: $checkpointBranch"
& git -C $RepoPath branch $checkpointBranch
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git branch returned non-zero exit. Branch '$checkpointBranch' may not have been created."
    $liveFailed = $true
} else {
    $verify = (Invoke-GitR @("branch", "--list", $checkpointBranch)).Out
    if ($verify -match [regex]::Escape($checkpointBranch)) {
        Write-Ok "Branch '$checkpointBranch' created and verified."
    } else {
        Write-Fail "Branch '$checkpointBranch' not found after creation."
        $liveFailed = $true
    }
}

if ($liveFailed) {
    Write-Host ""
    Write-Fail "Step 2 failed. Aborting before worktree creation."
    Write-Host " Partial state:" -ForegroundColor Yellow
    Write-Host "   Tag '$checkpointTag' EXISTS (do not delete automatically)." -ForegroundColor Yellow
    Write-Host "   Branch '$checkpointBranch' may be partial - inspect: git branch --list checkpoint/*" -ForegroundColor Yellow
    exit 1
}

# Step 3: sibling worktree on nightly branch
Write-Step "Step 3 - Creating sibling worktree at: $WorktreePath (branch: $nightlyBranch)"
& git -C $RepoPath worktree add -b $nightlyBranch $WorktreePath HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Fail "git worktree add returned non-zero exit."
    $liveFailed = $true
} else {
    if (Test-Path -LiteralPath $WorktreePath) {
        Write-Ok "Worktree created and verified at '$WorktreePath' (branch: $nightlyBranch)."
    } else {
        Write-Fail "Worktree path '$WorktreePath' not found after creation."
        $liveFailed = $true
    }
}

if ($liveFailed) {
    Write-Host ""
    Write-Fail "Step 3 failed."
    Write-Host " Partial state:" -ForegroundColor Yellow
    Write-Host "   Tag '$checkpointTag' EXISTS." -ForegroundColor Yellow
    Write-Host "   Branch '$checkpointBranch' EXISTS." -ForegroundColor Yellow
    Write-Host "   Worktree may be partial - inspect: git worktree list" -ForegroundColor Yellow
    exit 1
}

# ---- 7. live success --------------------------------------------------------

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " VERDICT: CHECKPOINT CREATED SUCCESSFULLY." -ForegroundColor Green
Write-Host "   Tag:      $checkpointTag" -ForegroundColor Green
Write-Host "   Branch:   $checkpointBranch" -ForegroundColor Green
Write-Host "   Worktree: $WorktreePath" -ForegroundColor Green
Write-Host "   Branch:   $nightlyBranch" -ForegroundColor Green
Write-Host " (Primary repo working tree unchanged.)" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
exit 0
