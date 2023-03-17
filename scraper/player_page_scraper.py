import requests
from bs4 import BeautifulSoup, SoupStrainer


def scrape_player_page(player_url):
    """Scrape Player Page for tables.

    Raises:
        SystemExit: HTTPError for player ID
    
    Args:
        player_url: URL to scrape

    Returns:
        soup of scraped page
    """
    try:
        page_request = requests.get(player_url)
        page_request.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit from err
    player_page = page_request.text
    tables = SoupStrainer(id=[
        'per_game',
        'playoffs_per_game',
        'per_minute',
        'playoffs_per_minute',
        'per_poss',
        'playoffs_per_poss',
        'advanced',
        'playoffs_advanced',
    ])
    player_page = player_page.replace('<!--', '').replace('-->', '')

    soup = BeautifulSoup(player_page, 'lxml', parse_only=tables)
    return soup.contents