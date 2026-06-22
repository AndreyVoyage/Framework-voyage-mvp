# Installation

This guide installs Voyage Framework from the repository for local development. Voyage v4.1 does not execute AI agents or call AI models, and installation requires no provider credentials.

Architecture and contributor rules are defined in [`docs/VOYAGE_V4_1_CONTRACT.md`](../VOYAGE_V4_1_CONTRACT.md), [`AGENTS.md`](../../AGENTS.md), and [`PHASE_WORKFLOW_POLICY.md`](PHASE_WORKFLOW_POLICY.md).

## Prerequisites

- Python 3.11 or newer;
- Git;
- a Python virtual environment, strongly recommended;
- PowerShell or Git Bash on Windows.

Check the tools first:

```bash
python --version
git --version
```

If `python` is not the intended interpreter on Linux or macOS, use `python3` consistently.

## Clone the repository

```bash
git clone https://github.com/AndreyVoyage/Framework-voyage-mvp.git
cd Framework-voyage-mvp
```

## Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

Git Bash, Linux, or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

PowerShell may block `Activate.ps1` under a local execution policy. Activation is optional: every command can instead call `.\.venv\Scripts\python.exe` directly.

## Install development dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows without activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Verify the installation

```bash
python -c "import voyage_framework; print('OK')"
voyage --help
```

The current CLI does not define a `--version` switch, so use `voyage --help` or:

```bash
python -m voyage_framework.cli --help
```

The help output may list legacy `run` or `graph` commands from historical modules. They are outside the Voyage v4.1 MVP core and must not be treated as current agent-runtime support.

If the `voyage` command is not found, confirm the virtual environment is active or use the module form above.

## Run tests

```bash
python -m pytest tests/unit -v --basetemp=.pytest-tmp/install-unit
```

Windows without activation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -v --basetemp=.pytest-tmp/install-unit
```

Use a unique `--basetemp` path for later runs if Windows leaves an ACL-protected directory behind.

## Run quality checks

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy voyage_framework
```

If Ruff cannot open pre-existing Windows temporary directories, keep the warning visible and narrow the check rather than changing `.gitignore`:

```bash
python -m ruff check voyage_framework tests
```

## Windows notes

- Git Bash gives consistent POSIX commands; PowerShell is equally valid when commands use PowerShell syntax.
- The virtual-environment Python is `.venv\Scripts\python.exe`.
- The pytest executable is `.venv\Scripts\pytest.exe`, though `python -m pytest` is less ambiguous.
- Prefer `--basetemp=.pytest-tmp/<run-name>` over the system `%TEMP%`.
- If cleanup fails with `Permission denied` or `Access is denied`, report the ACL condition honestly. Do not hide it with product changes.

## Troubleshooting

### Import fails

Confirm the current directory is the repository root and reinstall with the same interpreter used to run the command:

```bash
python -m pip install -e ".[dev]"
python -c "import voyage_framework; print(voyage_framework.__file__)"
```

### CLI command fails to resolve

Use:

```bash
python -m voyage_framework.cli --help
```

Then verify that the editable installation completed without errors.

### Tests report temp-directory ACL errors

Choose a new explicit base directory:

```bash
python -m pytest tests/unit -v --basetemp=.pytest-tmp/install-unit-2
```

Do not change project code or `.gitignore` to conceal an environmental ACL warning.
