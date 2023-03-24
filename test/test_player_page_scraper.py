"""Test rsvsps file"""

import time
import unittest
from scrapers import player_page_scraper


class TestRSvsPS(unittest.TestCase):
    """Test cases for each aspect of code"""

    def tearDown(self) -> None:
        time.sleep(60)

    def test_scrape_player_page(self):
        """Test scrape player page functionality"""
        # normal test
        self.assertIsNotNone(player_page_scraper.scrape_player_page(
            "https://www.basketball-reference.com/players/p/petrodr01.html"))

        # player missing some tables
        self.assertIsNotNone(player_page_scraper.scrape_player_page(
            "https://www.basketball-reference.com/players/c/cousybo01.html"))

        # player page doesn't exist
        with self.assertRaises(SystemExit):
            player_page_scraper.scrape_player_page(
                "https://www.basketball-reference.com/players/3")
