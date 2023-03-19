import requests
from bs4 import BeautifulSoup, SoupStrainer


def scrape_team_season_log_page(team_season_log_urls):
    """Scrape Team Log Page for tables.

    Raises:
        SystemExit: HTTPError for team season

    Args:
        team_game_log_data_list: URL to scrape

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
    """Scrape game log tables.

    Args:
        soup: soup of team log page
        label: regular season or post-season

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


def scrape_column_headers(team_data_log_list):
    """Store column headers.

    Args:
        team_game_log_data_list: team game log data list

    Returns:
        headers for team game log table
    """
    team_col_prefix = 'Team'
    opponent_col_prefix = 'Opponent'
    team_columns_headers = team_data_log_list[1]
    team_columns_headers[0] = 'Game Number'
    team_columns_headers[1] = 'Game Number'
    team_columns_headers[3] = 'Home Flag'
    team_columns_headers[6] = 'Team Points'
    team_columns_headers[7] = 'Opponent Points'
    num_team_cols_except_score = int((len(team_columns_headers) - 9)/2)
    
    for i in range(8, 8+num_team_cols_except_score):
        team_columns_headers[i] = '{team_indicator} {stat}'.format(
            team_indicator=team_col_prefix,
            stat=team_columns_headers[i],
        )
    for i in range(len(team_columns_headers)-num_team_cols_except_score, len(team_columns_headers)):
        team_columns_headers[i] = '{team_indicator} {stat}'.format(
            team_indicator=opponent_col_prefix,
            stat=team_columns_headers[i],
        )
    return team_columns_headers


def remove_column_headers(team_data_log_list):
    """Remove column headers.

    Args:
        team_game_log_data_list: team game log data list

    Returns:
        team game log data list without column headers
    """
    header_col_type_1 = team_data_log_list[0]
    header_col_type_2 = team_data_log_list[1]
    team_data_log_column_headers_removed = []
    for row in team_data_log_list:
        if row != header_col_type_1 and row != header_col_type_2:
            team_data_log_column_headers_removed.append(row)
    return team_data_log_column_headers_removed


def get_log_for_team_season_and_season_type(soup, label):
    """Put functions for RS and PS into one.

    Args:
        soup: soup for team data log page

    Returns:
        team log data table
    """
    table = scrape_tables(soup, label)
    if table is None:
        return None
    team_game_log_data_list = scraped_table_to_list(table)
    column_headers = scrape_column_headers(team_game_log_data_list) + ['RSPS'] + ['diff_qualifier']
    team_game_log_data_list = remove_column_headers(team_game_log_data_list)
    team_game_log_data_list = [column_headers] + team_game_log_data_list
    return team_game_log_data_list
