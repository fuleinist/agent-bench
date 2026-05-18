"""Data models for agent-bench."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import yaml


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TaskStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class Task:
    id: str
    name: str
    description: str
    setup: str
    task_prompt: str
    test_command: str
    expected_outputs: list[str]
    timeout: int = 60
    difficulty: str = "easy"
    category: str = "general"

    @classmethod
    def from_yaml(cls, path: str) -> "Task":
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            setup=data.get("setup", ""),
            task_prompt=data["task_prompt"],
            test_command=data["test_command"],
            expected_outputs=data.get("expected_outputs", []),
            timeout=data.get("timeout", 60),
            difficulty=data.get("difficulty", "easy"),
            category=data.get("category", "general"),
        )


@dataclass
class TaskResult:
    task_id: str
    agent: str
    status: TaskStatus
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent": self.agent,
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration": self.duration,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
        }


@dataclass
class AgentConfig:
    name: str
    type: str
    command: str
    available: bool = False
    notes: str = ""


@dataclass
class Run:
    id: int
    agent: str
    task_count: int
    passed: int
    failed: int
    duration: float
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def score(self) -> float:
        if self.task_count == 0:
            return 0.0
        return (self.passed / self.task_count) * 100