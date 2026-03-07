import re
import requests
import bs4
from datetime import datetime

class PlayoffScraper:
    def __init__(self):
        """
        Initializes the PlayoffScraper object.
        """
        pass

    def get_data(self, year):
        """
        Gets datetime object of playoff duration for a given year.
        ---
        Parameters:
            year: integer, representing year to scrape
        ---
        Returns start and end datetime objects.
        """

        url = f'https://en.wikipedia.org/wiki/{year}_NBA_playoffs'
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; nba-elo-scraper/1.0)'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = bs4.BeautifulSoup(response.text, 'lxml')
        try:
            if year == 2020:
                dates = (soup.find('body')
                            .find('div', class_='mw-page-container')
                            .find('div', class_='mw-page-container-inner')
                            .find('div', class_='mw-content-container')
                            .find('main', class_='mw-body')
                            .find('div', class_='mw-body-content')
                            .find('div', class_='mw-content-ltr mw-parser-output')
                            .find('table', class_='infobox vcard')
                            .find('tbody')
                            .find_all('tr')[3]
                            .find('td', class_='infobox-data')).text
            else:
                dates = (soup.find('body')
                            .find('div', class_='mw-page-container')
                            .find('div', class_='mw-page-container-inner')
                            .find('div', class_='mw-content-container')
                            .find('main', class_='mw-body')
                            .find('div', class_='mw-body-content')
                            .find('div', class_='mw-content-ltr mw-parser-output')
                            .find('table', class_='infobox vcard')
                            .find('tbody')
                            .find_all('tr')[1]
                            .find('td')).text
        except AttributeError:
            return None, None
        
        # Extract year with regex to handle varying Wikipedia date formats
        year_match = re.search(r'\b(\d{4})\b', dates)
        if not year_match:
            return None, None
        year_str = year_match.group(1)

        # Extract date range (handles both '–' en-dash and '-' hyphen)
        range_match = re.search(r'([A-Za-z]+ \d+)\s*[–-]\s*([A-Za-z]+ \d+)', dates)
        if not range_match:
            return None, None
        start_date_str = range_match.group(1) + ', ' + year_str
        end_date_str = range_match.group(2) + ', ' + year_str

        # Parse the start and end date strings into datetime objects
        try:
            start_date = datetime.strptime(start_date_str, '%B %d, %Y')
            end_date = datetime.strptime(end_date_str, '%B %d, %Y')
        except ValueError:
            return None, None

        # Return the datetime objects
        return start_date, end_date
        
