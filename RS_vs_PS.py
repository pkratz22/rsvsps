# imports

from bs4 import BeautifulSoup, SoupStrainer, Comment
import re
import requests
import operator

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
    if year[0] == "":
        RS.remove(year)
for year in PS:
    if year[0] == "":
        PS.remove(year)
for year in RS:
    if("Did Not Play" in year[2]):
        for i in range(27):
            year.append("")
RS = list(filter(None, RS))
PS = list(filter(None, PS))
for year in RS:
    year.extend(['RS'])
for year in PS:
    year.extend(['PS'])
perGame = RS+PS

for year in perGame:
    if "season" in year[0]:
        year.insert(len(year), "1"+year[2])
    elif "Career" in year[0]:
        year.insert(len(year), "2")
    else:
        year.insert(len(year), "0"+year[0])

perGame = sorted(perGame, key=lambda x: (x[31]))

print(perGame)
