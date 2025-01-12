import requests
from bs4 import BeautifulSoup
import time
import string
import csv

# Base URL for player pages
BASE_URL = "https://www.basketball-reference.com/players/{letter}/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
RANGE_LIMIT = 1  # Number of players to scrape per letter for testing
RATE_LIMIT_SECONDS = 5  # Time to wait between requests
def fetch_page(url):
    """Fetches a webpage and returns the response text."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_player_row(row):
    """Parses a row from the players table and returns player data."""
    try:
        player_name = row.select_one('th[data-stat="player"] a').text
        player_link = "https://www.basketball-reference.com" + row.select_one('th[data-stat="player"] a')['href']
        year_from = int(row.select_one('td[data-stat="year_min"]').text)
        return player_name, player_link, year_from
    except (AttributeError, ValueError) as e:
        print(f"Error parsing player row: {e}")
        return None, None, None

def fetch_player_data(player_link):
    """Fetches and parses the details and stats of an individual player from a single page."""
    player_page = fetch_page(player_link)
    if not player_page:
        return {"details": None, "stats": []}

    player_soup = BeautifulSoup(player_page, 'html.parser')

    # Extract player details
    try:
        info_div = player_soup.find('div', id='info')
        if not info_div:
            print(f"No info div found for {player_link}")
            return {"details": None, "stats": []}

        paragraphs = info_div.find_all('p')

        # Preprocess content to remove excessive newlines
        paragraphs_text = [p.text.replace('\n', ' ').replace(' ▪', '') for p in paragraphs]

        # Extract data using index based on the static structure
        name = player_soup.select_one('h1 span').text.strip() if player_soup.select_one('h1 span') else "N/A"
        position = paragraphs_text[3].split("Position:")[1].split("Shoots:")[0].strip() if len(
            paragraphs_text) > 3 else "N/A"
        height_weight = paragraphs_text[4] if len(paragraphs_text) > 4 else "N/A"
        height, weight = "N/A", "N/A"
        if height_weight:
            parts = height_weight.split(',')
            height = parts[0].strip() if len(parts) > 0 else "N/A"
            weight = parts[1].strip().split("lb")[0] if len(parts) > 1 else "N/A"
        birthdate = paragraphs_text[5].split("Born:")[1].split("in")[0].strip() if len(paragraphs_text) > 5 else "N/A"
        nba_debut = paragraphs_text[9].split("NBA Debut:")[1].strip() if len(paragraphs_text) > 9 else "N/A"
    except AttributeError as e:
        print(f"Error parsing player details: {e}")
        name, position, height, weight, birthdate, nba_debut = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

    details = {
        "Name": name,
        "Position": position,
        "Height": height,
        "Weight": weight,
        "Birthdate": birthdate,
        "NBA Debut": nba_debut
    }

    return {"details": details, "stats": []}

def scrape_players_for_letter(letter):
    """Scrapes players for a given letter and returns player details and stats."""
    players = []
    stats_collection = {}
    url = BASE_URL.format(letter=letter)
    page_content = fetch_page(url)
    if not page_content:
        return players, stats_collection

    soup = BeautifulSoup(page_content, 'html.parser')
    table_rows = soup.select('#players tbody tr')

    for index, row in enumerate(table_rows):
        if index >= RANGE_LIMIT:
            break

        player_name, player_link, year_from = parse_player_row(row)
        if not player_name or year_from < 1980:
            continue

        time.sleep(RATE_LIMIT_SECONDS)  # Rate limiting between player detail requests
        player_data = fetch_player_data(player_link)

        players.append({
            "name": player_data["details"]["Name"],
            "link": player_link,
            "position": player_data["details"]["Position"],
            "height": player_data["details"]["Height"],
            "weight": player_data["details"]["Weight"],
            "birthdate": player_data["details"]["Birthdate"],
            "nba_debut": player_data["details"]["NBA Debut"]
        })

    return players, stats_collection

def save_to_csv(players, stats):
    """Saves players and their stats to CSV files."""
    # Save players data
    with open('players.csv', 'w', newline='', encoding='utf-8') as players_file:
        writer = csv.DictWriter(players_file, fieldnames=["name", "link", "position", "height", "weight", "birthdate", "nba_debut"])
        writer.writeheader()
        writer.writerows(players)

    # Save stats data
    with open('player_stats.csv', 'w', newline='', encoding='utf-8') as stats_file:
        fieldnames = ["player_name", "season", "data-stat", "value"]
        writer = csv.writer(stats_file)
        writer.writerow(["player_name", "season", "data-stat", "value"])

        for player_name, player_stats in stats.items():
            for season_stats in player_stats:
                for stat, value in season_stats.items():
                    season = season_stats.get('season', 'N/A')
                    writer.writerow([player_name, season, stat, value])

def main():
    """Main function to scrape all players and their stats."""
    all_players = []
    all_stats = {}
    letters_range = string.ascii_lowercase  # List of letters from a to z

    for letter in letters_range:
        print(f"Scraping letter: {letter}")
        players_for_letter, stats_for_letter = scrape_players_for_letter(letter)
        all_players.extend(players_for_letter)
        all_stats.update(stats_for_letter)
        time.sleep(RATE_LIMIT_SECONDS)  # Rate limiting to avoid overloading the server

        break

    print(f"Total players retrieved: {len(all_players)}")
    save_to_csv(all_players, all_stats)
    print("Data saved to CSV files.")

if __name__ == "__main__":
    main()
