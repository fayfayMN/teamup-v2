"""Core matching tests — run with: python -m unittest discover tests"""

import unittest

from teamup.match import Profile, pair_score, form_teams, summarize_team


def _p(id, skills, avail, commit=2):
    return Profile(id=id, name=id, skills=skills, availability=avail, commitment=commit)


class PairScoreTests(unittest.TestCase):
    def test_complementary_scores_higher_than_redundant(self):
        a = _p("a", ["Python / coding"], ["sat-day"])
        b_complement = _p("b", ["UI/UX design"], ["sat-day"])
        b_redundant = _p("c", ["Python / coding"], ["sat-day"])
        self.assertGreater(
            pair_score(a, b_complement)["score"],
            pair_score(a, b_redundant)["score"],
        )

    def test_no_shared_availability_flagged(self):
        a = _p("a", ["Python / coding"], ["mon-eve"])
        b = _p("b", ["UI/UX design"], ["sun-day"])
        self.assertIn("no shared availability", pair_score(a, b)["reasons"])

    def test_mismatched_commitment_flagged(self):
        a = _p("a", ["Python / coding"], ["sat-day"], commit=1)
        b = _p("b", ["UI/UX design"], ["sat-day"], commit=3)
        self.assertIn("mismatched stakes", pair_score(a, b)["reasons"])


class TeamFormationTests(unittest.TestCase):
    def test_partitions_whole_pool(self):
        pool = [_p(f"p{i}", ["Python / coding"], ["sat-day"]) for i in range(7)]
        teams = form_teams(pool, team_size=3)
        self.assertEqual(sum(len(t["members"]) for t in teams), 7)

    def test_missing_roles_detected(self):
        team = [_p(f"p{i}", ["Python / coding"], ["sat-day"]) for i in range(3)]
        summary = summarize_team(team)
        self.assertIn("Build", summary["covered_roles"])
        self.assertEqual(set(summary["missing_roles"]), {"Design", "Pitch", "Organize"})

    def test_full_coverage_has_no_gaps(self):
        team = [
            _p("a", ["Python / coding"], ["sat-day"]),
            _p("b", ["UI/UX design"], ["sat-day"]),
            _p("c", ["Pitching / presenting"], ["sat-day"]),
            _p("d", ["Project management"], ["sat-day"]),
        ]
        self.assertEqual(summarize_team(team)["missing_roles"], [])


if __name__ == "__main__":
    unittest.main()
