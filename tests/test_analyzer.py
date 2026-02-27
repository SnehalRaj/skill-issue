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


class TestClaudeOnlyMentions:
    """Tests for Claude-only mention scoring behavior."""

    def test_analyzer_ignores_claude_only_mentions_low_score(self, isolated_env):
        """
        If a concept only appears in Claude responses (assistant role),
        the score should be minimal (<= 0.05 per mention).
        User questions/confusion should lower score.
        User code/assertions should raise score.
        """
        domain = f"claude-only-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "quantum-annealing", "name": "Quantum Annealing", "aliases": ["QA"]},
                {"id": "variational-circuits", "name": "Variational Circuits", "aliases": ["VQE"]},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Claude mentions quantum-annealing once, but user never mentions it
        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "Tell me about optimization algorithms"},
                {"role": "assistant", "text": "Quantum annealing is a metaheuristic for optimization."},
            ]
        )

        result = analyzer.analyze_sessions([session], [domain])

        # quantum-annealing only mentioned by Claude once, should have minimal score
        if "quantum-annealing" in result[domain]:
            assert result[domain]["quantum-annealing"]["score"] <= 0.05
            assert "claude_explained" in result[domain]["quantum-annealing"]["signals"]
            # Claude-only mentions should never give high mastery
            assert result[domain]["quantum-annealing"]["score"] < 0.20

    def test_user_question_lowers_score(self, isolated_env):
        """User asking questions about a concept indicates weakness."""
        domain = f"question-weakness-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "backprop", "name": "Backpropagation", "aliases": ["back propagation"]},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "What is backpropagation? I don't understand it."},
                {"role": "assistant", "text": "Backpropagation is..."},
                {"role": "user", "text": "Why does backpropagation use the chain rule?"},
                {"role": "assistant", "text": "The chain rule allows..."},
            ]
        )

        result = analyzer.analyze_sessions([session], [domain])

        # Multiple questions should result in 0.0 score (clamped from negative)
        assert "backprop" in result[domain]
        assert result[domain]["backprop"]["score"] == 0.0
        assert result[domain]["backprop"]["signals"].count("question") >= 2

    def test_user_code_raises_score(self, isolated_env):
        """User sharing code/implementations indicates strength."""
        domain = f"code-strength-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "attention-mechanism", "name": "Attention Mechanism", "aliases": ["self-attention"]},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "I implemented the attention mechanism:\n```python\nclass Attention:\n    pass\n```"},
                {"role": "assistant", "text": "Nice implementation!"},
                {"role": "user", "text": "I built another self-attention variant:\n```python\nclass SelfAttention:\n    pass\n```"},
                {"role": "assistant", "text": "Good work!"},
            ]
        )

        result = analyzer.analyze_sessions([session], [domain])

        # Code sharing should give high score
        assert "attention-mechanism" in result[domain]
        assert result[domain]["attention-mechanism"]["score"] >= 0.4
        assert result[domain]["attention-mechanism"]["signals"].count("assertion") >= 2


class TestConceptFrequencyOrdering:
    """Tests for frequency-based mastery scoring."""

    def test_analyzer_concept_frequency_ordering(self, isolated_env):
        """
        Given sessions where concept A appears 100x and concept B appears 5x,
        after analysis, A should have higher mastery signal than B.
        """
        domain = f"frequency-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "frequent-concept", "name": "Frequent Concept", "aliases": []},
                {"id": "rare-concept", "name": "Rare Concept", "aliases": []},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Create many messages mentioning frequent-concept
        messages = []
        for i in range(20):
            messages.append({
                "role": "user",
                "text": f"I implemented frequent concept variant {i}:\n```code\nfreq_{i}\n```"
            })
            messages.append({"role": "assistant", "text": "Good!"})

        # Only a few for rare-concept
        messages.append({"role": "user", "text": "What is rare concept?"})
        messages.append({"role": "assistant", "text": "Rare concept is..."})

        session = _create_session(isolated_env["claude_dir"], "-test-project", messages)
        result = analyzer.analyze_sessions([session], [domain])

        # Frequent concept has many positive signals, rare concept has question signal
        assert result[domain]["frequent-concept"]["score"] > result[domain]["rare-concept"]["score"]
        # Frequent should be capped at 0.8, rare should be 0.0 (from question)
        assert result[domain]["frequent-concept"]["score"] == 0.8
        assert result[domain]["rare-concept"]["score"] == 0.0


