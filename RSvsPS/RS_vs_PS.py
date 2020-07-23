#imports
from bs4 import BeautifulSoup, SoupStrainer
import re
import requests
import operator
import sys
import pandas as pd


def determine_player_URL(player_ID):
    """Determine the Player's Page URL from player's ID"""
    if player_ID == "":
        raise SystemExit(IndexError)
    return "https://www.basketball-reference.com/players/{last_initial}/{ID}.html".format(
        last_initial=player_ID[0], ID=player_ID)


def scrape_player_page(player_URL):
    """Scrape Player Page for tables"""
    try:
        page_request = requests.get(player_URL)
        page_request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    player_page = page_request.text
    tables = SoupStrainer(id=[
        "per_game",
        "playoffs_per_game",
        "per_minute",
        "playoffs_per_minute",
        "per_poss",
        "playoffs_per_poss",
        "advanced",
        "playoffs_advanced",
    ])
    soup = BeautifulSoup(re.sub("<!--|-->", "", player_page),
                         "lxml",
                         parse_only=tables)
    return soup


def scrape_tables(soup, label, table_type):
    """Scrape the PerGameTables from the Player Page"""
    playoffs_qualifier = ""
    if label == "PS":
        playoffs_qualifier = "playoffs_"
    return soup.find(id=playoffs_qualifier + table_type)


def scraped_table_to_list(table):
    """Convert the scraped table to a multidimensional list"""
    return [[cell.text for cell in row.find_all(["th", "td"])]
            for row in table.find_all("tr")]


def scrape_column_headers(list):
    """Store column headers"""
    return list[0]


def remove_column_headers(list):
    """Remove column headers"""
    return list[1:]


def remove_blank_lines(list):
    """Remove blank lines"""
    return [year for year in list if year[0] != ""]


def adjustments_for_did_not_play_seasons(list):
    """Corrects formatting for seasons with Did Not Play"""
    list_extender = [""] * (len(list[0]) - 3)
    return [[*year, *list_extender] if "Did Not Play" in year[2] else year
            for year in list]


def label_RS_or_PS(list, label):
    """Adds label of either RS or PS"""
    return [[*year, label] for year in list]


def clean_table(soup, label, table_type):
    """Put functions for RS and PS into one"""
    table = scrape_tables(soup, label, table_type)
    if table is None:
        return
    list = scraped_table_to_list(table)
    column_headers = scrape_column_headers(list) + ["RSPS"
                                                    ] + ["diff_qualifier"]
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
    return [[*year, "1" + year[2]] if "season" in year[0] else
            [*year, "2"] if "Career" in year[0] else [*year, "0" + year[0]]
            for year in list]


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
        if ((list[row][0] != "")
                & (list[row + 1][0] != "")
                & (list[row][-1] != list[row + 1][-1])):
            list = list[:row + 1] + [[""] * len(list[0])] + list[row + 1:]
            upper_bound += 1
        row += 1
    return list


def add_qualifier_col_diff(list):
    """Add qualifier that will determine which rows to take difference from"""
    return [[*year, ""] for year in list]


def create_dataframe(list, column_headers):
    """Turns the list into a dataframe"""
    return pd.DataFrame(list, columns=column_headers)


def dataframe_data_types(dataframe, table_type):
    """Creates column headers for dataframe"""
    cols = []
    if (table_type == "per_game" or table_type == "per_minute"
            or table_type == "per_poss"):
        possible_columns = [
            "G",
            "GS",
            "MP",
            "FG",
            "FGA",
            "FG%",
            "3P",
            "3PA",
            "3P%",
            "2P",
            "2PA",
            "2P%",
            "eFG%",
            "FT",
            "FTA",
            "FT%",
            "ORB",
            "DRB",
            "TRB",
            "AST",
            "STL",
            "BLK",
            "TOV",
            "PF",
            "PTS",
            "ORtg",
            "DRtg",
        ]
        for column in possible_columns:
            if column in dataframe.columns:
                cols += [column]

    elif table_type == "advanced":
        possible_columns = [
            "G",
            "MP",
            "PER",
            "TS%",
            "3PAr",
            "FTr",
            "ORB%",
            "DRB%",
            "TRB%",
            "AST%",
            "STL%",
            "BLK%",
            "TOV%",
            "USG%",
            "OWS",
            "DWS",
            "WS",
            "WS/48",
            "OBPM",
            "DBPM",
            "BPM",
            "VORP",
        ]
        for column in possible_columns:
            if column in dataframe.columns:
                cols += [column]

    dataframe[cols] = dataframe[cols].apply(pd.to_numeric,
                                            errors="coerce",
                                            axis=1)
    return dataframe


