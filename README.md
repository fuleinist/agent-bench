# Agent-Bench

Benchmark suite for comparing AI coding agents on reproducible real-world tasks.

## Features

- **Standardized Tasks**: YAML-defined tasks with setup, prompt, and test commands
- **Agent Adapters**: Pluggable interface for Claude Code, Codex, Cursor, and custom agents
- **Results Storage**: SQLite database with JSON/CSV export
- **Dashboard**: HTML dashboard with leaderboard and per-task breakdown

## Installation

```bash
pip install -e .
```

## Usage

### List available tasks
```bash
ab list
```

### Run a single task
```bash
ab run add_tests --agent claude-code
```

### Run all tasks
```bash
ab run --all --agent claude-code
```

### Generate report
```bash
ab report --format json
ab report --format csv -o results.csv
```

### Generate dashboard
```bash
ab serve -o dashboard.html
```

### List available agents
```bash
ab agents
```

## Adding Tasks

Create a YAML file in `tasks/` directory:

```yaml
id: my_task
name: My Task
description: |
  Description of the task.
category: feature
difficulty: medium

setup: |
  # Commands to create initial files
  echo 'code' > file.py

task_prompt: |
  Instruction for the agent to complete.

test_command: python test.py
expected_outputs:
  - "expected text in output"
timeout: 120
difficulty: medium
```

## Agent Configuration

Edit `agents.yaml` to configure agents:

```yaml
agents:
  my-agent:
    type: command
    command: my-agent-cli
    available: true
```

## License

MIT
