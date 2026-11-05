"""Test rsvsps file"""

import time
import unittest

from rsvsps.scrapers import player_page_scraper


class TestRSvsPS(unittest.TestCase):
    """Test cases for each aspect of code"""

    def test_determine_player_url(self):
        """Test function to determine player URL"""
        # normal test
        self.assertEqual(
            player_page_scraper.determine_player_url("petrodr01"),
            "https://www.basketball-reference.com/players/p/petrodr01.html")

        # player_ID with quotes
        self.assertEqual(
            player_page_scraper.determine_player_url("'Hello'"),
            "https://www.basketball-reference.com/players/'/'Hello'.html")

        # blank player_ID
        with self.assertRaises(SystemExit):
            player_page_scraper.determine_player_url("")

    def test_adjustments_for_did_not_play_seasons_handles_short_rows(self):
        """DNP seasons can have fewer columns than the rest of the table."""
        rows = [
            ['Season', 'Age', 'Team', 'Lg', 'Pos'],
            ['1986-87', 'Did not play - other pro league (Yugoslavia) '],
            ['1989-90', '25', 'POR', 'NBA', 'SG'],
        ]

        adjusted = player_page_scraper.adjustments_for_did_not_play_seasons(rows)

        self.assertEqual(adjusted[1][0], '1986-87')
        self.assertEqual(adjusted[1][2], '')
        self.assertEqual(adjusted[2][2], 'POR')


if __name__ == "__main__":
    unittest.main()
