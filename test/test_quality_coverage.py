"""Quality coverage tests for the core scraper and comparison logic."""

import csv
import os
import runpy
import sys
import tempfile
import unittest
from unittest import mock

import requests
from bs4 import BeautifulSoup

from rsvsps import rsvsps
from rsvsps.scrapers import player_page_scraper, team_log_scraper


class TestPlayerPageCoverage(unittest.TestCase):
    """Exercise scraper helpers and edge cases."""

    def test_determine_player_url_and_scrape_helpers(self):
        self.assertEqual(
            player_page_scraper.determine_player_url('petrodr01'),
            'https://www.basketball-reference.com/players/p/petrodr01.html',
        )

        with self.assertRaises(SystemExit):
            player_page_scraper.determine_player_url('')

        html = '''
        <table id="per_game">
            <tr><th>Season</th><th>FG</th></tr>
            <tr><td>1989-90</td><td>10</td></tr>
            <tr><td> </td><td> </td></tr>
        </table>
        <table id="playoffs_per_game">
            <tr><th>Season</th><th>FG</th></tr>
            <tr><td>1990-91</td><td>12</td></tr>
        </table>
        '''
        soup = list(BeautifulSoup(html, 'lxml').find_all('table'))

        self.assertIsNotNone(player_page_scraper.scrape_tables(soup, 'RS', 'per_game'))
        self.assertIsNone(player_page_scraper.scrape_tables(soup, 'RS', 'per_minute'))

        table = player_page_scraper.scrape_tables(soup, 'RS', 'per_game')
        self.assertEqual(player_page_scraper.scraped_table_to_list(table)[0][0], 'Season')

        self.assertEqual(
            player_page_scraper.remove_blank_lines([
                ['Season', 'FG'],
                ['', ''],
                ['1989-90', '10'],
            ]),
            [['Season', 'FG'], ['1989-90', '10']],
        )

        self.assertEqual(player_page_scraper.adjustments_for_did_not_play_seasons([]), [])
        self.assertEqual(
            player_page_scraper.adjustments_for_did_not_play_seasons([
                ['Season', 'Age', 'Team', 'Lg', 'Pos'],
                ['1986-87', 'Did not play - other pro league (Yugoslavia) '],
                ['1989-90', '25', 'POR', 'NBA', 'SG'],
            ])[1][2],
            '',
        )

        with mock.patch('rsvsps.scrapers.player_page_scraper.requests.get') as mock_get:
            mock_get.return_value = mock.Mock(status_code=500, text='bad', raise_for_status=lambda: None)
            with self.assertRaises(SystemExit):
                player_page_scraper.scrape_player_page('https://example.test')

        cleaned = player_page_scraper.clean_table(soup, 'RS', 'per_game')
        self.assertEqual(cleaned[0][0], 'Season')
        self.assertEqual(cleaned[1][-1], 'RS')

    def test_uncovered_player_scraper_branches(self):
        with mock.patch.object(player_page_scraper, 'fetch_with_retries', side_effect=requests.exceptions.RequestException('boom')):
            with self.assertRaises(SystemExit):
                player_page_scraper.scrape_player_page('https://example.test')

        empty_table = BeautifulSoup('<table id="per_game"></table>', 'lxml').find('table')
        self.assertIsNone(player_page_scraper.clean_table([empty_table], 'RS', 'per_game'))

        self.assertEqual(player_page_scraper.combine_rs_and_ps(None, [['Season', 'FG']]), [['Season', 'FG']])
        self.assertEqual(player_page_scraper.combine_rs_and_ps([['Season', 'FG']], None), [['Season', 'FG']])

        with mock.patch.object(player_page_scraper, 'clean_table', side_effect=[[], None]):
            self.assertEqual(player_page_scraper.get_table_data([], 'per_game'), (None, None))

        with mock.patch.object(player_page_scraper, 'scrape_player_page', return_value=None), \
                mock.patch.object(player_page_scraper, 'get_table_data', side_effect=[
            (['Season', 'FG'], [['1989-90', '10', 'RS', '']]),
            (['Season', 'FG'], [['1989-90', '10', 'RS', '']]),
            (['Season', 'FG'], [['1989-90', '10', 'RS', '']]),
            (['Season', 'FG'], [['1989-90', '10', 'RS', '']]),
        ]):
            all_data = player_page_scraper.main('petrodr01', 'all')
            self.assertEqual(len(all_data), 4)

    def test_get_table_data_and_main_table_type(self):
        html = '''
        <table id="per_game">
            <tr><th>Season</th><th>Age</th><th>Team</th><th>Lg</th><th>Pos</th><th>FG</th><th>PTS</th></tr>
            <tr><td>1989-90</td><td>25</td><td>POR</td><td>NBA</td><td>SG</td><td>10</td><td>100</td></tr>
            <tr><td>1990-91</td><td>26</td><td>NJN</td><td>NBA</td><td>SG</td><td>12</td><td>120</td></tr>
        </table>
        <table id="playoffs_per_game">
            <tr><th>Season</th><th>Age</th><th>Team</th><th>Lg</th><th>Pos</th><th>FG</th><th>PTS</th></tr>
            <tr><td>1990-91</td><td>26</td><td>POR</td><td>NBA</td><td>SG</td><td>13</td><td>130</td></tr>
            <tr><td>1991-92</td><td>27</td><td>NJN</td><td>NBA</td><td>SG</td><td>15</td><td>150</td></tr>
        </table>
        '''
        soup = list(BeautifulSoup(html, 'lxml').find_all('table'))

        headers, rows = player_page_scraper.get_table_data(soup, 'per_game')
        self.assertEqual(headers[0], 'Season')
        self.assertGreater(len(rows), 0)

        result = rsvsps.player_single_table_type(headers, rows, 'per_game')
        self.assertIsNotNone(result)
        self.assertIn('FG', result.columns)

        self.assertIsNone(rsvsps.player_single_table_type(None, None, 'per_game'))

        sorted_rows = player_page_scraper.add_sorting_qualifier([
            ['season', 'Age', 'Team'],
            ['1989-90', '25', 'POR'],
            ['Career', '25', 'TOT'],
        ])
        self.assertEqual(sorted_rows[0][-1], '1Team')
        self.assertEqual(sorted_rows[1][-1], '01989-90')
        self.assertEqual(sorted_rows[2][-1], '2')

        self.assertIsNone(player_page_scraper.scrape_tables([
            BeautifulSoup('<table><tr><td>no id</td></tr></table>', 'lxml')
        ], 'RS', 'per_game'))

        empty_table = BeautifulSoup('<table id="per_game"><tr><td></td></tr></table>', 'lxml').find('table')
        self.assertIsNone(player_page_scraper.clean_table([empty_table], 'RS', 'per_game'))
        soup = list(BeautifulSoup('<table id="per_game"><tr><th>Season</th><th>FG</th></tr><tr><td>1989-90</td><td>10</td></tr></table>', 'lxml').find_all('table'))
        self.assertEqual(player_page_scraper.get_table_data(soup, 'per_game')[0][0], 'Season')

        with mock.patch.object(player_page_scraper, 'determine_player_url', return_value='https://example.test'):
            with mock.patch.object(
                player_page_scraper,
                'scrape_player_page',
                return_value=[BeautifulSoup('<table id="per_game"><tr><th>Season</th><th>FG</th></tr><tr><td>1989-90</td><td>10</td></tr></table>', 'lxml')],
            ):
                result = player_page_scraper.main('petrodr01', 'per_game')
                self.assertIsNotNone(result)

    def test_scrape_tables_and_table_conversion(self):
        page = BeautifulSoup('<table id="per_game"><tr><th>Season</th></tr></table>', 'lxml').find_all('table')
        self.assertIsNotNone(player_page_scraper.scrape_tables(page, 'RS', 'per_game'))
        self.assertIsNone(player_page_scraper.scrape_tables(page, 'RS', 'per_minute'))
        self.assertEqual(player_page_scraper.scraped_table_to_list(page[0])[0][0], 'Season')

    def test_fetch_retries_and_cli_entrypoint(self):
        with mock.patch('rsvsps.scrapers.player_page_scraper.time.sleep') as sleep:
            with mock.patch(
                'rsvsps.scrapers.player_page_scraper.requests.get',
                side_effect=[
                    mock.Mock(status_code=429),
                    mock.Mock(status_code=200, text='<table id="per_game"><tr><th>Season</th></tr></table>'),
                ],
            ):
                response = player_page_scraper.fetch_with_retries('https://example.test', max_retries=2)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(sleep.call_count, 1)

        with mock.patch('rsvsps.scrapers.player_page_scraper.requests.get', side_effect=requests.exceptions.RequestException('boom')):
            with self.assertRaises(requests.exceptions.RequestException):
                player_page_scraper.fetch_with_retries('https://example.test', max_retries=2)

        with self.assertRaises(requests.exceptions.RequestException):
            player_page_scraper.fetch_with_retries('https://example.test', max_retries=0)

        with mock.patch('requests.get') as mock_get:
            mock_get.side_effect = [
                mock.Mock(status_code=429, text='retry'),
                mock.Mock(status_code=200, text='''<html><body><table id="per_game"><tr><th>Season</th><th>FG</th></tr><tr><td>1989-90</td><td>10</td></tr></table></body></html>'''),
            ]
            with mock.patch.object(sys, 'argv', ['player_page_scraper.py', '--player', 'petrodr01', '--table-type', 'per_game']):
                runpy.run_path('rsvsps/scrapers/player_page_scraper.py', run_name='__main__')

        with mock.patch('rsvsps.scrapers.team_log_scraper.requests.get', side_effect=
            [mock.Mock(status_code=429), mock.Mock(status_code=200, text='<html><body><table id="tgl_basic"></table></body></html>')]):
            with mock.patch('rsvsps.scrapers.team_log_scraper.time.sleep'):
                self.assertEqual(team_log_scraper.fetch_with_retries('https://example.test', max_retries=2).status_code, 200)

        with mock.patch('rsvsps.scrapers.team_log_scraper.requests.get', side_effect=[requests.exceptions.RequestException('boom'), requests.exceptions.RequestException('boom')]):
            with self.assertRaises(requests.exceptions.RequestException):
                team_log_scraper.fetch_with_retries('https://example.test', max_retries=2)

        with mock.patch('rsvsps.scrapers.team_log_scraper.requests.get', side_effect=requests.exceptions.RequestException('boom')):
            with self.assertRaises(requests.exceptions.RequestException):
                team_log_scraper.fetch_with_retries('https://example.test', max_retries=3)

        with self.assertRaises(requests.exceptions.RequestException):
            team_log_scraper.fetch_with_retries('https://example.test', max_retries=0)

        with mock.patch.object(sys, 'argv', ['team_log_scraper.py', '--team', 'BOS', '--season', '2024', '--postseason_bool', 'False']):
            with mock.patch('requests.get', return_value=mock.Mock(status_code=200, text='<html><body><table id="tgl_basic"><tr><th>Rk</th><th>G</th><th>Date</th><th>Home/ Away</th><th>Opp</th><th>W/L</th><th>Tm</th><th>Opp</th><th>FG</th><th>FGA</th></tr><tr><td>1</td><td>1</td><td>2024-10-20</td><td></td><td>MIA</td><td>W</td><td>110</td><td>105</td><td>40</td><td>90</td></tr></table></body></html>')):
                runpy.run_path('rsvsps/scrapers/team_log_scraper.py', run_name='__main__')

        with mock.patch('rsvsps.scrapers.team_log_scraper.scrape_team_season_log_page', return_value=[BeautifulSoup('<table id="tgl_basic"></table>', 'lxml')]):
            self.assertEqual(team_log_scraper.get_output_for_team('BOS', '2024', None), [])


