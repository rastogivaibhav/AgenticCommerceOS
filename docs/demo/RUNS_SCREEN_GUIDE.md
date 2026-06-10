# ACOS Runs Screen Guide

The Runs screen is the operator view for every captured north-star orchestration.

Open: `/ui/runs`

Use it to prove:

- run list and status
- session ID, journey ID and correlation ID
- primary intent and agent
- participating agents
- tool calls and policy verdicts
- evidence timeline
- human handoff events
- replay of a captured run

Demo sequence:

1. Open `/ui/demo-guide`.
2. Open `/ui/runs`.
3. Click **Run golden journey**.
4. Select the newest run.
5. Show the response, agents, tool calls and evidence timeline.
6. Click **Replay this run**.
7. Move to `/ui/studio-proof` to show the broader control-plane proof.

API endpoints:

- `GET /api/northstar/runs`
- `GET /api/northstar/runs/{run_id}`
- `POST /api/northstar/replays/{replay_id}/rerun`
