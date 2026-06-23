$ErrorActionPreference = "Stop"

$Path = "docs\handoff\LATEST_AGENT_REPORT.md"

if (!(Test-Path -LiteralPath $Path)) {
    Write-Error "File not found: $Path"
    Write-Host ""
    Write-Host "Ask Claude Code or Kimi Code to write the full final report to:"
    Write-Host "  $Path"
    exit 1
}

$content = Get-Content -LiteralPath $Path -Raw

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
