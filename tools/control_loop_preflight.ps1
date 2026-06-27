#requires -Version 5.1
<#
.SYNOPSIS
    VOYAGE-CONTROL-LOOP-1 - read-only preflight for the overnight control loop.

.DESCRIPTION
    Checks whether the repository is in a safe state to LATER create a checkpoint /
    worktree runner (CONTROL-LOOP-2+). This script is strictly READ-ONLY.

    It DOES NOT, under any circumstances:
      * create a checkpoint tag
      * create a backup branch
      * create a git worktree
      * launch Claude
      * perform rollback / git reset / git clean
      * commit or push
      * modify .voyage runtime state
      * modify any source code
      * read .env or any secret file

    It only inspects state and prints a GO / NO-GO safety report.
    Exit code: 0 = GO, 1 = NO-GO, 2 = preflight could not run (e.g. not a git repo).

.PARAMETER RepoPath
    Path to the primary repository. Defaults to the current directory.

.PARAMETER MainBranch
    Name of the stable branch. Default: main.

.PARAMETER Remote
    Name of the remote to compare against. Default: origin.

.PARAMETER WorktreeSuffix
    Suffix for the future sibling worktree directory. Default: -auto-night.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\control_loop_preflight.ps1 -RepoPath .
#>

[CmdletBinding()]
param(
    [string]$RepoPath       = (Get-Location).Path,
    [string]$MainBranch     = "main",
    [string]$Remote         = "origin",
    [string]$WorktreeSuffix = "-auto-night"
)

# Read-only posture: never stop the world on a single failed probe, never mutate.
$ErrorActionPreference = "Continue"

# ----- result accumulators -------------------------------------------------
$checks   = New-Object System.Collections.Generic.List[object]
$blockers = New-Object System.Collections.Generic.List[string]

function Add-Check {
    param(
        [string]$Name,
        [ValidateSet("PASS", "WARN", "FAIL", "INFO")]
        [string]$Status,
        [string]$Detail,
        [switch]$Blocking
    )
    $checks.Add([pscustomobject]@{ Name = $Name; Status = $Status; Detail = $Detail })
    if ($Blocking -and $Status -eq "FAIL") { $blockers.Add($Name) }
}

# Run a git command read-only and capture stdout (trimmed). Never throws.
function Invoke-Git {
    param([Parameter(Mandatory)][string[]]$GitArgs)
    try {
        $out = & git -C $RepoPath @GitArgs 2>$null
        return @{ Ok = ($LASTEXITCODE -eq 0); Out = ($out | Out-String).Trim() }
    } catch {
        return @{ Ok = $false; Out = "" }
    }
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " VOYAGE CONTROL LOOP - PREFLIGHT (read-only)" -ForegroundColor Cyan
Write-Host " Phase: VOYAGE-CONTROL-LOOP-1   Mode: READ-ONLY PREFLIGHT + SPEC" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# ----- 0. git availability + repo sanity -----------------------------------
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Add-Check -Name "git available" -Status "FAIL" -Detail "git not found on PATH" -Blocking
    Write-Host "FAIL: git is not installed or not on PATH. Cannot continue." -ForegroundColor Red
    exit 2
}
Add-Check -Name "git available" -Status "PASS" -Detail $gitCmd.Source

$inside = Invoke-Git @("rev-parse", "--is-inside-work-tree")
if (-not $inside.Ok -or $inside.Out -ne "true") {
    Add-Check -Name "is git repo" -Status "FAIL" -Detail "$RepoPath is not a git work tree" -Blocking
    Write-Host "FAIL: $RepoPath is not a git repository." -ForegroundColor Red
    exit 2
}
Add-Check -Name "is git repo" -Status "PASS" -Detail $RepoPath

# Resolve to absolute path so Split-Path works correctly when "." is passed.
$RepoPath = (Resolve-Path -LiteralPath $RepoPath).Path

