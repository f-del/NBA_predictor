import random
import string
import time

import requests
from bs4 import BeautifulSoup

# Base URL for player pages
BASE_URL = "https://www.basketball-reference.com/players/{letter}/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
RANGE_LIMIT = 1  # Number of players to scrape per letter (if needed)

def fetch_page(url, retries=3, delay_min=1, delay_max=3):
    """Fetches a webpage and returns the response text."""
    try:

        for attempt in range(retries):
            try:
                print(f"Request headers for {url}: {HEADERS}")
                response = requests.get(url, headers=HEADERS)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        sleep_time = int(retry_after)
                        print(f"Retry-After header value: {retry_after} seconds")
                    else:
                        sleep_time = min(2 ** attempt, delay_max)
                    print(f"Rate limit reached. Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == retries - 1:
                    print(f"Failed to fetch {url} after {retries} attempts: {e}")
                    return None
                sleep_time = min(2**attempt, delay_max)
                print(f"Error fetching {url}. Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_player_row(row):
    """Parses a row from the player table and returns player data."""
    try:
        player_name = row.select_one('th[data-stat="player"] a').text
        player_link = "https://www.basketball-reference.com" + row.select_one('th[data-stat="player"] a')['href']
        year_from = int(row.select_one('td[data-stat="year_min"]').text)
        return player_name, player_link, year_from
    except (AttributeError, ValueError) as e:
        print(f"Error parsing player row: {e}")
        return None, None, None

def fetch_player_details(player_link, retries=3, delay_min=1, delay_max=3):
    """Fetches and parses the details of an individual player."""
    player_page = fetch_page(player_link, retries, delay_min, delay_max)

    time.sleep(random.uniform(1, 3))
    if not player_page:
        return "N/A", "N/A", "N/A"

    player_soup = BeautifulSoup(player_page, 'html.parser')
    try:
        position = player_soup.select_one('span[itemprop="role"]').text if player_soup.select_one('span[itemprop="role"]') else "N/A"
        height = player_soup.select_one('span[itemprop="height"]').text if player_soup.select_one('span[itemprop="height"]') else "N/A"
        weight = player_soup.select_one('span[itemprop="weight"]').text if player_soup.select_one('span[itemprop="weight"]') else "N/A"
        return position, height, weight
    except AttributeError as e:
        print(f"Error parsing player details: {e}")
        return "N/A", "N/A", "N/A"

def scrape_players_for_letter(letter):
    """Scrapes players for a given letter and returns a list of player dictionaries."""
    players = []
    url = BASE_URL.format(letter=letter)
    time.sleep(random.uniform(1, 3))
    page_content = fetch_page(url)
    if not page_content:
        return players

    soup = BeautifulSoup(page_content, 'html.parser')
    table_rows = soup.select('#players tbody tr')

    for row in table_rows:
        player_name, player_link, year_from = parse_player_row(row)
        if not player_name or year_from < 1980:
            continue

        position, height, weight = fetch_player_details(player_link)
        players.append({
            "name": player_name,
            "link": player_link,
            "position": position,
            "height": height,
            "weight": weight
        })

    return players

def main():
    """Main function to scrape all players and display results."""
    all_players = []
    letters_range = string.ascii_lowercase  # List of letters from a to z

    for letter in letters_range:
        print(f"Scraping letter: {letter}")
        players_for_letter = scrape_players_for_letter(letter)
        all_players.extend(players_for_letter)
        time.sleep(random.uniform(1, 3))  # Random delay for rate limiting

    print(f"Total players retrieved: {len(all_players)}")
    for player in all_players:
        print(player)

if __name__ == "__main__":
    main()

