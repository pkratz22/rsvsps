from .context import RS_vs_PS

import unittest

class test_RS_vs_PS(unittest.TestCase):
    """Test cases for each aspect of code"""

    def test_determine_player_URL(self):
        # normal test
        self.assertEqual(RS_vs_PS.determine_player_URL("petrodr01"), "https://www.basketball-reference.com/players/p/petrodr01.html")
        
        # blank player_ID
        with self.assertRaises(IndexError):
            RS_vs_PS.determine_player_URL("")

        # player_ID with quotes
        self.assertEqual(RS_vs_PS.determine_player_URL("'Hello'"), "https://www.basketball-reference.com/players/'/'Hello'.html")
  
    
    def test_scrape_player_page(self):

        

if __name__ == "__main__":
    unittest.main()
