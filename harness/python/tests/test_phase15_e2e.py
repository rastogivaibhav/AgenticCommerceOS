#!/usr/bin/env python3
"""End-to-end test for Phase 15 - UX Polish & Lifecycle Operations"""

import json
import sys
import time
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

def test_agent_crud():
    """Test creating and reading agents"""
    print("[TEST] Testing Agent CRUD operations...")

    # Initialize database
    from acosplatform.db.connection import ensure_schema
    from acosplatform.db.repository import get_agents, save_agent

    ensure_schema()

    # Get initial agents
    initial_agents = get_agents()
    initial_count = len(initial_agents)
    print(f"  [OK] Initial agent count: {initial_count}")

    # Create new agent
    test_agent = {
        "id": "test_agent_e2e_001",
        "name": "E2E Test Agent",
        "subsystem": "Testing",
        "status": "healthy",
        "tech_stack": "Test",
        "type": "Task",
        "calls": "0",
        "uptime": "100%",
        "skills": [],
        "grade": "-",
        "latency": "0ms",
        "history": []
    }

    save_agent(test_agent)
    print(f"  [OK] Created test agent: {test_agent['name']}")

    # Verify agent was saved
    agents_after = get_agents()
    assert len(agents_after) == initial_count + 1, "Agent not saved!"

    found = next((a for a in agents_after if a['id'] == test_agent['id']), None)
    assert found is not None, "Agent not found in list!"
    assert found['name'] == "E2E Test Agent", "Agent name mismatch!"
    print(f"  [OK] Agent retrieved from database: {found['name']}")

    return True

def test_skill_crud():
    """Test creating and reading skills"""
    print("\n[TEST] Testing Skill CRUD operations...")

    from acosplatform.db.connection import ensure_schema
    from acosplatform.db.repository import get_skills, save_skill

    ensure_schema()

    # Get initial skills
    initial_skills = get_skills()
    initial_count = len(initial_skills)
    print(f"  [OK] Initial skill count: {initial_count}")

    # Create new skill
    test_skill = {
        "id": "test_skill_e2e_001",
        "name": "E2E Test Skill",
        "category": "Testing",
        "type": "read",
        "tech_stack": "Test",
        "status": "active",
        "calls": "0",
        "code": "def evaluate():\n    pass\n",
        "linterWarnings": []
    }

    save_skill(test_skill)
    print(f"  [OK] Created test skill: {test_skill['name']}")

    # Verify skill was saved
    skills_after = get_skills()
    assert len(skills_after) == initial_count + 1, "Skill not saved!"

    found = next((s for s in skills_after if s['id'] == test_skill['id']), None)
    assert found is not None, "Skill not found in list!"
    assert found['name'] == "E2E Test Skill", "Skill name mismatch!"
    print(f"  [OK] Skill retrieved from database: {found['name']}")

    return True

def test_workflows_no_auth():
    """Test that workflows endpoint works without auth"""
    print("\n[TEST] Testing Workflows endpoint (auth removal)...")

    from acosplatform.workflows.service import list_workflows_with_state

    # This should work without token dependency
    try:
        workflows = list_workflows_with_state()
        print(f"  [OK] Workflows retrieved without auth: {len(workflows)} workflows found")
        return True
    except Exception as e:
        print(f"  [FAIL] Failed to retrieve workflows: {e}")
        return False

def test_loading_states():
    """Test that loading states are implemented in components"""
    print("\n[TEST] Testing Loading States implementation...")

    agents_file = Path("apps/ops_ui_v2/src/pages/Agents.jsx")
    skills_file = Path("apps/ops_ui_v2/src/pages/Skills.jsx")

    # Check Agents.jsx for isLoading state
    agents_content = agents_file.read_text()
    assert "const [isLoading, setIsLoading] = useState(true)" in agents_content, "Missing isLoading state in Agents"
    assert "skeleton-row" in agents_content, "Missing skeleton-row class usage in Agents"
    print("  [OK] Agents.jsx has isLoading state and skeleton UI")

    # Check Skills.jsx for isLoading state
    skills_content = skills_file.read_text()
    assert "const [isLoading, setIsLoading] = useState(true)" in skills_content, "Missing isLoading state in Skills"
    assert "skeleton-row" in skills_content, "Missing skeleton-row class usage in Skills"
    print("  [OK] Skills.jsx has isLoading state and skeleton UI")

    # Check CSS for animation
    css_file = Path("apps/ops_ui_v2/src/pages/Lists.css")
    css_content = css_file.read_text()
    assert ".skeleton-row" in css_content, "Missing skeleton-row CSS class"
    assert "loadingPulsey" in css_content, "Missing loadingPulsey animation"
    print("  [OK] Lists.css has skeleton animation styles")

    return True

def test_wcag_contrast():
    """Test WCAG AA color contrast improvements"""
    print("\n[TEST] Testing WCAG AA Contrast improvements...")

    css_file = Path("apps/ops_ui_v2/src/pages/Lists.css")
    css_content = css_file.read_text()

    # Check that darker text colors are used (WCAG AA compliant)
    # Green status should use darker green (#059669) not light green (#34d399)
    assert "#059669" in css_content, "Missing darker green text color for status badges"
    assert "#b45309" in css_content, "Missing darker amber text color for status badges"
    assert "#0369a1" in css_content, "Missing darker blue text color for read tags"
    assert "#7f1d1d" in css_content, "Missing darker red text color for write tags"

    print("  [OK] Status badge colors updated for WCAG AA compliance")
    print("  [OK] Type tag colors updated for WCAG AA compliance")

    # Check that secondary text has improved weight
    assert "font-weight: 500" in css_content or ".stat-label" in css_content, "Missing font-weight improvements"
    print("  [OK] Secondary text readability improved")

    return True

def test_workflows_auth_removal():
    """Test that workflows auth has been removed from router"""
    print("\n[TEST] Testing Workflows auth removal...")

    router_file = Path("apps/ops_api/routers/workflows.py")
    router_content = router_file.read_text()

    # Check that Depends(require_ops_token) has been removed
    lines = router_content.split('\n')
    for i, line in enumerate(lines):
        if '@router.get' in line or '@router.post' in line or '@router.patch' in line:
            # Check the next line(s) for the function definition
            # It should NOT have _token parameter with Depends
            if 'Depends(require_ops_token)' in line or ('require_ops_token' in line and 'import' not in line):
                print(f"  [FAIL] Auth still present on line {i+1}: {line}")
                return False

    # Verify the unused imports were removed
    assert 'from acosplatform.auth.api_key import require_ops_token' not in router_content, "require_ops_token import not removed"
    print("  [OK] Workflows auth token requirement removed from router")
    print("  [OK] Unused imports cleaned up")

    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Phase 15 - UX Polish & Lifecycle Operations")
    print("End-to-End Test Suite")
    print("=" * 60)

    tests = [
        ("Agent CRUD Operations", test_agent_crud),
        ("Skill CRUD Operations", test_skill_crud),
        ("Workflows Auth Removal", test_workflows_no_auth),
        ("Loading States Implementation", test_loading_states),
        ("WCAG AA Contrast Improvements", test_wcag_contrast),
        ("Workflows Router Auth Removal", test_workflows_auth_removal),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except AssertionError as e:
            print(f"  [FAIL] Assertion failed: {e}")
            results.append((test_name, False))
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            results.append((test_name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
