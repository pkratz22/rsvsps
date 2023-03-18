import requests
from bs4 import BeautifulSoup, SoupStrainer


def scrape_team_season_log_page(team_season_log_urls):
    """Scrape Player Page for tables.

    Raises:
        SystemExit: HTTPError for player ID

    Args:
        player_url: URL to scrape

    Returns:
        soup of scraped page
    """
    try:
        page_request = requests.get(team_season_log_urls)
        page_request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit from err
    team_season_log_page = page_request.text
    tables = SoupStrainer(id=[
        'tgl_basic',
        'tgl_basic_playoffs'
    ])
    team_season_log_page = team_season_log_page.replace('<!--', '').replace('-->', '')

    soup = BeautifulSoup(team_season_log_page, 'lxml', parse_only=tables)
    return soup.contents


def scrape_tables(soup, label):
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
        if table.attrs['id'] == 'tgl_basic{ps_qualifier}'.format(ps_qualifier=qualifier_map[label]):
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


def clean_table(soup, label):
    """Put functions for RS and PS into one.

    Args:
        soup: soup for player page

    Returns:
        player data for label and table_type
    """
    table = scrape_tables(soup, label)
    if table is None:
        return None
    player_data_list = scraped_table_to_list(table)
    column_headers = scrape_column_headers(player_data_list) + ['RSPS'] + ['diff_qualifier']
    player_data_list = remove_column_headers(player_data_list)
    player_data_list = remove_blank_lines(player_data_list)
    player_data_list = adjustments_for_did_not_play_seasons(player_data_list)
    #player_data_list = label_rs_or_ps(player_data_list, label)
    #if label == 'RS':
    #    player_data_list = [column_headers] + player_data_list
    return player_data_list


if __name__ == '__main__':
    soup = scrape_team_season_log_page('https://www.basketball-reference.com/teams/MIL/2022/gamelog/')
    del soup[0]
    label = 'RS'
    output = clean_table(soup, label)
    print(output)