# ----- 1. repo path / branch / HEAD ----------------------------------------
$branch    = (Invoke-Git @("rev-parse", "--abbrev-ref", "HEAD")).Out
$headFull  = (Invoke-Git @("rev-parse", "HEAD")).Out
$headShort = (Invoke-Git @("rev-parse", "--short", "HEAD")).Out
$headSubj  = (Invoke-Git @("log", "-1", "--pretty=%s")).Out
Add-Check -Name "repo path" -Status "INFO" -Detail $RepoPath
Add-Check -Name "current branch" -Status "INFO" -Detail $branch
Add-Check -Name "HEAD" -Status "INFO" -Detail "$headShort  $headSubj"

if ($branch -ne $MainBranch) {
    Add-Check -Name "on main branch" -Status "WARN" -Detail "currently on '$branch', expected '$MainBranch' (checkpoint must be taken from '$MainBranch')"
} else {
    Add-Check -Name "on main branch" -Status "PASS" -Detail "on '$MainBranch'"
}

# ----- 2. git status clean -------------------------------------------------
$porcelain = Invoke-Git @("status", "--porcelain")
if ([string]::IsNullOrWhiteSpace($porcelain.Out)) {
    Add-Check -Name "working tree clean" -Status "PASS" -Detail "no staged/unstaged/untracked changes" -Blocking
} else {
    $lines = ($porcelain.Out -split "`n").Count
    Add-Check -Name "working tree clean" -Status "FAIL" -Detail "$lines changed/untracked path(s) present - commit or stash before a checkpoint run" -Blocking
}

# ----- 3. main synced with origin/main (read-only; ls-remote, no fetch) ----
$localMainSha = (Invoke-Git @("rev-parse", $MainBranch)).Out
$lsRemote     = Invoke-Git @("ls-remote", $Remote, "refs/heads/$MainBranch")
if (-not $lsRemote.Ok -or [string]::IsNullOrWhiteSpace($lsRemote.Out)) {
    Add-Check -Name "origin reachable" -Status "WARN" -Detail "could not read $Remote/$MainBranch via 'git ls-remote' (offline?) - sync UNVERIFIED"
} else {
    $remoteMainSha = ($lsRemote.Out -split "\s+")[0]
    if ($remoteMainSha -eq $localMainSha) {
        $shortSha = $localMainSha.Substring(0, [Math]::Min(7, $localMainSha.Length))
        Add-Check -Name "main synced with $Remote/$MainBranch" -Status "PASS" -Detail "local and remote at $shortSha" -Blocking
    } else {
        # Determine ahead/behind against the locally-known tracking ref WITHOUT fetching.
        $aheadBehind = Invoke-Git @("rev-list", "--left-right", "--count", "$MainBranch...$Remote/$MainBranch")
        $detail = "local=$($localMainSha.Substring(0,7)) remote=$($remoteMainSha.Substring(0,7))"
        if ($aheadBehind.Ok -and $aheadBehind.Out) {
            $parts = $aheadBehind.Out -split "\s+"
            $detail = "$detail (ahead $($parts[0]) / behind $($parts[1]) vs cached $Remote/$MainBranch; run 'git fetch' to refresh)"
        }
        Add-Check -Name "main synced with $Remote/$MainBranch" -Status "FAIL" -Detail $detail -Blocking
    }
}

# ----- 4. claude CLI present -----------------------------------------------
$claude = Get-Command claude -ErrorAction SilentlyContinue
if ($claude) {
    Add-Check -Name "claude CLI present" -Status "PASS" -Detail $claude.Source
} else {
    # Not blocking for Phase 1: preflight does not launch Claude. Future phases need it.
    Add-Check -Name "claude CLI present" -Status "WARN" -Detail "claude not found on PATH - required by CONTROL-LOOP-4, not by this phase"
}

# ----- 5. git worktree subcommand available --------------------------------
$wtList = Invoke-Git @("worktree", "list")
if ($wtList.Ok) {
    $wtCount = @($wtList.Out -split "`n" | Where-Object { $_ -ne "" }).Count
    Add-Check -Name "git worktree available" -Status "PASS" -Detail "$wtCount existing worktree(s)"
} else {
    Add-Check -Name "git worktree available" -Status "FAIL" -Detail "'git worktree' not supported by this git version" -Blocking
}

