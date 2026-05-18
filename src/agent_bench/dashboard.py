"""Dashboard generation for agent-bench results."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from jinja2 import Template

from .models import Run
from .store import Store


DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent-Bench Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        .subtitle { color: #94a3b8; margin-bottom: 2rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .card { background: #1e293b; border-radius: 12px; padding: 1.5rem; }
        .card h3 { color: #94a3b8; font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
        .card .value { font-size: 2rem; font-weight: 700; }
        .card .sub { color: #64748b; font-size: 0.875rem; }
        .success { color: #22c55e; }
        .fail { color: #ef4444; }
        table { width: 100%; border-collapse: collapse; }
        th, td { text-align: left; padding: 0.75rem; border-bottom: 1px solid #334155; }
        th { color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; }
        .score { font-weight: 700; }
        .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }
        .badge-pass { background: #22c55e20; color: #22c55e; }
        .badge-fail { background: #ef444420; color: #ef4444; }
        .leaderboard tr:hover { background: #1e293b; }
        .rank { font-size: 1.5rem; font-weight: 700; width: 50px; }
        .rank-1 { color: #ffd700; }
        .rank-2 { color: #c0c0c0; }
        .rank-3 { color: #cd7f32; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Agent-Bench Dashboard</h1>
        <p class="subtitle">Last updated: {{ last_updated }}</p>

        <div class="grid">
            <div class="card">
                <h3>Total Runs</h3>
                <div class="value">{{ total_runs }}</div>
                <div class="sub">benchmark executions</div>
            </div>
            <div class="card">
                <h3>Pass Rate</h3>
                <div class="value {% if avg_score >= 70 %}success{% endif %}">{{ "%.1f"|format(avg_score) }}%</div>
                <div class="sub">average score</div>
            </div>
            <div class="card">
                <h3>Best Agent</h3>
                <div class="value">{{ best_agent or "N/A" }}</div>
                <div class="sub">{{ "%.1f"|format(best_score) }}% best score</div>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-bottom: 1rem;">Leaderboard</h2>
            <table class="leaderboard">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Agent</th>
                        <th>Tasks</th>
                        <th>Passed</th>
                        <th>Failed</th>
                        <th>Score</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody>
                    {% for run in runs %}
                    <tr>
                        <td class="rank {% if loop.index <= 3 %}rank-{{ loop.index }}{% endif %}">{{ loop.index }}</td>
                        <td>{{ run.agent }}</td>
                        <td>{{ run.task_count }}</td>
                        <td class="success">{{ run.passed }}</td>
                        <td class="fail">{{ run.failed }}</td>
                        <td class="score">{{ "%.1f"|format(run.score) }}%</td>
                        <td>{{ run.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% if not runs %}
            <p style="color: #64748b; padding: 2rem; text-align: center;">No benchmark runs yet. Run `ab run --all` to get started.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""


class Dashboard:
    """HTML dashboard generator."""

    def __init__(self, store: Optional[Store] = None):
        self.store = store or Store()
        self.template = Template(DASHBOARD_TEMPLATE)

    def generate(self) -> str:
        """Generate the dashboard HTML."""
        runs = self.store.get_all_runs()

        total_runs = len(runs)
        avg_score = sum(r.score for r in runs) / len(runs) if runs else 0

        best_agent = None
        best_score = 0
        agent_scores = {}
        for run in runs:
            if run.agent not in agent_scores:
                agent_scores[run.agent] = []
            agent_scores[run.agent].append(run.score)

        if agent_scores:
            best_agent = max(agent_scores, key=lambda a: sum(agent_scores[a]) / len(agent_scores[a]))
            best_score = sum(agent_scores[best_agent]) / len(agent_scores[best_agent])

        return self.template.render(
            last_updated=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            total_runs=total_runs,
            avg_score=avg_score,
            best_agent=best_agent,
            best_score=best_score,
            runs=runs,
        )

    def save(self, output_path: str = "dashboard.html"):
        """Generate and save dashboard to file."""
        html = self.generate()
        Path(output_path).write_text(html)
        return output_path