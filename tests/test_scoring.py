"""
Tests for scoring and XP calculation logic.
"""

from skill_issue.update_score import calculate_xp, get_overall_level


class TestCalculateXP:
    """Tests for calculate_xp function."""

    def test_score_2_practitioner_streak_3_no_hint(self):
        """Score=2, difficulty=Practitioner, streak=3, hint=False."""
        # base=12, diff_mult=1.5, streak_mult=1+3*0.15=1.45, hint=1.0
        # 12 * 1.5 * 1.45 * 1.0 = 26.1 → 26
        xp = calculate_xp(score=2, difficulty="Practitioner", streak=3, hint_used=False)
        assert xp == 26

    def test_score_0_always_returns_0(self):
        """Score=0 should always return 0 XP regardless of other factors."""
        assert calculate_xp(score=0, difficulty="Master", streak=10, hint_used=False) == 0
        assert calculate_xp(score=0, difficulty="Apprentice", streak=0, hint_used=True) == 0

    def test_hint_applies_penalty(self):
        """hint_used=True should apply 0.75x penalty."""
        xp_no_hint = calculate_xp(score=3, difficulty="Apprentice", streak=0, hint_used=False)
        xp_with_hint = calculate_xp(score=3, difficulty="Apprentice", streak=0, hint_used=True)

        # base=20, diff=1.0, streak=1.0
        # no hint: 20 * 1.0 * 1.0 * 1.0 = 20
        # hint: 20 * 1.0 * 1.0 * 0.75 = 15
        assert xp_no_hint == 20
        assert xp_with_hint == 15
        assert xp_with_hint == round(xp_no_hint * 0.75)

    def test_streak_multiplier_caps_at_2_5(self):
        """Streak multiplier should cap at 2.5x regardless of streak length."""
        # streak=10: 1 + 10*0.15 = 2.5 (exactly at cap)
        xp_10 = calculate_xp(score=2, difficulty="Apprentice", streak=10, hint_used=False)

        # streak=100: would be 1 + 100*0.15 = 16, but capped at 2.5
        xp_100 = calculate_xp(score=2, difficulty="Apprentice", streak=100, hint_used=False)

        # Both should be identical: 12 * 1.0 * 2.5 = 30
        assert xp_10 == 30
        assert xp_100 == 30

    def test_all_difficulty_multipliers(self):
        """Verify difficulty multipliers: Apprentice=1.0, Practitioner=1.5, Expert=2.0, Master=3.0."""
        # Use score=2 (base=12), streak=0 (mult=1.0), no hint
        assert calculate_xp(2, "Apprentice", 0, False) == 12   # 12 * 1.0
        assert calculate_xp(2, "Practitioner", 0, False) == 18  # 12 * 1.5
        assert calculate_xp(2, "Expert", 0, False) == 24       # 12 * 2.0
        assert calculate_xp(2, "Master", 0, False) == 36       # 12 * 3.0


class TestGetOverallLevel:
    """Tests for get_overall_level function."""

    def test_0_xp_is_apprentice(self):
        """0 XP should be Apprentice."""
        assert get_overall_level(0) == "Apprentice"

    def test_500_xp_is_practitioner(self):
        """500 XP should be Practitioner."""
        assert get_overall_level(500) == "Practitioner"

    def test_2000_xp_is_expert(self):
        """2000 XP should be Expert."""
        assert get_overall_level(2000) == "Expert"

    def test_5000_xp_is_master(self):
        """5000 XP should be Master."""
        assert get_overall_level(5000) == "Master"

    def test_threshold_boundaries(self):
        """Test values just below thresholds."""
        assert get_overall_level(499) == "Apprentice"
        assert get_overall_level(1999) == "Practitioner"
        assert get_overall_level(4999) == "Expert"
