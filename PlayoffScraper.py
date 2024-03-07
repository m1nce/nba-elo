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
        response = requests.get(url)
        response.raise_for_status()

        soup = bs4.BeautifulSoup(response.text, 'lxml')
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
        
        # Extract the year
        date = dates.split(', ')
        year = date[1]
        # Extract and format the start and end date strings
        start_date_str = date[0].split('–')[0].strip() + ', ' + year
        end_date_str = date[0].split('–')[1].strip() + ', ' + year

        # Parse the start and end date strings into datetime objects
        start_date = datetime.strptime(start_date_str, '%B %d, %Y')
        end_date = datetime.strptime(end_date_str, '%B %d, %Y')

        # Return the datetime objects
        return start_date, end_date
        
