"""Bounded fixed-command local Git reader for MCP-READ-01."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from voyage_framework.mcp_read.config import Limits
from voyage_framework.mcp_read.confinement import classify_sensitive_filename

GIT_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("rev-parse", "--show-toplevel"),
    ("branch", "--show-current"),
    ("rev-parse", "HEAD"),
    ("rev-parse", "--verify", "--quiet", "refs/remotes/origin/main"),
    ("status", "--porcelain=v1", "-z", "--untracked-files=all"),
)
_PREFIX = (
    "git",
    "--no-optional-locks",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "color.ui=false",
    "-c",
    "core.quotepath=false",
    "-c",
    "core.pager=cat",
)
_REMOVE_ENV = {
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_PREFIX",
    "GIT_SUPER_PREFIX",
    "GIT_QUARANTINE_PATH",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
}


class GitReadError(Exception):
    """Safe failure from the bounded Git process boundary."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class _CommandResult:
    returncode: int
    stdout: bytes
    stderr: bytes


def _git_env() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in _REMOVE_ENV
        and not key.startswith("GIT_CONFIG_KEY_")
        and not key.startswith("GIT_CONFIG_VALUE_")
    }
    env.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GCM_INTERACTIVE": "Never",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_EXTERNAL_DIFF": "",
            "GIT_ASKPASS": "",
            "SSH_ASKPASS": "",
            "GIT_SSH": "",
            "GIT_SSH_COMMAND": "",
            "LESS": "",
        }
    )
    return env


def _run_fixed(root: Path, command: tuple[str, ...], limits: Limits) -> _CommandResult:
    if command not in GIT_COMMANDS:
        raise GitReadError("git_command_denied")
    try:
        process = subprocess.Popen(
            [*_PREFIX, *command],
            cwd=root,
            env=_git_env(),
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, ValueError) as exc:
        raise GitReadError("git_spawn_error") from exc
    if process.stdout is None or process.stderr is None:
        process.kill()
        process.wait()
        raise GitReadError("git_pipe_error")

    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    lock = threading.Lock()
    overflow = threading.Event()
    stop = threading.Event()

    def read_pipe(name: str, pipe: BinaryIO) -> None:
        while not stop.is_set():
            try:
                chunk = pipe.read(8192)
            except (OSError, ValueError):
                return
            if not chunk:
                return
            with lock:
                used = len(buffers["stdout"]) + len(buffers["stderr"])
                remaining = limits.max_git_output_bytes - used
                if len(chunk) > remaining:
                    if remaining > 0:
                        buffers[name].extend(chunk[:remaining])
                    overflow.set()
                    return
                buffers[name].extend(chunk)

    threads = [
        threading.Thread(target=read_pipe, args=("stdout", process.stdout), daemon=False),
        threading.Thread(target=read_pipe, args=("stderr", process.stderr), daemon=False),
    ]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + limits.git_timeout_seconds
    failure: str | None = None
    while process.poll() is None:
        if overflow.is_set():
            failure = "git_output_limit_exceeded"
            break
        if time.monotonic() >= deadline:
            failure = "git_timeout"
            break
        time.sleep(0.01)
    if failure is not None:
        stop.set()
        with suppress(OSError):
            process.terminate()
        try:
            process.wait(timeout=0.25)
        except subprocess.TimeoutExpired:
            with suppress(OSError):
                process.kill()
            process.wait()
        process.stdout.close()
        process.stderr.close()
    else:
        process.wait()
    for thread in threads:
        thread.join(timeout=1.0)
        if thread.is_alive():
            raise GitReadError("git_reader_cleanup_failed")
    if failure is None and overflow.is_set():
        failure = "git_output_limit_exceeded"
    stop.set()
    if not process.stdout.closed:
        process.stdout.close()
    if not process.stderr.closed:
        process.stderr.close()
    if failure is not None:
        raise GitReadError(failure)
    return _CommandResult(process.returncode, bytes(buffers["stdout"]), bytes(buffers["stderr"]))


def _text(result: _CommandResult, *, allow_missing: bool = False) -> str | None:
    if result.returncode != 0:
        if allow_missing and result.returncode == 1:
            return None
        raise GitReadError("git_command_failed")
    try:
        return result.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise GitReadError("git_output_decode_error") from exc


def git_read_state(project_root: Path, limits: Limits | None = None) -> dict[str, object]:
    effective = limits or Limits()
    try:
        root = Path(project_root).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GitReadError("project_root_unavailable") from exc
    if not root.is_dir():
        raise GitReadError("project_root_invalid")
    results = [_run_fixed(root, command, effective) for command in GIT_COMMANDS]
    top = _text(results[0])
    if top is None or os.path.normcase(str(Path(top).resolve())) != os.path.normcase(str(root)):
        raise GitReadError("project_root_mismatch")
    branch = _text(results[1]) or None
    head = _text(results[2])
    origin = _text(results[3], allow_missing=True)
    status = _parse_status(results[4].stdout)
    warnings: list[str] = []
    if branch is None:
        warnings.append("HEAD is detached")
    if origin is None:
        warnings.append("local origin/main tracking ref not found")
    if status["untracked_files"]:
        warnings.append("untracked files exist")
    all_paths = sorted(set(status["changed_files"]))
    sensitive = [
        {"path": path, "classification": "potentially_sensitive"}
        for path in all_paths
        if classify_sensitive_filename(path) is not None
    ]
    return {
        "repo_path": str(root),
        "local_branch": branch,
        "local_head": head,
        "local_origin_main_ref": origin,
        "local_head_matches_origin_ref": head == origin if head and origin else None,
        "worktree_clean": not status["records"],
        "changed_files": status["changed_files"],
        "staged_files": status["staged_files"],
        "untracked_files": status["untracked_files"],
        "git_status_short": status["records"],
        "sensitive_files": sensitive,
        "file_count": {
            "changed": len(status["changed_files"]),
            "staged": len(status["staged_files"]),
            "untracked": len(status["untracked_files"]),
        },
        "remote_verified": False,
        "remote_checked_at": None,
        "remote_verification_method": "none",
        "warnings": warnings,
        "errors": [],
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }


def git_read_report_context(project_root: Path, limits: Limits | None = None) -> dict[str, object]:
    state = git_read_state(project_root, limits)
    keys = (
        "repo_path",
        "local_branch",
        "local_head",
        "local_origin_main_ref",
        "worktree_clean",
        "changed_files",
        "staged_files",
        "untracked_files",
        "remote_verified",
        "warnings",
        "errors",
    )
    return {key: state[key] for key in keys}


def _parse_status(raw: bytes) -> dict[str, list[str]]:
    try:
        parts = raw.decode("utf-8", errors="strict").split("\0")
    except UnicodeDecodeError as exc:
        raise GitReadError("git_output_decode_error") from exc
    records: list[str] = []
    changed: set[str] = set()
    staged: set[str] = set()
    untracked: set[str] = set()
    index = 0
    while index < len(parts) and parts[index]:
        record = parts[index]
        index += 1
        if len(record) < 4 or record[2] != " ":
            raise GitReadError("git_status_invalid")
        code, path = record[:2], record[3:]
        if "R" in code or "C" in code:
            if index >= len(parts) or not parts[index]:
                raise GitReadError("git_status_invalid")
            index += 1  # original path; destination is the first path in -z form
        records.append(record)
        changed.add(path)
        if code == "??":
            untracked.add(path)
        elif code[0] != " ":
            staged.add(path)
    return {
        "records": records,
        "changed_files": sorted(changed),
        "staged_files": sorted(staged),
        "untracked_files": sorted(untracked),
    }
