# imports

import re
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

playerPage = requests.get(playerURL).text

soup = BeautifulSoup(re.sub('<!--|-->','', playerPage), 'lxml')
