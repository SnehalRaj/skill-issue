"""
Tests for the retroactive bootstrap analyzer.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from skill_issue import analyzer
from skill_issue import knowledge_state


@pytest.fixture
def isolated_env(monkeypatch, tmp_path):
    """Set up isolated test environment."""
    # Isolated skill-issue directory
    skill_dir = tmp_path / ".skill-issue"
    skill_dir.mkdir()
    graphs_dir = tmp_path / "knowledge_graphs"
    graphs_dir.mkdir()

    # Isolated Claude projects directory
    claude_dir = tmp_path / ".claude" / "projects"
    claude_dir.mkdir(parents=True)

    # Patch knowledge_state paths
    monkeypatch.setattr(knowledge_state, "SKILL_DIR", skill_dir)
    monkeypatch.setattr(knowledge_state, "KNOWLEDGE_STATE_PATH", skill_dir / "knowledge_state.json")
    monkeypatch.setattr(knowledge_state, "GRAPHS_DIR", graphs_dir)

    # Patch analyzer paths
    monkeypatch.setattr(analyzer, "CLAUDE_PROJECTS_DIR", claude_dir)

    return {
        "skill_dir": skill_dir,
        "graphs_dir": graphs_dir,
        "claude_dir": claude_dir,
    }


def _write_graph(graphs_dir: Path, domain: str, graph: dict):
    """Write a test graph to the graphs directory."""
    graph_path = graphs_dir / f"{domain}.json"
    graph_path.write_text(json.dumps(graph))


def _unique_id():
    """Generate unique ID for test isolation."""
    return uuid.uuid4().hex[:8]


def _create_session(claude_dir: Path, project_name: str, messages: list[dict]) -> Path:
    """
    Create a mock session JSONL file.

    messages: list of {"role": "user"|"assistant", "text": str}
    """
    project_dir = claude_dir / project_name
    project_dir.mkdir(exist_ok=True)

    session_id = str(uuid.uuid4())
    session_path = project_dir / f"{session_id}.jsonl"

    lines = []
    timestamp = datetime.now(timezone.utc).isoformat()

    for msg in messages:
        obj = {
            "type": msg["role"],
            "timestamp": timestamp,
            "message": {
                "content": msg["text"]
            }
        }
        lines.append(json.dumps(obj))

    session_path.write_text("\n".join(lines))
    return session_path


class TestClassifyMessageIntent:
    """Tests for classify_message_intent function."""

    def test_question_with_what_is(self):
        assert analyzer.classify_message_intent("What is gradient descent?") == "question"

    def test_question_with_how_does(self):
        assert analyzer.classify_message_intent("How does backpropagation work?") == "question"

    def test_question_with_question_mark(self):
        assert analyzer.classify_message_intent("Can you help me with this?") == "question"

    def test_question_with_confusion(self):
        assert analyzer.classify_message_intent("I don't understand regularization") == "question"

    def test_assertion_with_code_block(self):
        text = "Here's my implementation:\n```python\ndef train(): pass\n```"
        assert analyzer.classify_message_intent(text) == "assertion"

    def test_assertion_with_i_implemented(self):
        assert analyzer.classify_message_intent("I implemented the loss function") == "assertion"

    def test_neutral_simple_statement(self):
        assert analyzer.classify_message_intent("Let's work on this next") == "neutral"


class TestDetectConceptsInText:
    """Tests for detect_concepts_in_text function."""

    def test_detects_node_name(self, isolated_env):
        domain = f"detect-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "gradient-descent", "name": "Gradient Descent", "aliases": ["SGD"]}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        detected = analyzer.detect_concepts_in_text("I'm learning about gradient descent", domain)
        assert "gradient-descent" in detected

    def test_detects_alias(self, isolated_env):
        domain = f"alias-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "gradient-descent", "name": "Gradient Descent", "aliases": ["SGD", "optimizer"]}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        detected = analyzer.detect_concepts_in_text("I configured the SGD optimizer", domain)
        assert "gradient-descent" in detected

    def test_detects_kebab_case_id(self, isolated_env):
        domain = f"kebab-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "bias-variance-tradeoff", "name": "Bias-Variance Tradeoff", "aliases": []}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        detected = analyzer.detect_concepts_in_text("the bias variance tradeoff is important", domain)
        assert "bias-variance-tradeoff" in detected

    def test_no_false_positives(self, isolated_env):
        domain = f"fp-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "transformer", "name": "Transformer", "aliases": ["BERT"]}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        detected = analyzer.detect_concepts_in_text("I transformed the data using pandas", domain)
        # "transform" should not match "transformer" unless the full word matches
        assert detected == []  # pandas transform != transformer


class TestAnalyzeSessions:
    """Tests for analyze_sessions function."""

    def test_question_decreases_score(self, isolated_env):
        domain = f"analyze-q-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "backpropagation", "name": "Backpropagation", "aliases": ["backprop"]}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Create session with user asking about backprop
        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "What is backpropagation?"},
                {"role": "assistant", "text": "Backpropagation is the chain rule applied to neural networks..."},
            ]
        )

        result = analyzer.analyze_sessions([session], [domain])

        assert "backpropagation" in result[domain]
        # Score clamped to 0.0 minimum (question signal was -0.15, clamped up)
        assert result[domain]["backpropagation"]["score"] == 0.0
        assert "question" in result[domain]["backpropagation"]["signals"]

    def test_assertion_increases_score(self, isolated_env):
        domain = f"analyze-a-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "loss-functions", "name": "Loss Functions", "aliases": ["cross-entropy", "MSE"]}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Create session with user showing code
        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "I implemented the cross-entropy loss function:\n```python\ndef loss(): pass\n```"},
                {"role": "assistant", "text": "Looks good!"},
            ]
        )

        result = analyzer.analyze_sessions([session], [domain])

        assert "loss-functions" in result[domain]
        assert result[domain]["loss-functions"]["score"] > 0.0
        assert "assertion" in result[domain]["loss-functions"]["signals"]

    def test_claude_only_mention_slight_positive(self, isolated_env):
        domain = f"analyze-c-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "regularization", "name": "Regularization", "aliases": ["L1", "L2"]}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Claude mentions regularization but user doesn't
        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "How can I prevent overfitting?"},
                {"role": "assistant", "text": "You can use regularization like L1 or L2 penalties."},
            ]
        )

        result = analyzer.analyze_sessions([session], [domain])

        assert "regularization" in result[domain]
        assert result[domain]["regularization"]["score"] > 0.0
        assert "claude_explained" in result[domain]["regularization"]["signals"]

    def test_score_clamped_to_max(self, isolated_env):
        domain = f"clamp-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "attention", "name": "Attention", "aliases": []}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Many assertion signals
        messages = []
        for i in range(10):
            messages.append({"role": "user", "text": f"I built attention mechanism {i}:\n```code\n```"})
            messages.append({"role": "assistant", "text": "Great!"})

        session = _create_session(isolated_env["claude_dir"], "-test-project", messages)
        result = analyzer.analyze_sessions([session], [domain])

        assert result[domain]["attention"]["score"] <= 0.8


class TestApplyAnalysisToState:
    """Tests for apply_analysis_to_state function."""

    def test_updates_node_mastery(self, isolated_env):
        domain = f"apply-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "test-node", "name": "Test Node", "aliases": [], "reuse_weight": 0.5}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Initialize domain
        knowledge_state.init_domain(domain)

        # Apply analysis
        analysis = {
            domain: {
                "test-node": {
                    "score": 0.6,
                    "signals": ["assertion", "assertion", "neutral_user"]
                }
            }
        }

        analyzer.apply_analysis_to_state(analysis)

        # Check state was updated
        state = knowledge_state.load_state()
        node = state["domains"][domain]["nodes"]["test-node"]
        assert node["mastery"] == 0.6
        assert node["attempts"] == 3
        assert node["status"] == "developing"

    def test_skips_nodes_without_signals(self, isolated_env):
        domain = f"skip-test-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "test-node", "name": "Test Node", "aliases": [], "reuse_weight": 0.5}
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        knowledge_state.init_domain(domain)

        # Analysis with empty signals
        analysis = {
            domain: {
                "test-node": {
                    "score": 0.5,
                    "signals": []  # No signals
                }
            }
        }

        analyzer.apply_analysis_to_state(analysis)

        # Node should not be updated (still at initial 0.0)
        state = knowledge_state.load_state()
        node = state["domains"][domain]["nodes"]["test-node"]
        assert node["mastery"] == 0.0


class TestFindSessions:
    """Tests for session discovery functions."""

    def test_find_project_sessions(self, isolated_env, monkeypatch):
        # Create a mock project directory
        project_path = Path("/Users/test/my-project")
        mangled = "-Users-test-my-project"
        project_dir = isolated_env["claude_dir"] / mangled
        project_dir.mkdir()

        # Create some session files
        (project_dir / "session1.jsonl").write_text("{}")
        (project_dir / "session2.jsonl").write_text("{}")

        sessions = analyzer.find_project_sessions(project_path)
        assert len(sessions) == 2

    def test_find_all_sessions(self, isolated_env):
        # Create sessions in multiple projects
        for proj in ["proj1", "proj2"]:
            proj_dir = isolated_env["claude_dir"] / proj
            proj_dir.mkdir()
            (proj_dir / "session.jsonl").write_text("{}")

        sessions = analyzer.find_all_sessions()
        assert len(sessions) == 2


class TestExtractMessages:
    """Tests for extract_messages function."""

    def test_extracts_string_content(self, isolated_env):
        session = _create_session(
            isolated_env["claude_dir"],
            "-test",
            [{"role": "user", "text": "Hello world"}]
        )

        messages = analyzer.extract_messages(session)
        assert len(messages) == 1
        assert messages[0]["text"] == "Hello world"
        assert messages[0]["role"] == "user"

    def test_handles_list_content(self, isolated_env):
        # Create session with list-format content
        project_dir = isolated_env["claude_dir"] / "-test-list"
        project_dir.mkdir()
        session_path = project_dir / "session.jsonl"

        obj = {
            "type": "user",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": {
                "content": [
                    {"type": "text", "text": "First part"},
                    {"type": "text", "text": "Second part"},
                ]
            }
        }
        session_path.write_text(json.dumps(obj))

        messages = analyzer.extract_messages(session_path)
        assert len(messages) == 1
        assert "First part" in messages[0]["text"]
        assert "Second part" in messages[0]["text"]

    def test_skips_non_message_entries(self, isolated_env):
        project_dir = isolated_env["claude_dir"] / "-test-skip"
        project_dir.mkdir()
        session_path = project_dir / "session.jsonl"

        lines = [
            json.dumps({"type": "progress", "data": {}}),
            json.dumps({"type": "user", "message": {"content": "Real message"}}),
            json.dumps({"type": "queue-operation", "operation": "dequeue"}),
        ]
        session_path.write_text("\n".join(lines))

        messages = analyzer.extract_messages(session_path)
        assert len(messages) == 1
        assert messages[0]["text"] == "Real message"
