"""Create excel sheet comparing players Regular Seasons and Post-Seasons."""

import argparse

import pandas as pd
import requests
from bs4 import BeautifulSoup, SoupStrainer


def determine_player_url(player_id):
    """Determine the Player's Page URL from player's ID.

    Raises:
        SystemExit: index error if ID blank

    Args:
        player_id: inputted player ID

    Returns:
        URL for player based on ID
    """
    if not player_id:
        raise SystemExit(IndexError)
    base_url = 'https://www.basketball-reference.com/players/'
    return '{base}{last_initial}/{ID}.html'.format(
        base=base_url,
        last_initial=player_id[0],
        ID=player_id,
    )


def scrape_player_page(player_url):
    """Scrape Player Page for tables.

    Raises:
        SystemExit: HTTPError for player ID
    
    Args:
        player_url: URL to scrape

    Returns:
        soup of scraped page
    """
    try:
        page_request = requests.get(player_url)
        page_request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit from err
    player_page = page_request.text
    tables = SoupStrainer(id=[
        'per_game',
        'playoffs_per_game',
        'per_minute',
        'playoffs_per_minute',
        'per_poss',
        'playoffs_per_poss',
        'advanced',
        'playoffs_advanced',
    ])
    player_page = player_page.replace('<!--', '').replace('-->', '')

    soup = BeautifulSoup(player_page, 'lxml', parse_only=tables)
    return soup.contents


def scrape_tables(soup, label, table_type):
    """Scrape the PerGameTables from the Player Page.

    Args:
        soup: soup of player page
        label: regular season or post-season
        table_type: table type to scrape

    Returns:
        soup for table
    """
    qualifier_map = {'RS': '', 'PS': 'playoffs_'}
    for table in soup:
        if table.attrs['id'] == '{label}{tabletype}'.format(label=qualifier_map.get(label), tabletype=table_type):
            return table


def scraped_table_to_list(table):
    """Convert the scraped table to a multidimensional list.

    Args:
        table: table to scrape

    Returns:
        data scraped from soup of table
    """
    return [[cell.text for cell in row.find_all(['th', 'td'])] for row in table.find_all('tr')]


def scrape_column_headers(player_data_list):
    """Store column headers.

    Args:
        player_data_list: player data list

    Returns:
        headers for player data list
    """
    return player_data_list[0]


def remove_column_headers(player_data_list):
    """Remove column headers.

    Args:
        player_data_list: player data list

    Returns:
        player data list without column headers
    """
    return player_data_list[1:]


def remove_blank_lines(player_data_list):
    """Remove blank lines.

    Args:
        player_data_list: player data list

    Returns:
        list with blank lines removed
    """
    return [year for year in player_data_list if year[0] != '']


def adjustments_for_did_not_play_seasons(player_data_list):
    """Corrects formatting for seasons with Did Not Play.

    Args:
        player_data_list: player data list

    Returns:
        List with formatting for DNP seasons
    """
    list_extender = [''] * (len(player_data_list[0]) - 3)
    return [[*year, *list_extender] if 'Did Not Play' in year[2] else year for year in player_data_list]


def label_rs_or_ps(player_data_list, label):
    """Adds label of either RS or PS.

    Args:
        player_data_list: player data list
        label: RS or PS

    Returns:
        Labels data RS or PS
    """
    return [[*year, label] for year in player_data_list]


def clean_table(soup, label, table_type):
    """Put functions for RS and PS into one.

    Args:
        soup: soup for player page
        label: RS or PS to scrape
        table_type: type of table to scrape

    Returns:
        player data for label and table_type
    """
    table = scrape_tables(soup, label, table_type)
    if table is None:
        return None
    player_data_list = scraped_table_to_list(table)
    column_headers = scrape_column_headers(player_data_list) + ['RSPS'] + ['diff_qualifier']
    player_data_list = remove_column_headers(player_data_list)
    player_data_list = remove_blank_lines(player_data_list)
    player_data_list = adjustments_for_did_not_play_seasons(player_data_list)
    player_data_list = label_rs_or_ps(player_data_list, label)
    if label == 'RS':
        player_data_list = [column_headers] + player_data_list
    return player_data_list


def combine_rs_and_ps(regular_season, post_season):
    """Combine Regular Season and Post-Season Data into one table.

    Args:
        regular_season: player RS data for table type
        post_season: player PS data for table type

    Returns:
        combined RS and PS table
    """
    total = []
    if regular_season is not None:
        total += regular_season
    if post_season is not None:
        total += post_season
    return total


