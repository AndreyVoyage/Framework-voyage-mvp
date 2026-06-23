# Handoff Automation

This directory is used for local handoff between ChatGPT, Claude Code, Kimi Code, and VS Code.

Generated files in this directory are local-only and ignored by git:

- `LATEST_AGENT_REPORT.md` — latest full agent report for copying back to ChatGPT
- `NEXT_ACTION.md` — suggested next prompt/action
- `SESSION_EXPORT.md` — optional exported Claude/Kimi session text

## Standard agent rule

At the end of long audit/implementation/merge tasks, the agent should:

1. Write the full final report to `docs/handoff/LATEST_AGENT_REPORT.md`.
2. Write the next recommended action to `docs/handoff/NEXT_ACTION.md`.
3. Keep terminal output short.
4. Never store secrets, tokens, auth URLs, API keys, or personal data in handoff files.
5. Write generated handoff files as UTF-8.

## Copy latest report to clipboard

From PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File tools\copy_latest_report.ps1
```

Then paste into ChatGPT with `Ctrl+V`.

## Copy any report file to clipboard

```powershell
powershell -ExecutionPolicy Bypass -File tools\copy_report_to_clipboard.ps1 -Path docs\reports\REPORT_NAME.md
```

## Encoding

All handoff files must be written as UTF-8.

Claude Code / Kimi Code agents should write generated reports using UTF-8 and avoid legacy Windows encodings.

The clipboard scripts read files explicitly as UTF-8 to prevent mojibake in Russian text, for example `Ð¸`, `Ñ‡`, `âœ…`.

## Safety

Do not commit generated handoff files.

Tracked files in this directory should be documentation only.
