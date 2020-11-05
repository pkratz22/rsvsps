"""Test rsvsps file"""

import unittest

from .. import rsvsps


class TestRSvsPS(unittest.TestCase):
    """Test cases for each aspect of code"""

    def test_determine_player_url(self):
        """Test function to determine player URL"""
        # normal test
        self.assertEqual(
            rsvsps.determine_player_url("petrodr01"),
            "https://www.basketball-reference.com/players/p/petrodr01.html")

        # player_ID with quotes
        self.assertEqual(
            rsvsps.determine_player_url("'Hello'"),
            "https://www.basketball-reference.com/players/'/'Hello'.html")

        # blank player_ID
        with self.assertRaises(SystemExit):
            rsvsps.determine_player_url("")

    def test_scrape_player_page(self):
        """Test scrape player page functionality"""
        # normal test
        self.assertIsNotNone(rsvsps.scrape_player_page(
            "https://www.basketball-reference.com/players/p/petrodr01.html"))

        # player missing some tables
        self.assertIsNotNone(rsvsps.scrape_player_page(
            "https://www.basketball-reference.com/players/c/cousybo01.html"))

        # player page doesn't exist
        with self.assertRaises(SystemExit):
            rsvsps.scrape_player_page(
                "https://www.basketball-reference.com/players/3")


if __name__ == "__main__":
    unittest.main()
