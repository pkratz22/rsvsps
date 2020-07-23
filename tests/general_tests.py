import csv
import unittest
from .context import RS_vs_PS


class test_RS_vs_PS(unittest.TestCase):
    """General test cases for entire process"""
    def test_normal(self):     
        # normal test
        self.assertIsNotNone(RS_vs_PS.main('jamesle01'))
        self.assertIsNotNone(RS_vs_PS.main('abdulka01'))
    
    def test_multiple_team_one_season(self):
        # Player that played on multiple teams in one season
        self.assertIsNotNone(RS_vs_PS.main('petrodr01'))

    def test_has_season_with_PS_no_RS(self):
        # played in the post-season but not regular season for one season
        self.assertIsNotNone(RS_vs_PS.main('mcgratr01'))

    def test_never_made_playoffs(self):
        # player that has not reached the playoffs
        self.assertIsNotNone(RS_vs_PS.main('grahade01'))

    def test_multiple_seasons_overseas(self):
        # multiple seasons not in league
        self.assertIsNotNone(RS_vs_PS.main('tuckepj01'))

    def test_played_in_ABA(self):
        # played in the ABA
        self.assertIsNotNone(RS_vs_PS.main('ervinju01'))

    def test_less_stats_during_era(self):
        # retired then returned + less stats available during era
        self.assertIsNotNone(RS_vs_PS.main('cousybo01'))

    def test_stats_available_only_late_career(self):
        # certain stats available during only part of career
        self.assertIsNotNone(RS_vs_PS.main('ellisjo01'))

    def test_three_point_line_added_mid_career(self):
        # 3 point line added mid career
        self.assertIsNotNone(RS_vs_PS.main('furlote01'))

    
if __name__ == "__main__":
    unittest.main()
