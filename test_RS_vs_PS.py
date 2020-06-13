import csv
import unittest
import RS_vs_PS


class TestRSVSPS(unittest.TestCase):

    def test_main(self):
        
        with open("test_cases.txt") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                print(row)
                self.assertIsNotNone(RS_vs_PS.main(row[0]))

    def test_scrape_player_page(self):
        self.assertRaises(ValueError, RS_vs_PS.scrape_player_page, '')

if __name__ == "__main__":
    unittest.main()
