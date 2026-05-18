# Agent-Bench: Benchmark Suite for Coding Agents

## Overview

Benchmark suite for comparing AI coding agents (Claude Code, Codex, Cursor) on reproducible real-world tasks with standardized metrics and leaderboard.

## Core Features

### 1. Task Definitions (YAML)
- Tasks defined in `tasks/` directory as YAML files
- Each task has: id, name, description, difficulty, setup commands, test commands, expected outputs
- Difficulty levels: easy, medium, hard
- Categories: refactoring, debugging, feature addition, documentation, testing

### 2. Agent Adapters
- Pluggable adapter interface for different agents
- Built-in adapters: Claude Code, Codex (CLI), custom command
- Each adapter: install check, run task, parse results
- Agent config in `agents.yaml` with paths and settings

### 3. Benchmark Runner
- `ab run <task-id>` - run single task
- `ab run --all` - run all tasks
- `ab run --filter <category>` - run by category
- Docker sandbox support for isolation
- Timeout per task (configurable, default 5min)
- Capture: stdout, stderr, exit code, duration

### 4. Results Storage
- SQLite database `results.db`
- Tables: runs, task_results, agent_configs
- JSON export: `ab report --json`
- CSV export: `ab report --csv`

### 5. Dashboard
- Simple HTML dashboard served by `ab serve`
- Shows: pass/fail rates, timing, agent comparison charts
- Leaderboard sorted by score

## Acceptance Criteria

1. CLI `ab` command with run, list, report, serve subcommands
2. At least 5 sample tasks (2 easy, 2 medium, 1 hard)
3. Working Claude Code adapter (if available) and generic command adapter
4. Results stored in SQLite and viewable via dashboard
5. Dashboard shows leaderboard and per-task breakdown
6. Build succeeds, CLI is functional

## Project Structure

```
agent-bench/
├── SPEC.md
├── pyproject.toml
├── src/
│   └── agent_bench/
│       ├── __init__.py
│       ├── cli.py          # CLI entry point
│       ├── runner.py       # Task execution engine
│       ├── adapters.py     # Agent adapter interface
│       ├── models.py       # Data models
│       ├── store.py        # SQLite storage
│       └── dashboard.py    # HTML dashboard generation
├── tasks/                  # Task definitions (YAML)
│   ├── add_tests.yaml
│   ├── fix_bug.yaml
│   ├── refactor_yaml.yaml
│   ├── write_docs.yaml
│   └── optimize_sql.yaml
├── agents.yaml             # Agent configurations
└── results.db              # SQLite results (gitignored)
```

## Tech Stack

- Python 3.10+
- Click for CLI
- SQLite for storage
- Jinja2 for dashboard HTML
- PyYAML for task definitions
