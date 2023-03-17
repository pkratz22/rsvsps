"""Test overall script for players"""

import unittest
from rsvsps import rsvsps
from scraper import player_page_scraper


class TestRsvsps(unittest.TestCase):
    """General test cases for entire process"""

    def test_normal(self):
        """Test players with normal careers"""
        # normal test
        self.assertIsNotNone(rsvsps.main('jamesle01'))
        self.assertIsNotNone(rsvsps.main('abdulka01'))

    def test_multiple_team_one_season(self):
        """Test players who switched teams mid-season"""
        # Player that played on multiple teams in one season
        self.assertIsNotNone(rsvsps.main('petrodr01'))

    def test_has_season_with_ps_no_rs(self):
        """Test players who had PS but no RS for a season"""
        # played in the post-season but not regular season for one season
        self.assertIsNotNone(rsvsps.main('mcgratr01'))

    def test_never_made_playoffs(self):
        """Test players who never made playoffs"""
        # player that has not reached the playoffs
        self.assertIsNotNone(rsvsps.main('grahade01'))

    def test_multiple_seasons_overseas(self):
        """Test players who had multiple seasons overseas"""
        # multiple seasons not in league
        self.assertIsNotNone(rsvsps.main('tuckepj01'))

    def test_played_in_aba(self):
        """Test players who played in the ABA"""
        # played in the ABA
        self.assertIsNotNone(rsvsps.main('ervinju01'))

    def test_less_stats_during_era(self):
        """Test players who had less stats during era"""
        # retired then returned + less stats available during era
        self.assertIsNotNone(rsvsps.main('cousybo01'))

    def test_stats_available_only_late_career(self):
        """Test players who had more stats late career"""
        # certain stats available during only part of career
        self.assertIsNotNone(rsvsps.main('ellisjo01'))

    def test_three_point_line_added_mid_career(self):
        """Test players with three point line late career"""
        # 3 point line added mid career
        self.assertIsNotNone(rsvsps.main('furlote01'))

    def test_suite(self):
        self.test_normal


if __name__ == "__main__":
    unittest.main()