class TestTeamLogCoverage(unittest.TestCase):
    """Exercise the team log scraper across branches and edge cases."""

    def test_scrape_team_season_log_page_success_and_failure_modes(self):
        page = '<html><body><!--<table id="tgl_basic"></table><table id="tgl_basic_playoffs"></table>--></body></html>'

        with mock.patch('rsvsps.scrapers.team_log_scraper.requests.get') as mock_get:
            mock_response = mock.Mock(status_code=200, text=page)
            mock_get.return_value = mock_response
            soup = team_log_scraper.scrape_team_season_log_page('https://example.test')
            self.assertTrue(len(soup) >= 1)

        with mock.patch('rsvsps.scrapers.team_log_scraper.requests.get', side_effect=requests.exceptions.RequestException('boom')):
            with self.assertRaises(SystemExit):
                team_log_scraper.scrape_team_season_log_page('https://example.test')

        with mock.patch('rsvsps.scrapers.team_log_scraper.requests.get') as mock_get:
            mock_response = mock.Mock(status_code=404, text='missing')
            mock_get.return_value = mock_response
            with self.assertRaises(SystemExit):
                team_log_scraper.scrape_team_season_log_page('https://example.test')

    def test_team_log_helpers_and_standardization(self):
        raw_rows = [
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA', '3P', '3PA', 'PTS'],
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'Team FG', 'Team FGA', 'Team 3P', 'Team 3PA', 'Team PTS'],
            ['1', '1', '2024-10-20', '@', 'MIA', 'W', '110', '105', '40', '90', '12', '32', '110'],
        ]
        cleaned = team_log_scraper.clean_column_headers(raw_rows)
        self.assertIn('FG', cleaned[0][8])
        self.assertIn('3P', cleaned[0][10])
        self.assertIn('3PA', cleaned[0][11])

        home_flag = team_log_scraper.update_home_flag([
            ['Rank', 'Game Number', 'Date', 'Home Flag', 'Opp', 'Result', 'Team Points', 'Opponent Points'],
            ['1', '1', '2024-10-20', '', 'MIA', 'W', '110', '105'],
            ['2', '2', '2024-10-21', '@', 'BOS', 'L', '97', '103'],
        ])
        self.assertTrue(home_flag[1][3])
        self.assertFalse(home_flag[2][3])

        home_flag_missing = team_log_scraper.update_home_flag([
            ['Rank', 'Game Number', 'Date', 'Opp', 'Result'],
            ['1', '1', '2024-10-20', 'MIA', 'W'],
        ])
        self.assertEqual(home_flag_missing[0][0], 'Rank')

        duplicate_headers = team_log_scraper.remove_duplicate_header_rows([
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA'],
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA'],
            ['1', '1', '2024-10-20', '@', 'MIA', 'W', '110', '105', '40', '90'],
            ['2', '2', '2024-10-21', '', 'BOS', 'L', '97', '103', '35', '92'],
        ])
        self.assertEqual(duplicate_headers[0][0], 'Rk')
        self.assertEqual(len(duplicate_headers), 4)

        skipped_duplicate_header = team_log_scraper.remove_duplicate_header_rows([
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA'],
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA'],
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA'],
        ])
        self.assertEqual(len(skipped_duplicate_header), 2)

        away_standard = team_log_scraper.standardize_cols_for_home_court([
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA', '3P', '3PA', 'PTS'],
            ['1', '1', '2024-10-20', '@', 'MIA', 'L', '97', '103', '34', '87', '11', '28', '97'],
        ], 'BOS')
        self.assertEqual(away_standard[1][4], 'W')
        self.assertEqual(away_standard[1][2], 'MIA')

        explicit_loss = team_log_scraper.update_teams_to_home_and_away([
            ['Rk', 'G', 'Date', 'Home Flag', 'Opp', 'Result', 'Team Points', 'Opponent Points'],
            ['1', '1', '2024-10-20', False, 'MIA', 'L', '97', '103'],
        ], 'BOS', 3)
        self.assertIsNotNone(explicit_loss)
        self.assertEqual(explicit_loss[1][0], '1')

        neutral_result = team_log_scraper.update_teams_to_home_and_away([
            ['Rk', 'G', 'Date', 'Home Flag', 'Opp', 'Result', 'Team Points', 'Opponent Points'],
            ['1', '1', '2024-10-20', False, 'MIA', 'T', '97', '103'],
        ], 'BOS', 3)
        self.assertEqual(neutral_result[1][0], '1')

        standard = team_log_scraper.standardize_cols_for_home_court([
            ['Rk', 'G', 'Date', 'Home/ Away', 'Opp', 'W/L', 'Tm', 'Opp', 'FG', 'FGA', '3P', '3PA', 'PTS'],
            ['1', '1', '2024-10-20', '@', 'MIA', 'W', '110', '105', '40', '90', '12', '32', '110'],
            ['2', '2', '2024-10-21', '', 'BOS', 'L', '97', '103', '34', '87', '11', '28', '97'],
        ], 'BOS')
        self.assertEqual(standard[0][0], 'Game Number')
        self.assertEqual(standard[0][2], 'Home Team')
        self.assertEqual(standard[1][2], 'MIA')

        page = BeautifulSoup('''
        <table id="tgl_basic">
            <tr><th>Rk</th><th>G</th><th>Date</th><th>Home/ Away</th><th>Opp</th><th>W/L</th><th>Tm</th><th>Opp</th><th>FG</th><th>FGA</th><th>3P</th><th>3PA</th><th>PTS</th></tr>
            <tr><th>Rk</th><th>G</th><th>Date</th><th>Home/ Away</th><th>Opp</th><th>W/L</th><th>Tm</th><th>Opp</th><th>Team FG</th><th>Team FGA</th><th>Team 3P</th><th>Team 3PA</th><th>Team PTS</th></tr>
            <tr><td>1</td><td>1</td><td>2024-10-20</td><td>@</td><td>MIA</td><td>W</td><td>110</td><td>105</td><td>40</td><td>90</td><td>12</td><td>32</td><td>110</td></tr>
        </table>
        ''', 'lxml').find_all('table')
        data = team_log_scraper.get_log_for_team_season_and_season_type(page, False, 'BOS')
        self.assertIsNotNone(data)
        self.assertEqual(data[0][0], 'Game Number')

        self.assertIsNone(team_log_scraper.get_log_for_team_season_and_season_type(
            [BeautifulSoup('<table id="tgl_other"></table>', 'lxml')],
            False,
            'BOS',
        ))

        with mock.patch('rsvsps.scrapers.team_log_scraper.scrape_team_season_log_page', return_value=[BeautifulSoup('<table id="tgl_basic"></table>', 'lxml')]):
            with mock.patch('rsvsps.scrapers.team_log_scraper.get_log_for_team_season_and_season_type', side_effect=[[['header'], ['1', '1', 'BOS', 'MIA']], None]):
                rows = team_log_scraper.get_output_for_team('BOS', '2024', None)
                self.assertEqual(rows[0][0], 'header')

    def test_write_output_and_get_output_for_team(self):
        temp_dir = tempfile.mkdtemp()
        old_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            output_data = [
                ['Rank', 'Game Number', 'Date', 'Home Flag', 'Home Team', 'Away Team', 'Team Points', 'Opponent Points'],
                ['1', '1', '2024-10-20', True, 'BOS', 'MIA', '110', '105'],
            ]
            team_log_scraper.write_output(output_data, 'BOS', '2024', False)
            self.assertTrue(os.path.exists('output/BOS_2024_regular_season.csv'))

            team_log_scraper.write_output(output_data, 'BOS', '2024', True)
            self.assertTrue(os.path.exists('output/BOS_2024_post_season.csv'))

            team_log_scraper.write_output(output_data, 'BOS', '2024', None)
            self.assertTrue(os.path.exists('output/BOS_2024.csv'))

            with mock.patch('rsvsps.scrapers.team_log_scraper.scrape_team_season_log_page', return_value=[BeautifulSoup('<table id="tgl_basic"></table>', 'lxml')]):
                with mock.patch('rsvsps.scrapers.team_log_scraper.get_log_for_team_season_and_season_type', return_value=[['header'], ['1', '1', 'BOS', 'MIA']]):
                    rows = team_log_scraper.get_output_for_team('BOS', '2024', False)
                    self.assertGreater(len(rows), 0)

            with mock.patch('rsvsps.scrapers.team_log_scraper.get_output_for_team', return_value=[['header'], ['1', '1', 'BOS', 'MIA']]):
                team_log_scraper.main('ALL', '2024', False)
                self.assertTrue(os.path.exists('output/ALL_2024_regular_season.csv'))

            with mock.patch('rsvsps.scrapers.team_log_scraper.get_output_for_team', return_value=[['header'], ['1', '1', 'BOS', 'MIA']]):
                team_log_scraper.main('BOS', '2024', False)
                self.assertTrue(os.path.exists('output/BOS_2024_regular_season.csv'))

            with mock.patch('rsvsps.scrapers.team_log_scraper.scrape_team_season_log_page', return_value=[BeautifulSoup('<table id="tgl_basic"></table>', 'lxml')]):
                with mock.patch('rsvsps.scrapers.team_log_scraper.get_log_for_team_season_and_season_type', side_effect=[[['header'], ['1', '1', 'BOS', 'MIA']], [['header'], ['2', '2', 'BOS', 'MIA']]]):
                    rows = team_log_scraper.get_output_for_team('BOS', '2024', None)
                    self.assertEqual(rows[0][0], 'header')
                    self.assertEqual(rows[2][0], '2')
        finally:
            os.chdir(old_cwd)


