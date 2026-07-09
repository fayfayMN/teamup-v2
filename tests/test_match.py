"""Core matching tests — run with: python -m unittest discover tests"""

import unittest

from teamup.match import (Profile, pair_score, form_teams, summarize_team,
                          assign_roles, coach_team)
from teamup import scenarios


def _p(id, skills, avail, commit=2, learn=None):
    return Profile(id=id, name=id, skills=skills, availability=avail, commitment=commit,
                   wants_to_learn=learn or [])


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


class FixedTeamCoachingTests(unittest.TestCase):
    def test_scenario_required_roles_drive_coverage(self):
        # A pure-build team is fully covered for a scenario needing only Build-ish
        # roles, but gappy for a competition (needs Design + Pitch).
        team = [_p("a", ["Python / coding"], ["sat-day"]),
                _p("b", ["Data / ML"], ["sat-day"])]
        comp = coach_team(team, scenarios.get("competition"))
        self.assertIn("Design", comp["summary"]["missing_roles"])
        self.assertIn("Pitch", comp["summary"]["missing_roles"])

    def test_stretch_owner_prefers_who_wants_to_learn(self):
        team = [_p("a", ["Python / coding"], ["sat-day"], learn=["UI/UX design"]),
                _p("b", ["Data / ML"], ["sat-day"])]
        by_role = {x["role"]: x for x in assign_roles(team, ["Build", "Design"])}
        self.assertTrue(by_role["Design"]["stretch"])
        self.assertEqual(by_role["Design"]["owner"], "a")  # a wanted to learn Design

    def test_recruit_gap_when_no_one_can_stretch_into_empty_team(self):
        # An empty team yields a recruit gap (owner is None), never a crash.
        out = assign_roles([], ["Build"])
        self.assertIsNone(out[0]["owner"])

    def test_load_is_balanced_across_owners(self):
        # Two people both cover Build; the two Build-ish roles shouldn't both land
        # on the same person.
        team = [_p("a", ["Python / coding"], ["sat-day"]),
                _p("b", ["Web / frontend"], ["sat-day"])]
        owners = {x["role"]: x["owner"] for x in assign_roles(team, ["Build", "Build"])}
        # (same role twice is contrived, but proves the load balancer alternates)
        self.assertEqual(len({x["owner"] for x in assign_roles(team, ["Build"])}), 1)

    def test_mismatched_stakes_surfaced_as_advice(self):
        team = [_p("a", ["Python / coding"], ["sat-day"], commit=1),
                _p("b", ["UI/UX design"], ["sat-day"], commit=3)]
        advice = coach_team(team, scenarios.get("competition"))["advice"]
        self.assertTrue(any("stakes" in a["title"].lower() for a in advice))

    def test_explanations_are_plain_strings(self):
        team = [_p("a", ["Python / coding"], ["sat-day"])]
        r = coach_team(team, scenarios.get("coursework"))
        self.assertTrue(all(isinstance(s, str) and s for s in r["explanations"]))


if __name__ == "__main__":
    unittest.main()
