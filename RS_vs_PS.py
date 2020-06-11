# imports

import re
import requests
from bs4 import BeautifulSoup, SoupStrainer, Comment
import numpy as np
import pandas as pd

# get URL for player

baseURL = 'https://www.basketball-reference.com/players/'

playerID = input('Enter Player ID: ')
playerInitial = playerID[0]
playerURLIdentifier = playerInitial + '/' + playerID

playerURL = baseURL + playerURLIdentifier + '.html'

# get player page info

playerPage = requests.get(playerURL).text
tables = SoupStrainer('table')
soup = BeautifulSoup(re.sub('<!--|-->','', playerPage), 'lxml', parse_only=tables)

# create column headers

perGameColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'RS or PS']
perMinColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
perPossColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', '', 'ORtg', 'DRtg']
advancedColumns = ['Season', 'Age', 'Tm', 'Pos', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV', 'USG%', '', 'OWS', 'DWS', 'WS', 'WS/48', '', 'OBPM', 'DBPM', 'BPM', 'VORP']

# per Game

RSperGame = soup.find(id='per_game')
PSperGame = soup.find(id='playoffs_per_game')
RS = [[cell.text for cell in row.find_all(["th","td"])] for row in RSperGame.find_all("tr")]
PS = [[cell.text for cell in row.find_all(["th","td"])] for row in PSperGame.find_all("tr")]
del RS[0]
del PS[0]
for year in RS:
    year.extend(['RS'])
for year in PS:
    year.extend(['PS'])
perGameData = RS+PS
perGameDF = pd.DataFrame(perGameData, columns = perGameColumns)

# remove empty rows

perGameDF.replace('', np.nan, inplace = True)
perGameDF.dropna(subset=['Season'], inplace=True)

# sorting

perGameDF['Season, Team, or Career'] = np.select([(perGameDF['Season'].str.contains("season")),(perGameDF['Season'].str.contains("Career"))], [1, 2], default = 0)
perGameDF['Sort'] = np.select([perGameDF['Season, Team, or Career'] == 0, perGameDF['Season, Team, or Career'] == 1, perGameDF['Season, Team, or Career'] == 2], [perGameDF['Season'], perGameDF['Tm'], 'ZZZ'], default = 'Error')

perGameDF.sort_values(by=['Season, Team, or Career', 'Sort', 'RS or PS'], ascending = [True, True, False], inplace = True)

# add rows for differences

# add row to end of dataframe
perGameDF = perGameDF.append(pd.Series(), ignore_index = True)

# add row to separate years/teams/career

numDiffRows = -1

for index in range(len(perGameDF)-1, 1, -1):
    if(perGameDF.loc[index, 'Sort'] != perGameDF.loc[index-1, 'Sort']):
        numDiffRows+=1
        
for i in range(numDiffRows):
    perGameDF = perGameDF.append(pd.Series(), ignore_index = True)

perGameDF.drop(columns = ['Sort'], inplace = True)

print(perGameDF)