class TestDomainRelevance:
    """Tests for domain-specific concept detection."""

    def test_analyzer_rejects_irrelevant_domains(self, isolated_env):
        """
        User sessions about quantum ML should NOT boost web-frontend or devops concepts.
        Cross-domain contamination was a real bug.
        """
        # Create two domains: quantum-ml and web-frontend
        quantum_domain = f"quantum-ml-{_unique_id()}"
        web_domain = f"web-frontend-{_unique_id()}"

        quantum_graph = {
            "nodes": [
                {"id": "qaoa", "name": "QAOA", "aliases": ["quantum approximate optimization"]},
                {"id": "vqe", "name": "VQE", "aliases": ["variational quantum eigensolver"]},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], quantum_domain, quantum_graph)

        web_graph = {
            "nodes": [
                {"id": "react-hooks", "name": "React Hooks", "aliases": ["useState", "useEffect"]},
                {"id": "css-flexbox", "name": "CSS Flexbox", "aliases": ["flex container"]},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], web_domain, web_graph)

        # Session is purely about quantum computing
        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "I implemented QAOA:\n```python\nclass QAOA: pass\n```"},
                {"role": "assistant", "text": "Great QAOA implementation!"},
                {"role": "user", "text": "I built a VQE circuit:\n```python\nclass VQE: pass\n```"},
                {"role": "assistant", "text": "Nice VQE work!"},
            ]
        )

        result = analyzer.analyze_sessions([session], [quantum_domain, web_domain])

        # Quantum concepts should have signals
        assert len(result[quantum_domain]) >= 2
        assert result[quantum_domain]["qaoa"]["score"] > 0

        # Web concepts should have NO signals (not mentioned)
        assert len(result[web_domain]) == 0


class TestKnowledgeGraphWeightsMatch:
    """Tests to prevent hand-crafted weight bias."""

    def test_knowledge_graph_weights_match_session_data(self, isolated_env):
        """
        Load a domain graph and mock session data where:
        - QAOA appears 500x (20 user code submissions)
        - quantum-kernels appears 2x (as a question)

        After bootstrap analysis, QAOA mastery >> quantum-kernels mastery.
        This test would have caught the hand-crafted weight bug.
        """
        domain = f"weight-match-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "qaoa", "name": "QAOA", "aliases": [], "reuse_weight": 0.3},  # Hand-crafted weight
                {"id": "quantum-kernels", "name": "Quantum Kernels", "aliases": [], "reuse_weight": 0.9},  # Hand-crafted weight
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Create many sessions with QAOA mentions (code/assertions)
        messages = []
        for i in range(25):
            messages.append({
                "role": "user",
                "text": f"I implemented QAOA variant {i}:\n```python\nclass QAOA_{i}: pass\n```"
            })
            messages.append({"role": "assistant", "text": "Great!"})

        # Only questions about quantum-kernels
        messages.append({"role": "user", "text": "What are quantum kernels?"})
        messages.append({"role": "assistant", "text": "Quantum kernels are..."})

        session = _create_session(isolated_env["claude_dir"], "-test-project", messages)
        result = analyzer.analyze_sessions([session], [domain])

        # Despite quantum-kernels having higher reuse_weight (0.9 vs 0.3),
        # QAOA should have much higher mastery because user demonstrated it
        assert result[domain]["qaoa"]["score"] > result[domain]["quantum-kernels"]["score"]
        assert result[domain]["qaoa"]["score"] == 0.8  # Capped at max
        assert result[domain]["quantum-kernels"]["score"] == 0.0  # Question = weakness


class TestColdStart:
    """Tests for cold-start problem resolution."""

    def test_no_cold_start_after_analyze(self, isolated_env):
        """
        After running analyze on session data, knowledge_state.json should not be all zeros.
        At least one concept should have mastery > 0.0.
        """
        domain = f"cold-start-{_unique_id()}"
        graph = {
            "nodes": [
                {"id": "neural-networks", "name": "Neural Networks", "aliases": ["NN"], "reuse_weight": 0.5},
                {"id": "gradient-descent", "name": "Gradient Descent", "aliases": ["GD"], "reuse_weight": 0.5},
            ]
        }
        _write_graph(isolated_env["graphs_dir"], domain, graph)

        # Initialize domain (cold start - all zeros)
        knowledge_state.init_domain(domain)

        # Verify cold start state
        state_before = knowledge_state.load_state()
        for node_id, node_data in state_before["domains"][domain]["nodes"].items():
            assert node_data["mastery"] == 0.0, "Expected cold start with zero mastery"

        # Create session with user demonstrating knowledge
        session = _create_session(
            isolated_env["claude_dir"],
            "-test-project",
            [
                {"role": "user", "text": "I built a neural network:\n```python\nclass NN: pass\n```"},
                {"role": "assistant", "text": "Nice!"},
                {"role": "user", "text": "I implemented gradient descent:\n```python\ndef gd(): pass\n```"},
                {"role": "assistant", "text": "Great!"},
            ]
        )

        # Run analysis and apply
        analysis = analyzer.analyze_sessions([session], [domain])
        analyzer.apply_analysis_to_state(analysis)

        # Verify cold start problem is resolved
        state_after = knowledge_state.load_state()
        non_zero_count = sum(
            1 for node_data in state_after["domains"][domain]["nodes"].values()
            if node_data["mastery"] > 0.0
        )
        assert non_zero_count > 0, "Expected at least one concept with mastery > 0.0 after analysis"

        # Specifically check the concepts we demonstrated
        assert state_after["domains"][domain]["nodes"]["neural-networks"]["mastery"] > 0.0
        assert state_after["domains"][domain]["nodes"]["gradient-descent"]["mastery"] > 0.0
