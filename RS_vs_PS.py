# imports

import re
import requests
from bs4 import BeautifulSoup, SoupStrainer, Comment
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

# RSperGame
RSperGame = soup.find(id='per_game')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in RSperGame.find_all("tr")]
RSperGamedf = pd.DataFrame(tab_data)
RSperGamedf.columns = RSperGamedf.iloc[0,:]
RSperGamedf.drop(index = 0, inplace = True)
print(RSperGamedf)

# RSperMin
RSperMin = soup.find(id='per_minute')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in RSperMin.find_all("tr")]
RSperMindf = pd.DataFrame(tab_data)
RSperMindf.columns = RSperMindf.iloc[0,:]
RSperMindf.drop(index = 0, inplace = True)
print(RSperMindf)

# RSperPoss
RSperPoss = soup.find(id='per_poss')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in RSperPoss.find_all("tr")]
RSperPossdf = pd.DataFrame(tab_data)
RSperPossdf.columns = RSperPossdf.iloc[0,:]
RSperPossdf.drop(index = 0, inplace = True)
print(RSperPossdf)

# RSadvanced
RSadvanced = soup.find(id='advanced')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in RSadvanced.find_all("tr")]
RSadvanceddf = pd.DataFrame(tab_data)
RSadvanceddf.columns = RSadvanceddf.iloc[0,:]
RSadvanceddf.drop(index = 0, inplace = True)
print(RSadvanceddf)

# PSperGame
PSperGame = soup.find(id='playoffs_per_game')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in PSperGame.find_all("tr")]
PSperGamedf = pd.DataFrame(tab_data)
PSperGamedf.columns = PSperGamedf.iloc[0,:]
PSperGamedf.drop(index = 0, inplace = True)
print(PSperGamedf)

# PSperMin
PSperMin = soup.find(id='playoffs_per_minute')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in PSperMin.find_all("tr")]
PSperMindf = pd.DataFrame(tab_data)
PSperMindf.columns = PSperMindf.iloc[0,:]
PSperMindf.drop(index = 0, inplace = True)
print(PSperMindf)

# PSperPoss
PSperPoss = soup.find(id='playoffs_per_poss')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in PSperPoss.find_all("tr")]
PSperPossdf = pd.DataFrame(tab_data)
PSperPossdf.columns = PSperPossdf.iloc[0,:]
PSperPossdf.drop(index = 0, inplace = True)
print(PSperPossdf)

# PSadvanced
PSadvanced = soup.find(id='playoffs_advanced')
tab_data = [[cell.text for cell in row.find_all(["th","td"])] for row in PSadvanced.find_all("tr")]
PSadvanceddf = pd.DataFrame(tab_data)
PSadvanceddf.columns = PSadvanceddf.iloc[0,:]
PSadvanceddf.drop(index = 0, inplace = True)
print(PSadvanceddf)