def add_sorting_qualifier(player_data_list):
    """Add an element to each row that can be used to properly sort.

    Args:
        player_data_list: player data list

    Returns:
        player data list with 'column' for a sorting qualifier
    """
    return [[*year, '1' + year[2]] if 'season' in year[0] else [*year, '2'] if 'Career' in year[0] else [*year, '0' + year[0]] for year in player_data_list]


def sort_list(player_data_list):
    """Sort list based on qualifer.

    Args:
        player_data_list: player data list

    Returns:
        player data list properly sorted
    """
    return sorted(player_data_list, key=lambda x: x[-1])


def remove_sorting_column(player_data_list):
    """Remove sorting qualifier column.

    Args:
        player_data_list: list with player data

    Returns:
        player data list with sorting column removed
    """
    return [entry[:-1] for entry in player_data_list]


def add_blank_lines(player_data_list):
    """Add blank lines that will store differences.

    Args:
        player_data_list: player data list

    Returns:
        player data list with blank rows for differences
    """
    length_appended = max([len(row) for row in player_data_list])
    player_data_list = player_data_list + [[''] * length_appended]
    upper_bound = len(player_data_list) - 1
    row = 0
    while row < upper_bound:
        if ((player_data_list[row][0] != '') & (player_data_list[row + 1][0] != '') & (player_data_list[row][-1] != player_data_list[row + 1][-1])):
            player_data_list = player_data_list[:row + 1] + [[''] * length_appended] + player_data_list[row + 1:]
            upper_bound += 1
        row += 1
    return player_data_list


def add_qualifier_col_diff(player_data_list):
    """Add qualifier that will determine which rows to take difference from.

    Args:
        player_data_list: list with player data

    Returns:
        player data list with qualifier
    """
    return [[*year, ''] for year in player_data_list]


def create_dataframe(player_data_list, column_headers):
    """Turns the list into a dataframe.

    Args:
        player_data_list: list with player data
        column_headers: column headers for table type

    Returns:
        player info as dataframe
    """
    return pd.DataFrame(player_data_list, columns=column_headers)


def dataframe_data_types(dataframe, table_type):
    """Create column headers for dataframe.

    Args:
        dataframe: player dataframe
        table_type: type of table df is for

    Returns:
        Creates column headers for dataframe
    """
    cols = []
    if (table_type in {'per_game', 'per_minute', 'per_poss'}):
        possible_columns = [
            'G',
            'GS',
            'MP',
            'FG',
            'FGA',
            'FG%',
            '3P',
            '3PA',
            '3P%',
            '2P',
            '2PA',
            '2P%',
            'eFG%',
            'FT',
            'FTA',
            'FT%',
            'ORB',
            'DRB',
            'TRB',
            'AST',
            'STL',
            'BLK',
            'TOV',
            'PF',
            'PTS',
            'ORtg',
            'DRtg',
        ]
        for column in possible_columns:
            if column in dataframe.columns:
                cols += [column]

    elif table_type == 'advanced':
        possible_columns = [
            'G',
            'MP',
            'PER',
            'TS%',
            '3PAr',
            'FTr',
            'ORB%',
            'DRB%',
            'TRB%',
            'AST%',
            'STL%',
            'BLK%',
            'TOV%',
            'USG%',
            'OWS',
            'DWS',
            'WS',
            'WS/48',
            'OBPM',
            'DBPM',
            'BPM',
            'VORP',
        ]
        for column in possible_columns:
            if column in dataframe.columns:
                cols += [column]

    dataframe[cols] = dataframe[cols].apply(
        pd.to_numeric,
        errors='coerce',
        axis=1,
    )
    return dataframe


def determine_rows_to_fill(dataframe):
    """Determine rows with RS (tot) and PS.

    Args:
        dataframe: dataframe with RS and PS data

    Returns:
        dataframe with RS and PS identifiers
    """

    for row, _ in enumerate(dataframe.index):
        if dataframe.loc[row, 'RSPS'] == '':
            dataframe.loc[row, 'diff_qualifier'] = 'Diff'

    for row, _ in enumerate(dataframe.index):
        if (dataframe.loc[row, 'diff_qualifier'] != 'Diff' and (row == 0 or dataframe.loc[row - 1, 'diff_qualifier'] == 'Diff')):
            dataframe.loc[row, 'diff_qualifier'] = 'First'

    for row, _ in enumerate(dataframe.index):
        if (dataframe.loc[row, 'diff_qualifier'] != 'Diff' and (dataframe.loc[row + 1, 'diff_qualifier'] == 'Diff' and dataframe.loc[row, 'RSPS'] == 'PS')):
            dataframe.loc[row, 'diff_qualifier'] = 'Last'

    return dataframe