# ----- 6. safe location for the future sibling worktree --------------------
$parent       = Split-Path -Path $RepoPath -Parent
$repoLeaf     = Split-Path -Path $RepoPath -Leaf
$worktreePath = Join-Path $parent ("{0}{1}" -f $repoLeaf, $WorktreeSuffix)
if (Test-Path -LiteralPath $worktreePath) {
    Add-Check -Name "future worktree path free" -Status "FAIL" -Detail "$worktreePath already exists - must be absent before CONTROL-LOOP-2 creates it" -Blocking
} elseif (-not (Test-Path -LiteralPath $parent)) {
    Add-Check -Name "future worktree path free" -Status "FAIL" -Detail "parent '$parent' not found" -Blocking
} else {
    Add-Check -Name "future worktree path free" -Status "PASS" -Detail "available: $worktreePath"
}

# ----- 7. handoff directory ------------------------------------------------
$handoff = Join-Path $RepoPath "docs/handoff"
if (Test-Path -LiteralPath $handoff) {
    Add-Check -Name "docs/handoff exists" -Status "PASS" -Detail $handoff
} else {
    Add-Check -Name "docs/handoff exists" -Status "WARN" -Detail "missing - morning reports land here; CONTROL-LOOP-2+ should create it (preflight will not)"
}

# ----- print results table -------------------------------------------------
Write-Host ""
Write-Host "Checks" -ForegroundColor White
Write-Host "------" -ForegroundColor White
foreach ($c in $checks) {
    $color = switch ($c.Status) {
        "PASS"  { "Green" }
        "WARN"  { "Yellow" }
        "FAIL"  { "Red" }
        default { "Gray" }
    }
    Write-Host ("  [{0,-4}] {1,-32} {2}" -f $c.Status, $c.Name, $c.Detail) -ForegroundColor $color
}

# ----- 8. denylist commands (informational, static) ------------------------
Write-Host ""
Write-Host "Denylist - actions the future runner MUST block:" -ForegroundColor White
$denylist = @(
    "git push (any remote)",
    "git merge into $MainBranch",
    "git reset / git clean in the PRIMARY repo",
    "deploy / release publish",
    "docker compose up/down, docker build/run",
    "ssh to any host",
    "certbot / TLS / cert issuance",
    "read or write .env / secret files",
    "modify .voyage runtime (events.db, events.jsonl, tasks.db)",
    "delete files outside the worktree allowlist",
    "auto-accept risky Claude permission prompts",
    "network calls beyond 'git ls-remote' (read) for sync"
)
foreach ($item in $denylist) { Write-Host "  - $item" -ForegroundColor DarkYellow }

# ----- 9. automatable modes (informational, static) ------------------------
Write-Host ""
Write-Host "Modes that MAY be automated later (in the worktree only):" -ForegroundColor White
$modes = @(
    "READ_ONLY      - inspect repo, no side effects",
    "CODE_NO_COMMIT - edit in worktree, leave uncommitted",
    "TEST           - ruff + mypy + pytest",
    "DIFF_AUDIT     - git diff / diff --check / forbidden-touch check",
    "COMMIT         - nightly branch ONLY, after all gates pass"
)
foreach ($item in $modes) { Write-Host "  - $item" -ForegroundColor DarkCyan }

# ----- 10. stop conditions (informational, static) -------------------------
Write-Host ""
Write-Host "Stop conditions required before any checkpoint is created:" -ForegroundColor White
$stops = @(
    "preflight returns NO-GO",
    "any denylist action attempted",
    "2 consecutive task failures (default)",
    "disk/time budget exceeded",
    "a gate harness itself errors (ruff/mypy/pytest cannot run)",
    "PRIMARY repo working tree changes during the run"
)
foreach ($item in $stops) { Write-Host "  - $item" -ForegroundColor DarkGray }

# ----- verdict -------------------------------------------------------------
Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
if ($blockers.Count -eq 0) {
    Write-Host " VERDICT: GO - repo is ready for CONTROL-LOOP-2 (checkpoint/worktree)." -ForegroundColor Green
    Write-Host " (This script created nothing and changed nothing.)" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host (" VERDICT: NO-GO - blocking issue(s): " + ($blockers -join ', ')) -ForegroundColor Red
    Write-Host " Resolve the blockers above, then re-run this read-only preflight." -ForegroundColor Red
    Write-Host "==================================================================" -ForegroundColor Cyan
    exit 1
}
