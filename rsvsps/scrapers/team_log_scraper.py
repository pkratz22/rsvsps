"""Script to scrape game logs from basketball-reference."""

import argparse
import csv

import requests
from bs4 import BeautifulSoup, SoupStrainer


def scrape_team_season_log_page(team_season_log_urls):
    """Scrape Team Log Page for tables.

    Raises:
        SystemExit: HTTPError for team season

    Args:
        team_season_log_urls: URL to scrape

    Returns:
        soup of scraped page
    """
    try:
        page_request = requests.get(team_season_log_urls, timeout=5)
    except requests.exceptions.RequestException as err:
        raise SystemExit from err

    if page_request.status_code != 200:
        raise SystemExit('HTTP Error: {0}'.format(page_request.status_code))
    
    team_season_log_page = page_request.text
    tables = SoupStrainer(id=[
        'tgl_basic',
        'tgl_basic_playoffs',
    ])
    team_season_log_page = team_season_log_page.replace('<!--', '').replace('-->', '')

    soup = BeautifulSoup(team_season_log_page, 'lxml', parse_only=tables)
    return soup.contents[1:]


def scrape_tables(soup, label):
    """Scrape game log tables.

    Args:
        soup: soup of team log page
        label: regular season or post-season

    Returns:
        soup for table
    """
    qualifier_map = {False: '', True: '_playoffs'}
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

    
def remove_duplicate_header_rows(team_data_log_list):
    """Remove duplicate header rows.

    Args:
        team_data_log_list: table with potentially duplicated header rows

    Returns:
        table without duplicate header rows
    """
    header_row0 = team_data_log_list[0]
    header_row1 = team_data_log_list[1]

    team_data_log_with_dup_headers_removed = [header_row0, header_row1]

    for row in team_data_log_list[2:]:
        if row[0] not in {'', 'Rk'}:
            team_data_log_with_dup_headers_removed.append(row)

    return team_data_log_with_dup_headers_removed


def clean_column_headers(team_data_log_list):
    """Store column headers.

    Args:
        team_data_log_list: team game log data list

    Returns:
        2D list of data with column headers cleaned
    """
    team_data_log_list = remove_duplicate_header_rows(team_data_log_list)
    header_row1 = team_data_log_list[1]

    num_team_cols_except_score = int((len(header_row1) - 9) / 2)
    num_leading_cols = 8

    for index, _ in enumerate(header_row1):
        if num_leading_cols <= index < num_leading_cols + num_team_cols_except_score:
            header_row1[index] = '{team_indicator} {stat}'.format(
                team_indicator='Team',
                stat=header_row1[index],
            )
        elif num_leading_cols + num_team_cols_except_score + 1 <= index < len(header_row1):
            header_row1[index] = '{team_indicator} {stat}'.format(
                team_indicator='Opponent',
                stat=header_row1[index],
            )

    return team_data_log_list[1:]


def update_home_flag(team_log_data):
    """Update home flag.

    Args:
        team_log_data: team game log data list

    Returns:
        team log data with bool field indicating home team
    """
    home_flag_col_num = -1
    for row_num, _ in enumerate(team_log_data[0]):
        if team_log_data[0][row_num] == 'Home Flag':
            home_flag_col_num = row_num
            break
    for row in team_log_data:
        if row[home_flag_col_num] == '':
            row[home_flag_col_num] = True
        elif row[home_flag_col_num] == '@':
            row[home_flag_col_num] = False
    return team_log_data


def update_teams_to_home_and_away(team_log_data, team, home_flag_col_num):
    """Standardize teams to home and away instead of main and opp.

    Args:
        team_log_data: team game log data list
        team: main team
        home_flag_col_num: column number to indicate home vs away

    Returns:
        team log data with teams organized by home vs away
    """
    team_log_data[0].insert(4, 'Home Team')
    team_log_data[0][5] = 'Away Team'
    for row in team_log_data[1:]:
        if row[home_flag_col_num]:
            row.insert(4, team)
        else:
            row.insert(4, row[home_flag_col_num + 1])
            row[5] = team
            if row[6] == 'W':
                row[6] = 'L'
            elif row[6] == 'L':
                row[6] = 'W'
    team_log_data[0][6] = 'Home Team Result'

    for row_num, _ in enumerate(team_log_data):
        team_log_data[row_num] = team_log_data[row_num][1:3] + team_log_data[row_num][4:25] + team_log_data[row_num][26:]
    return team_log_data


def swap_home_and_away_teams(team_log_data, home_flag_col_num):
    """Swap columns for home and away teams.

    Args:
        team_log_data: team game log data list
        home_flag_col_num: col number for home team flag

    Returns:
        Swap data in columns of home and away teams when main team is away
    """
    num_team_cols_except_score = int((len(team_log_data[0]) - 9) / 2)

    standardize_game_logs = [team_log_data[0]]

    num_rows = len(team_log_data)

    for row_num in range(1, num_rows):
        standardize_game_logs.append(team_log_data[row_num])
        if not team_log_data[row_num][home_flag_col_num]:
            temp = team_log_data[row_num][6]
            standardize_game_logs[row_num][6] = team_log_data[row_num][7]
            standardize_game_logs[row_num][7] = temp
            for team_field_counter in range(num_team_cols_except_score):
                first_col = 8 + team_field_counter
                offset = 1 + num_team_cols_except_score
                temp = team_log_data[row_num][first_col]
                standardize_game_logs[row_num][first_col] = team_log_data[row_num][first_col + offset]
                standardize_game_logs[row_num][first_col + offset] = temp

    return standardize_game_logs


