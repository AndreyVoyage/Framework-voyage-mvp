"""Unit tests for DockerBackend."""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, patch

import pytest

from voyage_framework.security.docker_backend import DockerBackend


class TestDockerBackend:
    def test_docker_backend_init_defaults(self):
        backend = DockerBackend(project_root=".")
        assert backend.image == "python:3.11-slim"
        assert backend.network_mode == "none"
        assert backend.timeout_seconds == 60
        assert backend._container_root == "/workspace"

    def test_docker_backend_custom_params(self):
        backend = DockerBackend(
            project_root=".",
            image="python:3.12-alpine",
            network_mode="host",
            timeout_seconds=30,
        )
        assert backend.image == "python:3.12-alpine"
        assert backend.network_mode == "host"
        assert backend.timeout_seconds == 30

    def test_docker_backend_command_building(self, tmp_path):
        backend = DockerBackend(project_root=tmp_path)
        cmd = backend._build_docker_command(["python", "-c", "print(1)"], cwd=tmp_path)

        assert cmd[0] == "docker"
        assert cmd[1] == "run"
        assert "--rm" in cmd
        assert f"--volume={tmp_path.as_posix()}:/workspace" in cmd
        assert "--workdir=/workspace" in cmd
        assert "--network=none" in cmd
        assert "python:3.11-slim" in cmd
        assert cmd[-3:] == ["python", "-c", "print(1)"]

        if sys.platform != "win32":
            assert any(arg.startswith("--user=") for arg in cmd)
        else:
            assert not any(arg.startswith("--user=") for arg in cmd)

    def test_docker_backend_command_with_subdirectory(self, tmp_path):
        subdir = tmp_path / "sub"
        subdir.mkdir()
        backend = DockerBackend(project_root=tmp_path)
        cmd = backend._build_docker_command(["ls"], cwd=subdir)

        assert "--workdir=/workspace/sub" in cmd

    @pytest.mark.asyncio
    async def test_docker_backend_success(self, tmp_path):
        backend = DockerBackend(project_root=tmp_path)
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"hello\n", b"")

        with patch.object(
            backend,
            "_create_subprocess",
            return_value=mock_proc,
        ) as mock_create:
            result = await backend.execute(["echo", "hello"], cwd=tmp_path)

        assert result.success is True
        assert result.exit_code == 0
        assert "hello" in result.stdout
        assert result.execution_time_ms is not None

        docker_cmd = mock_create.call_args[0][0]
        assert docker_cmd[0] == "docker"
        assert "--rm" in docker_cmd

    @pytest.mark.asyncio
    async def test_docker_backend_not_installed(self, tmp_path):
        backend = DockerBackend(project_root=tmp_path)

        with patch.object(
            backend,
            "_create_subprocess",
            side_effect=FileNotFoundError(),
        ):
            result = await backend.execute(["echo", "hello"], cwd=tmp_path)

        assert result.success is False
        assert result.exit_code == 127
        assert "Docker not installed" in result.stderr

    @pytest.mark.asyncio
    async def test_docker_backend_timeout(self, tmp_path):
        backend = DockerBackend(project_root=tmp_path, timeout_seconds=1)
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(
            side_effect=TimeoutError(),
        )

        with patch.object(
            backend,
            "_create_subprocess",
            return_value=mock_proc,
        ):
            result = await backend.execute(["sleep", "10"], cwd=tmp_path)

        assert result.success is False
        assert result.exit_code == 124
        assert "Execution timeout after 1s" in result.stderr

    @pytest.mark.asyncio
    async def test_docker_backend_empty_command(self, tmp_path):
        backend = DockerBackend(project_root=tmp_path)
        result = await backend.execute([], cwd=tmp_path)
        assert result.success is True
        assert result.stdout == "Empty command"

    @pytest.mark.asyncio
    async def test_docker_backend_error_exit_code(self, tmp_path):
        backend = DockerBackend(project_root=tmp_path)
        mock_proc = AsyncMock()
        mock_proc.returncode = 42
        mock_proc.communicate.return_value = (b"", b"something failed")

        with patch.object(
            backend,
            "_create_subprocess",
            return_value=mock_proc,
        ):
            result = await backend.execute(["false"], cwd=tmp_path)

        assert result.success is False
        assert result.exit_code == 42
        assert "something failed" in result.stderr
