from .. import rsvsps

import requests

import unittest

class test_RS_vs_PS(unittest.TestCase):
    """Test cases for each aspect of code"""

    def test_determine_player_URL(self):
        # normal test
        self.assertEqual(rsvsps.determine_player_url("petrodr01"), "https://www.basketball-reference.com/players/p/petrodr01.html")

        # player_ID with quotes
        self.assertEqual(rsvsps.determine_player_url("'Hello'"), "https://www.basketball-reference.com/players/'/'Hello'.html")

        # blank player_ID
        with self.assertRaises(SystemExit):
            rsvsps.determine_player_url("")

    
    def test_scrape_player_page(self):
        # normal test
        self.assertIsNotNone(rsvsps.scrape_player_page("https://www.basketball-reference.com/players/p/petrodr01.html"))

        # player missing some tables
        self.assertIsNotNone(rsvsps.scrape_player_page("https://www.basketball-reference.com/players/c/cousybo01.html"))

        # player page doesn't exist
        with self.assertRaises(SystemExit):
             rsvsps.scrape_player_page("https://www.basketball-reference.com/players/3")


if __name__ == "__main__":
    unittest.main()