def determine_rows_to_fill(dataframe):
    """Determine rows with RS (tot) and PS"""

    for row in range(len(dataframe.index)):
        if dataframe.loc[row, "RSPS"] == "":
            dataframe.loc[row, "diff_qualifier"] = "Diff"

    for row in range(len(dataframe.index)):
        if (dataframe.loc[row, "diff_qualifier"] != "Diff" and
            (row == 0 or dataframe.loc[row - 1, "diff_qualifier"] == "Diff")):
            dataframe.loc[row, "diff_qualifier"] = "First"

    for row in range(len(dataframe.index)):
        if (dataframe.loc[row, "diff_qualifier"] != "Diff"
                and (dataframe.loc[row + 1, "diff_qualifier"] == "Diff"
                     and dataframe.loc[row, "RSPS"] == "PS")):
            dataframe.loc[row, "diff_qualifier"] = "Last"

    return dataframe


def remove_extra_first_last(dataframe):
    """Get rid of extra firsts/lasts"""
    first_count = 0
    last_count = 0
    for row in range(len(dataframe.index)):
        if dataframe.loc[row, "diff_qualifier"] == "First":
            first_count += 1
        elif dataframe.loc[row, "diff_qualifier"] == "Last":
            last_count += 1
        elif dataframe.loc[
                row, "diff_qualifier"] == "Diff" and first_count != last_count:
            first_count = 0
            last_count = 0
            dataframe.loc[row, "diff_qualifier"] = ""
            temp_row = row - 1
            while temp_row >= 0 and dataframe.loc[temp_row,
                                                  "diff_qualifier"] != "Diff":
                dataframe.loc[temp_row, "diff_qualifier"] = ""
                temp_row -= 1
    return dataframe


def get_differences(dataframe):
    """Calculate differences between RS and PS"""
    diff_columns = [
        "MP", "FG", "FGA", "FG%", "3P", "3PA", "3P%", "2P", "2PA", "2P%",
        "eFG%", "FT", "FTA", "FT%", "ORB", "DRB", "TRB", "AST", "STL", "BLK",
        "TOV", "PF", "PTS", "ORtg", "DRtg", "PER", "TS%", "3PAr", "FTr",
        "ORB%", "DRB%", "TRB%", "AST%", "STL%", "BLK%", "TOV%", "USG%", "OWS",
        "DWS", "WS", "WS/48", "OBPM", "DBPM", "BPM", "VORP"
    ]
    first = []
    last = []
    for row in range(len(dataframe.index)):

        if dataframe.loc[row, "diff_qualifier"] == "First":
            for col in diff_columns:
                if col in dataframe:
                    first.append(dataframe.loc[row, col])

        elif dataframe.loc[row, "diff_qualifier"] == "Last":
            for col in diff_columns:
                if col in dataframe:
                    last.append(dataframe.loc[row, col])

        elif dataframe.loc[row, "diff_qualifier"] == "Diff":
            counter = 0
            for col in diff_columns:
                if col in dataframe:
                    dataframe.loc[row, col] =  last[counter] - first[counter]
                    counter += 1
            first = []
            last = []

    return dataframe


def remove_diff_qualifier_column(dataframe):
    """Remove diff_qualifier column"""
    return dataframe.iloc[:, :-1]


def player_single_table_type(player_page, table_type):
    RS = clean_table(player_page, "RS", table_type)
    PS = clean_table(player_page, "PS", table_type)
    if (RS is None) & (PS is None):
        return pd.DataFrame()
    combined = combine_RS_and_PS(RS, PS)
    column_headers = scrape_column_headers(combined)
    combined = remove_column_headers(combined)
    combined = add_sorting_qualifier(combined)
    combined = sort_list(combined)
    combined = add_blank_lines(combined)
    combined = remove_sorting_column(combined)
    combined = add_qualifier_col_diff(combined)
    combined = create_dataframe(combined, column_headers)
    combined = dataframe_data_types(combined, table_type)
    combined = determine_rows_to_fill(combined)
    combined = remove_extra_first_last(combined)
    combined = get_differences(combined)
    combined = remove_diff_qualifier_column(combined)

    return combined


def main(player_ID):
    player_URL = determine_player_URL(player_ID)
    player_page = scrape_player_page(player_URL)

    per_game = player_single_table_type(player_page, "per_game")
    per_minute = player_single_table_type(player_page, "per_minute")
    per_poss = player_single_table_type(player_page, "per_poss")
    advanced = player_single_table_type(player_page, "advanced")

    writer = pd.ExcelWriter("{player}.xlsx".format(player = player_ID), engine = "xlsxwriter")

    per_game.to_excel(writer, sheet_name = "per_game")
    per_minute.to_excel(writer, sheet_name = "per_minute")
    per_poss.to_excel(writer, sheet_name = "per_poss")
    advanced.to_excel(writer, sheet_name = "advanced")

    writer.save()

    return writer


if __name__ == "__main__":
    player_ID = input("Enter playerID: ")
    main(player_ID)
