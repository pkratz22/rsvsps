import csv
import unittest
from .context import RS_vs_PS


class test_RS_vs_PS(unittest.TestCase):
    """General test cases for entire process"""
    
    def test_main(self):
        with open("test_cases.txt") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            for row in csv_reader:
                print(row)
                self.assertIsNotNone(RS_vs_PS.main(row[0]))

    
if __name__ == "__main__":
    unittest.main()
