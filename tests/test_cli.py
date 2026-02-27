"""
Tests for CLI commands.

These tests run actual CLI commands via subprocess to verify integration.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path


def test_init_creates_profile():
    """skill-issue init --domain algorithms creates ~/.skill-issue/profile.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        result = subprocess.run(
            ["skill-issue", "init", "--name", "clitest", "--domains", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"init failed: {result.stderr}"

        profile_path = fake_home / ".skill-issue" / "profile.json"
        assert profile_path.exists(), "profile.json not created"

        profile = json.loads(profile_path.read_text())
        assert profile["username"] == "clitest"
        assert profile["overall_level"] == "Apprentice"
        assert profile["total_xp"] == 0


def test_stats_works_after_init():
    """skill-issue stats works after init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        # Init
        subprocess.run(
            ["skill-issue", "init", "--name", "statsuser", "--domains", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            timeout=30,
        )

        # Stats
        result = subprocess.run(
            ["skill-issue", "stats"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"stats failed: {result.stderr}"
        assert "statsuser" in result.stdout
        assert "Apprentice" in result.stdout
        assert "XP" in result.stdout or "0" in result.stdout


def test_graph_domains_lists_all_domains():
    """skill-issue graph domains lists all 9 domains."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        result = subprocess.run(
            ["skill-issue", "graph", "domains"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"graph domains failed: {result.stderr}"

        # Should list all 9 domains
        expected_domains = [
            "algorithms",
            "backend-systems",
            "computer-science",
            "design-systems",
            "devops",
            "machine-learning",
            "mobile",
            "quantum-ml",
            "web-frontend",
        ]

        for domain in expected_domains:
            assert domain in result.stdout, f"Missing domain: {domain}"


def test_graph_init_creates_knowledge_state():
    """skill-issue graph init --domain algorithms creates knowledge_state.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        # Create profile first
        subprocess.run(
            ["skill-issue", "init", "--name", "graphtest", "--domains", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            timeout=30,
        )

        # Init knowledge graph
        result = subprocess.run(
            ["skill-issue", "graph", "init", "--domain", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"graph init failed: {result.stderr}"

        ks_path = fake_home / ".skill-issue" / "knowledge_state.json"
        assert ks_path.exists(), "knowledge_state.json not created"

        ks = json.loads(ks_path.read_text())
        assert "domains" in ks
        assert "algorithms" in ks["domains"]
        assert "nodes" in ks["domains"]["algorithms"]
        # algorithms.json has 8 nodes
        assert len(ks["domains"]["algorithms"]["nodes"]) >= 8


def test_graph_show_works():
    """skill-issue graph show --domain algorithms produces ASCII output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        # Create profile and init graph
        subprocess.run(
            ["skill-issue", "init", "--name", "showtest", "--domains", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            timeout=30,
        )

        subprocess.run(
            ["skill-issue", "graph", "init", "--domain", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            timeout=30,
        )

        # Show graph
        result = subprocess.run(
            ["skill-issue", "graph", "show", "--domain", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"graph show failed: {result.stderr}"
        # Should contain ASCII progress bars
        assert "[" in result.stdout and "]" in result.stdout
        # Should mention algorithms domain
        assert "algorithms" in result.stdout.lower()
