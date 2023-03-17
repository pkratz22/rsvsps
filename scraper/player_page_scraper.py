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


def scrape_tables(soup, label, table_type):
    """Scrape the PerGameTables from the Player Page.

    Args:
        soup: soup of player page
        label: regular season or post-season
        table_type: table type to scrape

    Returns:
        soup for table
    """
    qualifier_map = {'RS': '', 'PS': 'playoffs_'}
    for table in soup:
        if table.attrs['id'] == '{label}{tabletype}'.format(label=qualifier_map.get(label), tabletype=table_type):
            return table


def scraped_table_to_list(table):
    """Convert the scraped table to a multidimensional list.

    Args:
        table: table to scrape

    Returns:
        data scraped from soup of table
    """
    return [[cell.text for cell in row.find_all(['th', 'td'])] for row in table.find_all('tr')]