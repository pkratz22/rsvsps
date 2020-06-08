# imports

import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd

# get URL for player

baseURL = 'https://www.basketball-reference.com/players/'

playerID = input('Enter Player ID: ')
playerInitial = playerID[0]
playerURLIdentifier = playerInitial + '/' + playerID

playerURL = baseURL + playerURLIdentifier + '.html'

# get player page info

playerPage = requests.get(playerURL)

soup = BeautifulSoup(playerPage.text, 'lxml')

# create data frames

perColumns = ['Season', 'Age', 'Tm', 'Lg', 'Pos', 'G', 'GS', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', '2P', '2PA', '2P%', 'eFG%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
advancedColumns = ['Season', 'Age', 'Tm', 'Pos', 'G', 'MP', 'PER', 'TS%', '3PAr', 'FTr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV', 'USG%', '', 'OWS', 'DWS', 'WS', 'WS/48', '', 'OBPM', 'DBPM', 'BPM', 'VORP']

dfRSperGame = pd.DataFrame(columns = perColumns)
dfRSper36 = pd.DataFrame(columns = perColumns)
dfRSper100 = pd.DataFrame(columns = perColumns)
dfRSadvanced = pd.DataFrame(columns = advancedColumns)

dfPSperGame = pd.DataFrame(columns = perColumns)
dfPSper36 = pd.DataFrame(columns = perColumns)
dfPSper100 = pd.DataFrame(columns = perColumns)
dfPSadvanced = pd.DataFrame(columns = advancedColumns)

# collect data

for comment in soup.find_all(string = lambda text:isinstance(text,Comment)):
    data = BeautifulSoup(comment, 'lxml')
    #print(data)
    #print('----------------------------------------------------------------------------')
    for items in data.select('table.row_summable tr'):
        tds = [item.get_text(strip=True) for item in items.select('th,td')]
        print(tds)

