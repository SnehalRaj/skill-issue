"""
Smoke test: the test that would have caught today's SKILL.md bundling bug.

This test actually runs the installed CLI and checks real output.
No mocking the file system — this must catch packaging issues.
"""

import os
import subprocess
import tempfile
from pathlib import Path


def test_init_creates_profile_and_injects_skill_md():
    """
    pip install → skill-issue init --claude → CLAUDE.md has real SKILL.md content.

    This is the critical path that broke in v1.0.0 and v1.1.0:
    - SKILL.md wasn't bundled in the pip package
    - Path resolution only worked in dev mode
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up isolated home directory for the test
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        # Working directory for CLAUDE.md injection
        workdir = Path(tmpdir) / "project"
        workdir.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        # Run: skill-issue init --name test --domain algorithms
        result = subprocess.run(
            ["skill-issue", "init", "--name", "testuser", "--domains", "algorithms"],
            cwd=str(workdir),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"init failed: {result.stderr}"

        # Verify profile was created
        profile_path = fake_home / ".skill-issue" / "profile.json"
        assert profile_path.exists(), "profile.json not created"

        # Run: skill-issue init --claude (inject into CLAUDE.md)
        result = subprocess.run(
            ["skill-issue", "init", "--claude"],
            cwd=str(workdir),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"init --claude failed: {result.stderr}"

        # CRITICAL ASSERTIONS — what would have caught the bug
        claude_md = workdir / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md not created"

        content = claude_md.read_text()

        # Must contain actual SKILL.md content, not just a comment marker
        assert len(content) > 500, (
            f"CLAUDE.md too short ({len(content)} chars) — "
            "likely only contains marker, not SKILL.md content"
        )

        # Must contain the SKILL.md frontmatter
        assert "name: skill-issue" in content, (
            "CLAUDE.md missing 'name: skill-issue' — SKILL.md not injected properly"
        )

        # Must contain actual skill content (not just a placeholder comment)
        assert "challenge" in content.lower(), (
            "CLAUDE.md missing challenge content — SKILL.md not bundled"
        )


def test_init_print_outputs_skill_content():
    """skill-issue init --print should output actual SKILL.md content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()
        (fake_home / ".skill-issue").mkdir()  # Pre-create so init skips profile creation

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        result = subprocess.run(
            ["skill-issue", "init", "--print"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # --print should output SKILL.md content
        output = result.stdout
        assert len(output) > 500, f"--print output too short ({len(output)} chars)"
        assert "skill-issue" in output.lower(), "--print missing skill-issue content"


def test_stats_works_after_init():
    """skill-issue stats should work after init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_home = Path(tmpdir) / "home"
        fake_home.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(fake_home)

        # Init first
        subprocess.run(
            ["skill-issue", "init", "--name", "statstest", "--domains", "algorithms"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            timeout=30,
        )

        # Then stats
        result = subprocess.run(
            ["skill-issue", "stats"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, f"stats failed: {result.stderr}"
        assert "statstest" in result.stdout, "stats output missing username"
        assert "Apprentice" in result.stdout, "stats output missing level"
