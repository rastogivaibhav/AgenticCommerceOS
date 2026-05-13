"""Static UI load check for the embedded ACOS Ops UI.

This verifies that the FastAPI app can serve the React shell and its built assets
from /ui without requiring Docker or a live browser.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from apps.ops_api.main import app


def main() -> int:
    client = TestClient(app)
    checks: dict[str, object] = {}

    index = client.get('/ui/')
    checks['ui_index_status'] = index.status_code
    checks['ui_index_has_root'] = '<div id="root"></div>' in index.text
    checks['ui_index_has_assets'] = '/ui/assets/' in index.text

    asset_paths = re.findall(r'(?:src|href)="(/ui/assets/[^"]+)"', index.text)
    checks['asset_count'] = len(asset_paths)
    asset_statuses = []
    for asset in asset_paths:
        response = client.get(asset)
        asset_statuses.append({'asset': asset, 'status': response.status_code, 'content_type': response.headers.get('content-type', '')})
    checks['assets'] = asset_statuses
    checks['all_assets_200'] = bool(asset_paths) and all(item['status'] == 200 for item in asset_statuses)

    deep_links = ['/ui/runs', '/ui/estate', '/ui/agent-registry', '/ui/capabilities', '/ui/a2a-trace', '/ui/channel-modes', '/ui/evaluations', '/ui/governance']
    deep_results = []
    for route in deep_links:
        response = client.get(route)
        deep_results.append({'route': route, 'status': response.status_code, 'serves_shell': '<div id="root"></div>' in response.text})
    checks['deep_links'] = deep_results
    checks['deep_link_status'] = 200 if all(item['status'] == 200 for item in deep_results) else 500
    checks['deep_link_serves_shell'] = all(item['serves_shell'] for item in deep_results)

    head_index = client.head('/ui/')
    checks['head_ui_status'] = head_index.status_code

    ok = (
        checks['ui_index_status'] == 200
        and checks['ui_index_has_root']
        and checks['ui_index_has_assets']
        and checks['all_assets_200']
        and checks['deep_link_status'] == 200
        and checks['deep_link_serves_shell']
        and checks['head_ui_status'] == 200
    )
    checks['status'] = 'pass' if ok else 'fail'

    report_path = Path('docs/release/UI_LOAD_CHECK_REPORT.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(checks, indent=2), encoding='utf-8')
    print(json.dumps(checks, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
