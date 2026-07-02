param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Module,

    [Parameter(ValueFromRemainingArguments = $true, Position = 1)]
    [string[]]$ModuleArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path

$candidates = New-Object System.Collections.Generic.List[string]

if ($env:VIRTUAL_ENV) {
    $candidates.Add((Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"))
}

$candidates.Add((Join-Path $repoRoot ".venv\Scripts\python.exe"))

try {
    $commonDir = (& git -C $repoRoot rev-parse --git-common-dir).Trim()

    if ($commonDir) {
        if (-not [System.IO.Path]::IsPathRooted($commonDir)) {
            $commonDir = Join-Path $repoRoot $commonDir
        }

        $commonDir = (Resolve-Path $commonDir).Path

        if ((Split-Path $commonDir -Leaf) -eq ".git") {
            $primaryRoot = Split-Path $commonDir -Parent
        }
        else {
            $primaryRoot = $commonDir
        }

        $candidates.Add((Join-Path $primaryRoot ".venv\Scripts\python.exe"))
    }
}
catch {
    # Git common-dir lookup is a fallback only. Continue with other candidates.
}

$python = $null

foreach ($candidate in ($candidates | Select-Object -Unique)) {
    if (Test-Path -LiteralPath $candidate) {
        $python = $candidate
        break
    }
}

if (-not $python) {
    Write-Error "Could not find project Python. Checked: $($candidates -join '; ')"
    exit 127
}

& $python -m $Module @ModuleArgs
exit $LASTEXITCODE
