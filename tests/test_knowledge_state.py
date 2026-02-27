"""
Tests for knowledge state management and mastery tracking.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from skill_issue import knowledge_state


@pytest.fixture
def isolated_env(monkeypatch, tmp_path):
    """Set up isolated test environment for knowledge_state tests."""
    skill_dir = tmp_path / ".skill-issue"
    skill_dir.mkdir()
    graphs_dir = tmp_path / "knowledge_graphs"
    graphs_dir.mkdir()

    # Patch the module paths before any tests run
    monkeypatch.setattr(knowledge_state, "SKILL_DIR", skill_dir)
    monkeypatch.setattr(knowledge_state, "KNOWLEDGE_STATE_PATH", skill_dir / "knowledge_state.json")
    monkeypatch.setattr(knowledge_state, "GRAPHS_DIR", graphs_dir)

    return {"skill_dir": skill_dir, "graphs_dir": graphs_dir}


def _write_graph(graphs_dir: Path, domain: str, graph: dict):
    """Write a test graph to the graphs directory."""
    graph_path = graphs_dir / f"{domain}.json"
    graph_path.write_text(json.dumps(graph))


def _unique_id():
    """Generate unique ID for test isolation."""
    return uuid.uuid4().hex[:8]


class TestGetNodePriority:
    """Tests for get_node_priority function."""

    def test_high_weight_low_mastery_high_priority(self, isolated_env):
        """High reuse_weight + low mastery = high priority."""
        domain = f"priority-test-{_unique_id()}"
        node_id = "important-concept"

        graph = {"nodes": [{"id": node_id, "name": "Important", "reuse_weight": 0.95}]}
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        priority = knowledge_state.get_node_priority(domain, node_id)
        # priority = weight * (1 - mastery) = 0.95 * (1 - 0) = 0.95
        assert priority == 0.95

    def test_high_weight_high_mastery_low_priority(self, isolated_env):
        """High reuse_weight + high mastery = low priority."""
        domain = f"mastery-test-{_unique_id()}"
        node_id = "mastered-concept"

        graph = {"nodes": [{"id": node_id, "name": "Mastered", "reuse_weight": 0.95}]}
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        # Update mastery to high value (score=3 multiple times)
        for _ in range(5):
            knowledge_state.update_node(domain, node_id, 3)

        state = knowledge_state.load_state()
        mastery = state["domains"][domain]["nodes"][node_id]["mastery"]
        assert mastery > 0.8, f"Mastery should be high after multiple score=3: {mastery}"

        priority = knowledge_state.get_node_priority(domain, node_id)
        # priority = 0.95 * (1 - high_mastery) should be low
        assert priority < 0.2, f"Priority should be low for mastered node: {priority}"


class TestUpdateNode:
    """Tests for update_node function."""

    def test_score_2_increases_mastery(self, isolated_env):
        """Score 2 (correct) should increase mastery."""
        domain = f"update-test-{_unique_id()}"
        node_id = "test-node"

        graph = {"nodes": [{"id": node_id, "name": "Test", "reuse_weight": 0.5}]}
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        # Get initial mastery (should be 0)
        initial = knowledge_state.get_node_state(domain, node_id)
        assert initial["mastery"] == 0.0

        # Update with score=2
        result = knowledge_state.update_node(domain, node_id, 2)

        # score_to_mastery[2] = 0.7
        # EMA: new_mastery = 0.3 * 0.7 + 0.7 * 0.0 = 0.21
        assert result["mastery"] == pytest.approx(0.21, rel=0.01)
        assert result["attempts"] == 1

    def test_score_0_does_not_increase_mastery(self, isolated_env):
        """Score 0 (wrong) should not increase mastery from 0."""
        domain = f"zero-test-{_unique_id()}"
        node_id = "zero-node"

        graph = {"nodes": [{"id": node_id, "name": "Test", "reuse_weight": 0.5}]}
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        # Verify initial mastery is 0
        initial = knowledge_state.get_node_state(domain, node_id)
        assert initial["mastery"] == 0.0

        # Update with score=0 multiple times
        for _ in range(3):
            result = knowledge_state.update_node(domain, node_id, 0)

        # score_to_mastery[0] = 0.0, so mastery stays at 0
        # EMA: new = 0.3 * 0.0 + 0.7 * 0.0 = 0.0
        assert result["mastery"] == 0.0
        assert result["attempts"] == 3

    def test_score_0_decreases_existing_mastery(self, isolated_env):
        """Score 0 should decrease existing mastery via EMA."""
        domain = f"decrease-test-{_unique_id()}"
        node_id = "decay-node"

        graph = {"nodes": [{"id": node_id, "name": "Test", "reuse_weight": 0.5}]}
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        # Build up mastery with score=3
        for _ in range(5):
            knowledge_state.update_node(domain, node_id, 3)

        state = knowledge_state.load_state()
        high_mastery = state["domains"][domain]["nodes"][node_id]["mastery"]
        assert high_mastery > 0.7

        # Now score=0 should decrease it
        result = knowledge_state.update_node(domain, node_id, 0)
        # EMA: new = 0.3 * 0.0 + 0.7 * high_mastery < high_mastery
        assert result["mastery"] < high_mastery


class TestApplyDecay:
    """Tests for apply_decay function."""

    def test_mastery_decreases_after_grace_period(self, isolated_env):
        """Mastery should decrease for nodes not seen after grace period."""
        domain = f"decay-test-{_unique_id()}"
        node_id = "decay-node"

        graph = {"nodes": [{"id": node_id, "name": "Decay Test", "reuse_weight": 0.5}]}
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        # Build up mastery
        for _ in range(5):
            knowledge_state.update_node(domain, node_id, 3)

        state = knowledge_state.load_state()
        initial_mastery = state["domains"][domain]["nodes"][node_id]["mastery"]
        assert initial_mastery > 0.7

        # Manually set last_seen to 10 days ago (beyond 3-day grace)
        ten_days_ago = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        state["domains"][domain]["nodes"][node_id]["last_seen"] = ten_days_ago
        knowledge_state.save_state(state)

        # Apply decay
        knowledge_state.apply_decay()

        state = knowledge_state.load_state()
        decayed_mastery = state["domains"][domain]["nodes"][node_id]["mastery"]

        # Decay: 7 days past grace * 0.02/day = 0.14 reduction
        expected_decay = 7 * 0.02
        assert decayed_mastery < initial_mastery
        assert decayed_mastery == pytest.approx(initial_mastery - expected_decay, abs=0.01)