def remove_extra_first_last(dataframe):
    """Get rid of extra firsts/lasts.

    Args:
        dataframe: dataframe of player data

    Returns:
        dataframe with ensures properly placed diff rows
    """
    first_count = 0
    last_count = 0
    for row, _ in enumerate(dataframe.index):
        if dataframe.loc[row, 'diff_qualifier'] == 'First':
            first_count += 1
        elif dataframe.loc[row, 'diff_qualifier'] == 'Last':
            last_count += 1
        elif dataframe.loc[row, 'diff_qualifier'] == 'Diff' and first_count != last_count:
            first_count = 0
            last_count = 0
            dataframe.loc[row, 'diff_qualifier'] = ''
            temp_row = row - 1
            while temp_row >= 0 and dataframe.loc[temp_row, 'diff_qualifier'] != 'Diff':
                dataframe.loc[temp_row, 'diff_qualifier'] = ''
                temp_row -= 1
    return dataframe


def get_differences(dataframe):
    """Calculate differences between RS and PS.

    Args:
        dataframe: dataframe with RS and PS data

    Returns:
        dataframe with RS, PS, and differences
    """
    diff_columns = frozenset({
       '"MP',
       'FG',
       'FGA',
       'FG%',
       '3P',
       '3PA',
       '3P%',
       '2P',
       '2PA',
       '2P%',
       'eFG%',
       'FT',
       'FTA',
       'FT%',
       'ORB',
       'DRB',
       'TRB',
       'AST',
       'STL',
       'BLK',
       'TOV',
       'PF',
       'PTS',
       'ORtg',
       'DRtg',
       'PER',
       'TS%',
       '3PAr',
       'FTr',
       'ORB%',
       'DRB%',
       'TRB%',
       'AST%',
       'STL%',
       'BLK%',
       'TOV%',
       'USG%',
       'OWS',
       'DWS',
       'WS',
       'WS/48',
       'OBPM',
       'DBPM',
       'BPM',
       'VORP',
    })
    curr_cols = frozenset(dataframe.columns)
    curr_cols_to_diff = list(curr_cols.intersection(diff_columns))
    first = {}
    last = {}
    diff = {}
    for row, _ in enumerate(dataframe.index):
        if dataframe.at[row, 'diff_qualifier'] == 'First':

            for col in curr_cols_to_diff:
                first[col] = dataframe.at[row, col]

        elif dataframe.at[row, 'diff_qualifier'] == 'Last':
            for col in curr_cols_to_diff:
                last[col] = dataframe.at[row, col]

        elif dataframe.at[row, 'diff_qualifier'] == 'Diff':
            for col in curr_cols_to_diff:
                diff[col] = last.get(col) - first.get(col)
                dataframe.at[row, col] = diff.get(col)
            first = {}
            last = {}
            diff = {}

    return dataframe


def remove_diff_qualifier_column(dataframe):
    """Remove diff_qualifier column.

    Args:
        dataframe: dataframe with diff_qualifier

    Returns:
        dataframe without diff_qualifier
    """
    return dataframe.iloc[:, :-1]


def player_single_table_type(player_page, table_type):
    """Get specific single table for player.

    Args:
        player_page: player page to get table from
        table_type: table type to get info about

    Returns:
        dataframe of RS and PS data with comparisons
    """
    regular_season = clean_table(player_page, 'RS', table_type)
    post_season = clean_table(player_page, 'PS', table_type)
    if (regular_season is None) & (post_season is None):
        return pd.DataFrame()
    combined = combine_rs_and_ps(regular_season, post_season)
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
    return remove_diff_qualifier_column(combined)


def main(player_id):
    """Get player rsvsps data from player ID.

    Args:
        player_id: string that is player ID.

    Returns:
        An excel file with player data.
    """
    player_url = determine_player_url(player_id)
    player_page = scrape_player_page(player_url)
    del player_page[0]
    per_game = player_single_table_type(player_page, 'per_game')
    per_minute = player_single_table_type(player_page, 'per_minute')
    per_poss = player_single_table_type(player_page, 'per_poss')
    advanced = player_single_table_type(player_page, 'advanced')

    with pd.ExcelWriter('output/{player}.xlsx'.format(player=player_id), engine='xlsxwriter') as writer:
        per_game.to_excel(writer, sheet_name='per_game')
        per_minute.to_excel(writer, sheet_name='per_minute')
        per_poss.to_excel(writer, sheet_name='per_poss')
        advanced.to_excel(writer, sheet_name='advanced')
    return writer


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--player', type=str)
    args = parser.parse_args()
    main(args.player)
