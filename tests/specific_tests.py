from .context import RS_vs_PS

import unittest

class test_RS_vs_PS(unittest.TestCase):
    """Test cases for each aspect of code"""

    def test_determine_player_URL(self):
        self.assertEqual(RS_vs_PS.determine_player_URL("petrodr01"), "https://www.basketball-reference.com/players/p/petrodr01.html")


if __name__ == "__main__":
    unittest.main()