param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"

if (!(Test-Path -LiteralPath $Path)) {
    Write-Error "File not found: $Path"
    exit 1
}

$resolvedPath = (Resolve-Path -LiteralPath $Path).Path
$utf8 = New-Object System.Text.UTF8Encoding($false, $true)
$content = [System.IO.File]::ReadAllText($resolvedPath, $utf8)

if ([string]::IsNullOrWhiteSpace($content)) {
    Write-Error "File is empty: $Path"
    exit 1
}

Set-Clipboard -Value $content

Write-Host "Copied to clipboard:"
Write-Host "  $Path"
Write-Host ""
Write-Host "Characters copied: $($content.Length)"
Write-Host "Now paste into ChatGPT with Ctrl+V."