def standardize_cols_for_home_court(team_log_data, team):
    """Standardize columns to be team neutral.

    Args:
        team_log_data: team game log data list
        team: name of home team

    Returns:
        data log with teams organized by home and away
        instead of main team and opponent
    """
    team_log_data[0][0] = 'Rank'
    team_log_data[0][1] = 'Game Number'
    team_log_data[0][3] = 'Home Flag'
    team_log_data[0][6] = 'Team Points'
    team_log_data[0][7] = 'Opponent Points'

    team_log_data = update_home_flag(team_log_data)

    home_flag_col_num = 3

    standardize_game_logs = swap_home_and_away_teams(team_log_data, home_flag_col_num)

    for col_num, _ in enumerate(standardize_game_logs[0]):
        if 'Team ' in standardize_game_logs[0][col_num]:
            standardize_game_logs[0][col_num] = standardize_game_logs[0][col_num].replace('Team ', 'Home Team ')
        elif 'Opponent' in standardize_game_logs[0][col_num]:
            standardize_game_logs[0][col_num] = standardize_game_logs[0][col_num].replace('Opponent ', 'Away Team ')

    return update_teams_to_home_and_away(standardize_game_logs, team, home_flag_col_num)


def get_log_for_team_season_and_season_type(soup, label, team):
    """Put functions for RS and PS into one.

    Args:
        soup: soup for team data log page
        label: label for regular season vs post season
        team: team name

    Returns:
        team log data table
    """
    table = scrape_tables(soup, label)
    if table is None:
        return None
    team_game_log_data_list = scraped_table_to_list(table)

    team_game_log_data_list = clean_column_headers(team_game_log_data_list)
    return standardize_cols_for_home_court(team_game_log_data_list, team)


def write_output(team_log_data, team, season, post_season_bool):
    """Write output of game logs as csv.

    Args:
        team_log_data: game log data
        team: team name
        season: season number
        post_season_bool: bool to indicate rs or ps
    """
    if post_season_bool is None:
        post_season_ext = ''
    elif post_season_bool:
        post_season_ext = '_post_season'
    else:
        post_season_ext = '_regular_season'
    fname = 'output/{team}_{season}{post_season_bool}.csv'.format(
        team=team,
        season=season,
        post_season_bool=post_season_ext,
    )

    with open(fname, 'w', newline='') as my_csv:
        csv_writer = csv.writer(my_csv)
        csv_writer.writerows(team_log_data)


def get_output_for_team(team, season, post_season_bool):
    """Given team name, season, and post-season bool, output game logs.

    Args:
        team: team name
        season: season number
        post_season_bool: bool to indicate rs or ps
    """
    url = 'https://www.basketball-reference.com/teams/{team}/{season}/gamelog/'.format(
        team=team,
        season=season,
    )
    soup = scrape_team_season_log_page(url)
    output = []
    if post_season_bool is None:
        output.extend(get_log_for_team_season_and_season_type(soup, label=False, team=team))
        postseason = get_log_for_team_season_and_season_type(soup, label=True, team=team)
        if postseason is not None:
            output.extend(postseason[1:])
    else:
        output.extend(get_log_for_team_season_and_season_type(soup, post_season_bool, team))
    return output


def main(team, season, post_season_bool):
    all_team_bool = True if team == 'ALL' else False
    if team == 'ALL':
        team_list = (
            'ATL',
            'BOS',
            'BRK',
            'CHI',
            'CHO',
            'CLE',
            'DAL',
            'DEN',
            'DET',
            'GSW',
            'HOU',
            'IND',
            'LAC',
            'LAL',
            'MEM',
            'MIA',
            'MIL',
            'MIN',
            'NOP',
            'NYK',
            'OKC',
            'ORL',
            'PHI',
            'PHO',
            'POR',
            'SAC',
            'SAS',
            'TOR',
            'UTA',
            'WAS',  
        )
        output = []
        for team in team_list:
            output.extend(get_output_for_team(team, season, post_season_bool))
    else:
        output = get_output_for_team(team, season, post_season_bool)
    
    if all_team_bool:
        header_row = output[0]
        data = output[1:]
        data = [i for i in data if i != header_row]
        data = [i[1:] for i in data]
        data = list(map(list, set(map(tuple, data))))
        data.insert(0, header_row[1:])
        write_output(data, "ALL", season, post_season_bool)
    else:
        write_output(output, team, season, post_season_bool)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--team', type=str, required=True)
    parser.add_argument('--season', type=str, required=True)
    parser.add_argument('--postseason_bool', type=bool)
    args = parser.parse_args()

    main(args.team, args.season, args.postseason_bool)
