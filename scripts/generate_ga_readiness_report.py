from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from subprocess import run, PIPE, TimeoutExpired
from datetime import datetime, UTC
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "release" / "GA_READINESS_REPORT.md"


def cmd(label, args, timeout=180):
    try:
        proc = run(args, cwd=ROOT, stdout=PIPE, stderr=PIPE, text=True, timeout=timeout)
        return {"label": label, "code": proc.returncode, "stdout": proc.stdout[-5000:], "stderr": proc.stderr[-5000:], "timed_out": False}
    except TimeoutExpired as exc:
        return {"label": label, "code": 124, "stdout": (exc.stdout or "")[-5000:] if isinstance(exc.stdout, str) else "", "stderr": (exc.stderr or "")[-5000:] if isinstance(exc.stderr, str) else "", "timed_out": True}


if __name__ == "__main__":
    checks = [
        cmd("northstar pytest", ["python", "-m", "pytest", "harness/python/tests/northstar", "-q"]),
        cmd("northstar smoke", ["python", "scripts/northstar_smoke.py"]),
        cmd("week11/12 uat and production gate tests", ["python", "-m", "pytest", "harness/python/tests/integration/test_uat_week11_journeys.py", "harness/python/tests/test_week12_production_gate_checker.py", "-q"]),
    ]
    docker_available = bool(shutil.which("docker"))
    lines = [
        "# ACOS GA Readiness Report",
        "",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "## Automated checks",
        "",
    ]
    for c in checks:
        status = "PASS" if c["code"] == 0 else ("TIMEOUT" if c["timed_out"] else "FAIL")
        lines += [f"### {c['label']} — {status}", "", "```", c["stdout"] or c["stderr"], "```", ""]
    lines += [
        "### Docker runtime proof",
        "",
        "```",
        "PASS: docker executable found" if docker_available else "BLOCKED: docker executable not found in this sandbox",
        "```",
        "",
        "## GA status",
        "",
        "This package is now a hardened north-star pilot foundation. It is not a fully certified enterprise GA release until Docker Compose, cloud deployment, production RBAC, Postgres migrations, and full-harness completion are proven in CI.",
        "",
        "## Implemented north-star capabilities",
        "",
        "- Omnichannel message envelope and session/journey spine.",
        "- Durable SQLite-backed pilot state for sessions, identities, journeys, messages, and evidence.",
        "- Intent router and multi-agent retail routing skeleton.",
        "- Native retail tool layer with catalog, inventory, order, returns, loyalty, and case tools.",
        "- Evidence events for messages, intent, agent selection, tool calls, and responses.",
        "- Optional API-key guardrails for north-star and hosted MCP endpoints.",
        "- MCP client/router foundation and ACOS MCP JSON-RPC server.",
        "- GraphQL endpoint for Studio/Ops composition.",
        "- Golden winter-wedding retail journey smoke path.",
        "",
        "## Remaining GA blockers",
        "",
        "1. Docker Compose runtime proof in a Docker-enabled environment.",
        "2. Postgres migrations/repositories for north-star tables.",
        "3. Production-default RBAC and tenant isolation for GraphQL, MCP, and north-star APIs.",
        "4. Full legacy harness completion without timeout.",
        "5. Frontend bundle splitting and production performance budget.",
        "6. MCP validation against target client implementations.",
        "7. Cloud deployment smoke test.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(OUT)
