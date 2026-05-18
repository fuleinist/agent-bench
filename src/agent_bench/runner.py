"""Task runner engine for agent-bench."""

import subprocess
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Task, TaskResult, TaskStatus
from .store import Store


class Runner:
    """Task execution engine."""

    def __init__(self, store: Optional[Store] = None):
        self.store = store or Store()

    def load_tasks(self, tasks_dir: str = "tasks") -> list[Task]:
        """Load all tasks from the tasks directory."""
        tasks = []
        tasks_path = Path(tasks_dir)
        if not tasks_path.exists():
            return tasks

        for yaml_file in sorted(tasks_path.glob("*.yaml")):
            try:
                task = Task.from_yaml(str(yaml_file))
                tasks.append(task)
            except Exception as e:
                print(f"Warning: Failed to load {yaml_file}: {e}")

        return tasks

    def setup_task(self, task: Task, work_dir: Path) -> bool:
        """Run task setup commands in the work directory."""
        if not task.setup:
            return True

        try:
            # Run setup commands
            subprocess.run(
                task.setup,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                timeout=30,
            )
            return True
        except Exception as e:
            print(f"Setup failed: {e}")
            return False

    def verify_task(self, task: Task, work_dir: Path) -> bool:
        """Run test command and verify expected outputs."""
        if not task.test_command:
            return True

        try:
            result = subprocess.run(
                task.test_command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=task.timeout,
            )

            # Check for expected outputs
            output = result.stdout + result.stderr
            for expected in task.expected_outputs:
                if expected not in output:
                    return False

            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def run_task(
        self, task: Task, agent_cmd: str, work_dir: Optional[Path] = None
    ) -> TaskResult:
        """Run a task with a given agent command."""
        started = datetime.utcnow()

        # Create temp work directory
        if work_dir is None:
            work_dir = Path(tempfile.mkdtemp(prefix="agent-bench-"))

        # Run setup
        setup_ok = self.setup_task(task, work_dir)

        # Run agent command
        result = TaskResult(
            task_id=task.id,
            agent=agent_cmd,
            status=TaskStatus.PASSED if setup_ok else TaskStatus.ERROR,
            started_at=started,
        )

        if not setup_ok:
            result.error = "Task setup failed"
            result.completed_at = datetime.utcnow()
            return result

        try:
            # Execute the agent with the task prompt
            proc = subprocess.Popen(
                agent_cmd.split() + [task.task_prompt],
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            try:
                stdout, stderr = proc.communicate(timeout=task.timeout)
                result.stdout = stdout
                result.stderr = stderr
                result.status = TaskStatus.PASSED if proc.returncode == 0 else TaskStatus.FAILED
            except subprocess.TimeoutExpired:
                proc.kill()
                result.status = TaskStatus.TIMEOUT
                result.error = f"Task timed out after {task.timeout} seconds"

        except Exception as e:
            result.status = TaskStatus.ERROR
            result.error = str(e)

        result.completed_at = datetime.utcnow()
        result.duration = (result.completed_at - started).total_seconds()

        return result

    def run_benchmark(
        self,
        tasks: list[Task],
        agent_name: str,
        agent_cmd: str,
        save: bool = True,
    ) -> tuple[int, int, list[TaskResult]]:
        """Run a full benchmark across tasks."""
        passed = 0
        failed = 0
        results = []

        for task in tasks:
            result = self.run_task(task, agent_cmd)
            results.append(result)

            if result.status == TaskStatus.PASSED:
                passed += 1
            else:
                failed += 1

            # Save result if store is available
            if save:
                self.store.save_result(result)

        return passed, failed, results

    def run_single_task(
        self, task_id: str, agent_name: str, agent_cmd: str
    ) -> Optional[TaskResult]:
        """Run a single task by ID."""
        tasks = self.load_tasks()
        for task in tasks:
            if task.id == task_id:
                return self.run_task(task, agent_cmd)
        return None