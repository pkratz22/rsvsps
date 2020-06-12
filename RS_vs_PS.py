# imports

from bs4 import BeautifulSoup, SoupStrainer, Comment
import re
import requests
import operator

# profiling

import cProfile, pstats, io

def profile(fnc):
    
    """A decorator that uses cProfile to profile a function"""
    
    def inner(*args, **kwargs):
        
        pr = cProfile.Profile()
        pr.enable()
        retval = fnc(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        print(s.getvalue())
        return retval

    return inner

perGameColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'RS or PS']
#perMinColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
#perPossColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', '', 'ORtg', 'DRtg']
#advancedColumns = ['Season', 'Age', 'Tm', 'Pos', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV', 'USG%', '', 'OWS', 'DWS', 'WS', 'WS/48', '', 'OBPM', 'DBPM', 'BPM', 'VORP']



def determine_player_URL(playerID):
    """Determine the Player's Page URL from playerID"""
    playerURL = 'https://www.basketball-reference.com/players/' + playerID[0] + '/' + playerID + '.html'
    return playerURL

def scrape_player_page(playerURL):
    """Scrape Player Page for tables"""
    playerPage = requests.get(playerURL).text
    tables = SoupStrainer('table')
    soup = BeautifulSoup(re.sub('<!--|-->','', playerPage), 'lxml', parse_only = tables)
    return soup

def scrape_per_game_tables(soup, label):
    """Scrape the PerGameTables from the Player Page"""
    playoffsQualifier = ''
    if label == 'PS':
        playoffsQualifier = "playoffs_"
    table = soup.find(id=playoffsQualifier + 'per_game')
    return table

def scraped_table_to_list(table):
    """Convert the scraped table to a multidimensional list"""
    return [[cell.text for cell in row.find_all(["th","td"])] for row in table.find_all("tr")]

def delete_column_headers(list):
    """Remove column headers as we will adjust the table and re-add them later"""
    del list[0]
    return list

def remove_blank_lines(list):
    """Remove blank lines - there is one between career and team summaries"""
    for year in list:
        if year[0] == "":
            list.remove(year)
    return list

def adjustments_for_did_not_play_seasons(list):
    """Increase number of elements in list for seasons with Did Not Play"""
    listExtender = [''] * 27
    for year in list:
        if("Did Not Play" in year[2]):
            list.extend(listExtender)
    return list

def label_RS_or_PS(list, label):
    """Adds label of either RS or PS"""
    for year in list:
        year.extend([label])
    return list

def combine_RS_and_PS(RS, PS):
    """Combine Regular Season and Post-Season Data into one table"""
    total = RS+PS
    return total

def add_sorting_qualifier(list):
    """Add an element to each row that can be used to properly sort"""
    for year in list:
        if "season" in year[0]:
            year.insert(len(year), "1"+year[2])
        elif "Career" in year[0]:
            year.insert(len(year), "2")
        else:
            year.insert(len(year), "0"+year[0])
    return list

def sort_list(list):
    """Sort list based on qualifer"""
    list = sorted(list, key=lambda x: (x[-1]))
    return list

def clean_table(soup, label):
    """Put functions for RS and PS into one"""
    table = scrape_per_game_tables(soup, label)
    list = scraped_table_to_list(table)
    delete_column_headers(list)
    remove_blank_lines(list)
    adjustments_for_did_not_play_seasons(list)
    label_RS_or_PS(list, label)
    return list

def main():
    playerID = input('Enter Player ID: ')
    playerURL = determine_player_URL(playerID)
    playerPage = scrape_player_page(playerURL)
    RS = clean_table(playerPage, 'RS')
    PS = clean_table(playerPage, 'PS')
    combined = combine_RS_and_PS(RS, PS)
    add_sorting_qualifier(combined)
    sort_list(combined)
    print(combined)

if __name__ == "__main__":
    main()
