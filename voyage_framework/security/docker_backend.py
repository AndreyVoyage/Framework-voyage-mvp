"""DockerBackend — sandbox backend через docker run --rm."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

from voyage_framework.core.models import ToolResult
from voyage_framework.security.sandbox import SandboxBackend


class DockerBackend(SandboxBackend):
    """Backend для SecureExecutor, запускающий команды внутри Docker-контейнера."""

    def __init__(
        self,
        project_root: Path | str = ".",
        image: str = "python:3.11-slim",
        network_mode: str = "none",
        timeout_seconds: int = 60,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.image = image
        self.network_mode = network_mode
        self.timeout_seconds = timeout_seconds
        self._container_root = "/workspace"

    def _build_docker_command(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> list[str]:
        """Собрать команду docker run для выполнения command внутри контейнера."""
        host_cwd = Path(cwd).resolve() if cwd else self.project_root
        try:
            rel = host_cwd.relative_to(self.project_root)
            if rel == Path("."):
                container_cwd = self._container_root
            else:
                container_cwd = f"{self._container_root}/{rel.as_posix()}".rstrip("/")
        except ValueError:
            container_cwd = self._container_root

        docker_cmd: list[str] = [
            "docker",
            "run",
            "--rm",
            f"--volume={self.project_root.as_posix()}:{self._container_root}",
            f"--workdir={container_cwd}",
        ]

        if self.network_mode:
            docker_cmd.append(f"--network={self.network_mode}")

        if sys.platform != "win32":
            try:
                uid = os.getuid()
                gid = os.getgid()
                docker_cmd.append(f"--user={uid}:{gid}")
            except (AttributeError, OSError):
                pass

        docker_cmd.append(self.image)
        docker_cmd.extend(command)
        return docker_cmd

    async def _create_subprocess(self, docker_cmd: list[str]) -> Any:
        """Обертка для subprocess, чтобы тесты могли замокать точку запуска."""
        return await asyncio.create_subprocess_exec(
            *docker_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def execute(
        self,
        command: list[str],
        cwd: Path | None = None,
    ) -> ToolResult:
        """Выполнить команду внутри Docker-контейнера."""
        if not command:
            return ToolResult(success=True, stdout="Empty command")

        docker_cmd = self._build_docker_command(command, cwd)
        start = time.time()

        try:
            proc = await self._create_subprocess(docker_cmd)
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError:
            return ToolResult(
                success=False,
                stderr="Docker not installed",
                exit_code=127,
                execution_time_ms=round((time.time() - start) * 1000, 2),
            )
        except TimeoutError:
            return ToolResult(
                success=False,
                stderr=f"Execution timeout after {self.timeout_seconds}s",
                exit_code=124,
                execution_time_ms=round((time.time() - start) * 1000, 2),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                stderr=str(e),
                exit_code=1,
                execution_time_ms=round((time.time() - start) * 1000, 2),
            )

        elapsed = (time.time() - start) * 1000
        return ToolResult(
            success=proc.returncode == 0,
            stdout=stdout_b.decode("utf-8", errors="replace"),
            stderr=stderr_b.decode("utf-8", errors="replace"),
            exit_code=proc.returncode or 0,
            execution_time_ms=round(elapsed, 2),
        )
