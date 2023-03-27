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
        

if __name__ == "__main__":
    unittest.main()
