"""SQLite storage for benchmark results."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Run, TaskResult, TaskStatus


class Store:
    def __init__(self, db_path: str = "results.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent TEXT NOT NULL,
                    task_count INTEGER DEFAULT 0,
                    passed INTEGER DEFAULT 0,
                    failed INTEGER DEFAULT 0,
                    duration REAL DEFAULT 0.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    task_id TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    status TEXT NOT NULL,
                    stdout TEXT DEFAULT '',
                    stderr TEXT DEFAULT '',
                    duration REAL DEFAULT 0.0,
                    error TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                )
            """)
            conn.commit()

    def save_result(self, result: TaskResult, run_id: Optional[int] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO task_results 
                (run_id, task_id, agent, status, stdout, stderr, duration, error, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    result.task_id,
                    result.agent,
                    result.status.value,
                    result.stdout,
                    result.stderr,
                    result.duration,
                    result.error,
                    result.started_at.isoformat(),
                    result.completed_at.isoformat() if result.completed_at else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def create_run(self, agent: str, task_count: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO runs (agent, task_count) VALUES (?, ?)",
                (agent, task_count),
            )
            conn.commit()
            return cursor.lastrowid

    def update_run(self, run_id: int, passed: int, failed: int, duration: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE runs SET passed = ?, failed = ?, duration = ? WHERE id = ?",
                (passed, failed, duration, run_id),
            )
            conn.commit()

    def get_all_runs(self) -> list[Run]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, agent, task_count, passed, failed, duration, created_at FROM runs ORDER BY created_at DESC"
            )
            return [
                Run(
                    id=row[0],
                    agent=row[1],
                    task_count=row[2],
                    passed=row[3],
                    failed=row[4],
                    duration=row[5],
                    created_at=datetime.fromisoformat(row[6]),
                )
                for row in cursor.fetchall()
            ]

    def get_results_by_run(self, run_id: int) -> list[TaskResult]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT task_id, agent, status, stdout, stderr, duration, started_at, completed_at, error
                FROM task_results WHERE run_id = ?
                """,
                (run_id,),
            )
            results = []
            for row in cursor.fetchall():
                results.append(
                    TaskResult(
                        task_id=row[0],
                        agent=row[1],
                        status=TaskStatus(row[2]),
                        stdout=row[3] or "",
                        stderr=row[4] or "",
                        duration=row[5] or 0.0,
                        started_at=datetime.fromisoformat(row[6]) if row[6] else datetime.utcnow(),
                        completed_at=datetime.fromisoformat(row[7]) if row[7] else None,
                        error=row[8],
                    )
                )
            return results

    def export_json(self) -> str:
        runs = self.get_all_runs()
        data = {"runs": []}
        for run in runs:
            run_data = {
                "id": run.id,
                "agent": run.agent,
                "task_count": run.task_count,
                "passed": run.passed,
                "failed": run.failed,
                "duration": run.duration,
                "score": run.score,
                "created_at": run.created_at.isoformat(),
                "results": [],
            }
            for r in self.get_results_by_run(run.id):
                run_data["results"].append(r.to_dict())
            data["runs"].append(run_data)
        return json.dumps(data, indent=2)

    def export_csv(self) -> str:
        runs = self.get_all_runs()
        lines = ["run_id,agent,task_count,passed,failed,duration,score,created_at"]
        for run in runs:
            lines.append(
                f"{run.id},{run.agent},{run.task_count},{run.passed},{run.failed},{run.duration:.2f},{run.score:.1f},{run.created_at.isoformat()}"
            )
        return "\n".join(lines)