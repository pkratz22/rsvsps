# imports
from bs4 import BeautifulSoup, SoupStrainer, Comment
import re
import requests
import operator
import sys

# profiling imports
import cProfile
import pstats
import io


def profile(fnc):
    """A decorator that uses cProfile to profile a function"""

    def inner(*args, **kwargs):

        pr = cProfile.Profile()
        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = "cumulative"
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return inner


def determine_player_URL(player_ID):
    """Determine the Player's Page URL from player's ID"""
    player_URL = (
        "https://www.basketball-reference.com/players/"
        + player_ID[0]
        + "/"
        + player_ID
        + ".html"
    )
    return player_URL


def scrape_player_page(player_URL):
    """Scrape Player Page for tables"""
    try:
        page_request = requests.get(player_URL)
        page_request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    player_page = page_request.text
    tables = SoupStrainer("table")
    soup = BeautifulSoup(re.sub("<!--|-->", "", player_page), "lxml", parse_only=tables)
    return soup


def scrape_per_game_tables(soup, label, table_type):
    """Scrape the PerGameTables from the Player Page"""
    playoffs_qualifier = ""
    if label == "PS":
        playoffs_qualifier = "playoffs_"
    table = soup.find(id=playoffs_qualifier + table_type)
    return table


def scraped_table_to_list(table):
    """Convert the scraped table to a multidimensional list"""
    return [
        [cell.text for cell in row.find_all(["th", "td"])]
        for row in table.find_all("tr")
    ]


def scrape_column_headers(list):
    """Store column headers"""
    column_headers = []
    if list:
        column_headers = list[0]
    return column_headers


def remove_column_headers(list):
    """Remove column headers"""
    if list:
        del list[0]
    return list


def remove_blank_lines(list):
    """Remove blank lines"""
    for year in list:
        if year[0] == "":
            list.remove(year)
    return list


def adjustments_for_did_not_play_seasons(list):
    """Corrects formatting for seasons with Did Not Play"""
    list_extender = [""] * 27
    for year in list:
        if "Did Not Play" in year[2]:
            year.extend(list_extender)
    return list


def label_RS_or_PS(list, label):
    """Adds label of either RS or PS"""
    for year in list:
        year.extend([label])
    return list


def clean_table(soup, label, table_type):
    """Put functions for RS and PS into one"""
    table = scrape_per_game_tables(soup, label, table_type)
    if table is None:
        return
    list = scraped_table_to_list(table)
    column_headers = scrape_column_headers(list)
    list = remove_column_headers(list)
    list = remove_blank_lines(list)
    list = adjustments_for_did_not_play_seasons(list)
    list = label_RS_or_PS(list, label)
    if label == "RS":
        list = [column_headers] + list
    return list


def combine_RS_and_PS(RS, PS):
    """Combine Regular Season and Post-Season Data into one table"""
    total = []
    if RS is not None:
        total += RS
    if PS is not None:
        total += PS
    return total


def add_sorting_qualifier(list):
    """Add an element to each row that can be used to properly sort"""
    for year in list:
        if "season" in year[0]:
            year.insert(len(year), "1" + year[2])
        elif "Career" in year[0]:
            year.insert(len(year), "2")
        else:
            year.insert(len(year), "0" + year[0])
    return list


def sort_list(list):
    """Sort list based on qualifer"""
    return sorted(list, key=lambda x: x[-1])


def remove_sorting_column(list):
    """Remove sorting qualifier column"""
    for entry in list:
        del entry[-1]
    return list


def add_blank_lines(list):
    """Add blank lines that will store differences"""
    upper_bound = len(list)-1
    row = 0
    while row < upper_bound:
        if(list[row][0]!="") & (list[row+1][0]!="") & (list[row][-1] != list[row+1][-1]):
            list = list[:row+1] + [[""]*len(list[0])] + list[row+1:]
            upper_bound +=1
        row += 1
    return list
    

def player_single_table_type(player_page, table_type):
    RS = clean_table(player_page, "RS", table_type)
    PS = clean_table(player_page, "PS", table_type)
    combined = combine_RS_and_PS(RS, PS)
    column_headers = scrape_column_headers(combined)
    combined = remove_column_headers(combined)
    combined = add_sorting_qualifier(combined)
    combined = sort_list(combined)
    combined = combined + [[""]*len(combined[0])]
    combined = add_blank_lines(combined)
    combined = remove_sorting_column(combined)
    return [column_headers] + combined


def main(player_ID):
    player_URL = determine_player_URL(player_ID)
    player_page = scrape_player_page(player_URL)
    per_game = player_single_table_type(player_page, "per_game")
    per_minute = player_single_table_type(player_page, "per_minute")
    per_poss = player_single_table_type(player_page, "per_poss")
    advanced = player_single_table_type(player_page, "advanced")
    all_tables = [per_game, per_minute, per_poss, advanced]
    return all_tables


if __name__ == "__main__":
    player_ID = "cousybo01"
    print(main(player_ID))
