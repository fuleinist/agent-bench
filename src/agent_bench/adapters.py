"""Agent adapter interface for different coding agents."""

import subprocess
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .models import Task, TaskResult, TaskStatus


class BaseAdapter(ABC):
    """Base class for agent adapters."""

    name: str = "base"
    available: bool = False

    @abstractmethod
    def run_task(self, task: Task, cwd: Path) -> TaskResult:
        """Run a single task with the agent."""
        pass

    def is_available(self) -> bool:
        """Check if the agent is available."""
        return self.available

    def _check_command(self, cmd: str) -> bool:
        """Check if a command is available."""
        return shutil.which(cmd) is not None


class ClaudeCodeAdapter(BaseAdapter):
    """Adapter for Claude Code."""

    name = "claude-code"
    command = "claude"

    def __init__(self):
        self.available = self._check_command(self.command)

    def run_task(self, task: Task, cwd: Path) -> TaskResult:
        if not self.available:
            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.ERROR,
                error="Claude Code not available",
            )

        # Build the prompt
        prompt = f"Task: {task.name}\n\n{task.task_prompt}"

        try:
            result = subprocess.run(
                [self.command, "--print", prompt],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=task.timeout,
            )

            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.PASSED if result.returncode == 0 else TaskStatus.FAILED,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {task.timeout} seconds",
            )
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.ERROR,
                error=str(e),
            )


class GenericCommandAdapter(BaseAdapter):
    """Adapter for generic command-line agents."""

    name = "generic"
    available = True

    def __init__(self, command: str, name: str = "generic"):
        self.command = command
        self.name = name
        self.available = self._check_command(command) if command else True

    def run_task(self, task: Task, cwd: Path) -> TaskResult:
        if not self.command:
            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.ERROR,
                error="No command configured",
            )

        try:
            result = subprocess.run(
                self.command.split() + [task.task_prompt],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=task.timeout,
            )

            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.PASSED if result.returncode == 0 else TaskStatus.FAILED,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {task.timeout} seconds",
            )
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                agent=self.name,
                status=TaskStatus.ERROR,
                error=str(e),
            )


def load_adapters(config_path: str = "agents.yaml") -> list[BaseAdapter]:
    """Load adapters from configuration file."""
    import yaml

    adapters = []

    # Always add Claude Code adapter
    adapters.append(ClaudeCodeAdapter())

    # Add generic adapter as default
    adapters.append(GenericCommandAdapter("", "generic"))

    # Try to load custom config
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
                agents = config.get("agents", {})
                for agent_name, agent_config in agents.items():
                    if agent_config.get("available", False):
                        cmd = agent_config.get("command", "")
                        if cmd:
                            adapters.append(GenericCommandAdapter(cmd, agent_name))
        except Exception:
            pass  # Ignore config errors

    return adapters


def get_adapter(name: str, config_path: str = "agents.yaml") -> Optional[BaseAdapter]:
    """Get a specific adapter by name."""
    adapters = load_adapters(config_path)
    for adapter in adapters:
        if adapter.name == name:
            return adapter
    return None