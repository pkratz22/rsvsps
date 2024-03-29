import argparse

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
    
    if page_request.status_code != 200:
        raise SystemExit('HTTP Error: {0}'.format(page_request.status_code))

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
    return soup.contents[1:]


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


def get_table_data(player_page, table_type):
    regular_season = clean_table(player_page, 'RS', table_type)
    post_season = clean_table(player_page, 'PS', table_type)
    if (regular_season is None) & (post_season is None):
        return None, None
    combined = combine_rs_and_ps(regular_season, post_season)
    column_headers = scrape_column_headers(combined)
    combined = remove_column_headers(combined)
    combined = add_sorting_qualifier(combined)
    combined = sort_list(combined)
    return column_headers, combined


def main(player_id, table_type):
    player_url = determine_player_url(player_id)
    player_page = scrape_player_page(player_url) # returns soup
    
    if table_type == 'all':
        per_game_column_headers, per_game_combined = get_table_data(player_page, 'per_game')
        per_minute_column_headers, per_minute_combined = get_table_data(player_page, 'per_minute')
        per_poss_column_headers, per_poss_combined = get_table_data(player_page, 'per_poss')
        advanced_column_headers, advanced_combined = get_table_data(player_page, 'advanced')
        return (
            (per_game_column_headers, per_game_combined),
            (per_minute_column_headers, per_minute_combined),
            (per_poss_column_headers, per_poss_combined),
            (advanced_column_headers, advanced_combined),
        )
    else:
        return get_table_data(player_page, table_type)




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--player', type=str)
    parser.add_argument('--table-type', type=str)
    args = parser.parse_args()

    main(args.player, args.table_type)