class TestRsVsPsCoverage(unittest.TestCase):
    """Exercise remaining comparison logic and the main writer."""

    def test_dataframe_helpers_and_writer(self):
        dataset = [
            ['Season', 'Age', 'Team', 'Lg', 'Pos', 'FG', 'PTS', 'RSPS', 'diff_qualifier'],
            ['1989-90', '25', 'POR', 'NBA', 'SG', '10', '100', 'RS', ''],
            ['1990-91', '26', 'NJN', 'NBA', 'SG', '12', '120', 'PS', ''],
        ]
        frame = rsvsps.create_dataframe(dataset, dataset[0])
        frame = rsvsps.dataframe_data_types(frame, 'per_game')
        frame = rsvsps.determine_rows_to_fill(frame)
        frame = rsvsps.remove_extra_first_last(frame)
        frame = rsvsps.get_differences(frame)
        self.assertIn('FG', frame.columns)
        self.assertEqual(rsvsps.remove_diff_qualifier_column(frame).shape[1], 8)

        self.assertEqual(rsvsps.remove_sorting_column([['1', '2', '3', '4']]), [['1', '2', '3']])
        self.assertEqual(rsvsps.add_blank_lines([['a'], ['b']]), [['a'], [''], ['b'], ['']])
        self.assertEqual(rsvsps.add_qualifier_col_diff([['a']]), [['a', '']])

        advanced_frame = rsvsps.create_dataframe([
            ['Season', 'PER', 'WS', 'RSPS', 'diff_qualifier'],
            ['1989-90', '12.0', '5.0', 'RS', ''],
            ['1990-91', '14.0', '7.0', 'PS', ''],
        ], ['Season', 'PER', 'WS', 'RSPS', 'diff_qualifier'])
        advanced_frame = rsvsps.dataframe_data_types(advanced_frame, 'advanced')
        self.assertIn('PER', advanced_frame.columns)

        unknown_frame = rsvsps.create_dataframe([
            ['Season', 'FG'],
            ['1989-90', '10'],
        ], ['Season', 'FG'])
        unknown_frame = rsvsps.dataframe_data_types(unknown_frame, 'unknown')
        self.assertListEqual(list(unknown_frame.columns), ['Season', 'FG'])

        mismatch_frame = rsvsps.create_dataframe([
            ['Season', 'FG', 'RSPS', 'diff_qualifier'],
            ['1989-90', '10', 'RS', 'First'],
            ['1990-91', '12', 'RS', 'First'],
            ['', '', '', 'Diff'],
            ['1991-92', '15', 'PS', 'Last'],
        ], ['Season', 'FG', 'RSPS', 'diff_qualifier'])
        mismatch_frame = rsvsps.remove_extra_first_last(mismatch_frame)
        self.assertEqual(mismatch_frame.loc[2, 'diff_qualifier'], '')

    def test_main_writes_output(self):
        script_path = os.path.abspath(rsvsps.__file__)
        synthetic = (
            (['Season', 'Age', 'Team', 'Lg', 'Pos', 'FG', 'PTS', 'RSPS', 'diff_qualifier'], [
                ['1989-90', '25', 'POR', 'NBA', 'SG', '10', '100', 'RS', ''],
                ['1990-91', '26', 'NJN', 'NBA', 'SG', '12', '120', 'PS', ''],
            ]),
            (['Season', 'Age', 'Team', 'Lg', 'Pos', 'FG', 'PTS', 'RSPS', 'diff_qualifier'], [
                ['1989-90', '25', 'POR', 'NBA', 'SG', '10', '100', 'RS', ''],
                ['1990-91', '26', 'NJN', 'NBA', 'SG', '12', '120', 'PS', ''],
            ]),
            (['Season', 'Age', 'Team', 'Lg', 'Pos', 'FG', 'PTS', 'RSPS', 'diff_qualifier'], [
                ['1989-90', '25', 'POR', 'NBA', 'SG', '10', '100', 'RS', ''],
                ['1990-91', '26', 'NJN', 'NBA', 'SG', '12', '120', 'PS', ''],
            ]),
            (['Season', 'Age', 'Team', 'Lg', 'Pos', 'PER', 'WS', 'RSPS', 'diff_qualifier'], [
                ['1989-90', '25', 'POR', 'NBA', 'SG', '15.0', '5.0', 'RS', ''],
                ['1990-91', '26', 'NJN', 'NBA', 'SG', '17.0', '7.0', 'PS', ''],
            ]),
        )

        with mock.patch.object(rsvsps.player_page_scraper, 'main', return_value=synthetic):
            with tempfile.TemporaryDirectory() as tmpdir:
                old_cwd = os.getcwd()
                os.chdir(tmpdir)
                try:
                    result = rsvsps.main('petrodr01')
                    self.assertIsNotNone(result)
                    self.assertTrue(os.path.exists('output/petrodr01.xlsx'))

                    with mock.patch.object(rsvsps.player_page_scraper, 'main', return_value=(
                        (['Season', 'FG', 'RSPS', 'diff_qualifier'], [['1989-90', '10', 'RS', '']]),
                        (None, None),
                        (None, None),
                        (None, None),
                    )):
                        result = rsvsps.main('petrodr01')
                        self.assertIsNotNone(result)

                    with mock.patch.object(rsvsps.player_page_scraper, 'main', return_value=((None, None), (None, None), (None, None), (None, None))):
                        result = rsvsps.main('petrodr01')
                        self.assertIsNotNone(result)
                finally:
                    os.chdir(old_cwd)

        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with mock.patch.object(sys, 'argv', ['rsvsps.py', '--player', 'petrodr01']):
                    with mock.patch.object(rsvsps.player_page_scraper, 'main', return_value=synthetic):
                        runpy.run_path(
                            script_path,
                            run_name='__main__',
                            init_globals={'main': rsvsps.main},
                        )
            finally:
                os.chdir(old_cwd)




if __name__ == '__main__':
    unittest.main()
