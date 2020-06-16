# imports
from bs4 import BeautifulSoup, SoupStrainer
import re
import requests
import operator
import sys


def determine_player_URL(player_ID):
    """Determine the Player's Page URL from player's ID"""
    return "https://www.basketball-reference.com/players/{last_initial}/{ID}.html".format(
        last_initial=player_ID[0], ID=player_ID
    )


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


def scrape_tables(soup, label, table_type):
    """Scrape the PerGameTables from the Player Page"""
    playoffs_qualifier = ""
    if label == "PS":
        playoffs_qualifier = "playoffs_"
    return soup.find(id=playoffs_qualifier + table_type)


def scraped_table_to_list(table):
    """Convert the scraped table to a multidimensional list"""
    return [
        [cell.text for cell in row.find_all(["th", "td"])]
        for row in table.find_all("tr")
    ]


def scrape_column_headers(list):
    """Store column headers"""
    column_headers = list[0]
    return column_headers


def remove_column_headers(list):
    """Remove column headers"""
    return list[1:]


def remove_blank_lines(list):
    """Remove blank lines"""
    return [year for year in list if year[0] != ""]


def adjustments_for_did_not_play_seasons(list):
    """Corrects formatting for seasons with Did Not Play"""
    list_extender = [""] * len(list[0])
    return [[*year, *list_extender] if "Did Not Play" in year[2] else year for year in list]


def label_RS_or_PS(list, label):
    """Adds label of either RS or PS"""
    return [[*year, label] for year in list]


def clean_table(soup, label, table_type):
    """Put functions for RS and PS into one"""
    table = scrape_tables(soup, label, table_type)
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
    return [
        [*year, "1" + year[2]]
        if "season" in year[0]
        else [*year, "2"]
        if "Career" in year[0]
        else [*year, "0" + year[0]]
        for year in list
    ]


def sort_list(list):
    """Sort list based on qualifer"""
    return sorted(list, key=lambda x: x[-1])


def remove_sorting_column(list):
    """Remove sorting qualifier column"""
    return [entry[:-1] for entry in list]


def add_blank_lines(list):
    """Add blank lines that will store differences"""
    list = list + [[""] * len(list[0])]
    upper_bound = len(list) - 1
    row = 0
    while row < upper_bound:
        if (
            (list[row][0] != "")
            & (list[row + 1][0] != "")
            & (list[row][-1] != list[row + 1][-1])
        ):
            list = list[: row + 1] + [[""] * len(list[0])] + list[row + 1 :]
            upper_bound += 1
        row += 1
    return list


def player_single_table_type(player_page, table_type):
    RS = clean_table(player_page, "RS", table_type)
    PS = clean_table(player_page, "PS", table_type)
    combined = combine_RS_and_PS(RS, PS)
    if combined == []:
        return combined
    column_headers = scrape_column_headers(combined)
    combined = remove_column_headers(combined)
    combined = add_sorting_qualifier(combined)
    combined = sort_list(combined)
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
    player_ID = "melchbi01"
    print(main(player_ID))
