import pandas as pd
import numpy as np

class NBARater:
    def __init__(self):
        """
        Initializes the NBARater object by using a default Elo rating of 1200 for all teams.
        """
        team_names = [
            'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
            'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
            'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
            'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
            'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
            'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
            'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
            'Utah Jazz', 'Washington Wizards',
        ]
        
        # Initialize each team with a default ELO rating of 1200 using a dictionary comprehension
        self.teams = {team: np.array([1200]) for team in team_names}
        self.win_streaks = {team: 0 for team in team_names}


    @staticmethod
    def map_team_names(team_name):
        """
        Maps old team names to their current names.
        ---
        Parameters:
            team_name: str, name of the team.
        ---
        Returns the current name of the team.
        """
        name_changes = {
            'Charlotte Bobcats': 'Charlotte Hornets',
            'New Orleans Hornets': 'New Orleans Pelicans',
            'New Jersey Americans': 'Brooklyn Nets',
            'New York Nets': 'Brooklyn Nets',
            'New Jersey Nets': 'Brooklyn Nets',
            'Seattle SuperSonics': 'Oklahoma City Thunder',
            'Vancouver Grizzlies': 'Memphis Grizzlies',
            'Washington Bullets': 'Washington Wizards',
            'Chicago Zephyrs': 'Washington Wizards',
            'Capital Bullets': 'Washington Wizards',
            'Baltimore Bullets': 'Washington Wizards',
            'Chicago Packers': 'Washington Wizards',
            'New Orleans/Oklahoma City Hornets': 'New Orleans Pelicans',
            'New Orleans/OKC Hornets': 'New Orleans Pelicans',
            'Philadelphia Warriors': 'Golden State Warriors',
            'San Francisco Warriors': 'Golden State Warriors',
            'Fort Wayne Pistons': 'Detroit Pistons',
            'Minneapolis Lakers': 'Los Angeles Lakers',
            'Rochester Royals': 'Sacramento Kings',
            'Syracuse Nationals': 'Philadelphia 76ers',
            'Tri-Cities Blackhawks': 'Atlanta Hawks',
            'St. Louis Hawks': 'Atlanta Hawks',
            'Milwaukee Hawks': 'Atlanta Hawks',
            'Buffalo Braves': 'Los Angeles Clippers',
            'San Diego Clippers': 'Los Angeles Clippers',
            'Cincinnati Royals': 'Sacramento Kings',
            'Kansas City-Omaha Kings': 'Sacramento Kings',
            'Kansas City Kings': 'Sacramento Kings',
            'Denver Rockets': 'Denver Nuggets',
            'San Diego Rockets': 'Houston Rockets',
            'Dallas Chaparrals': 'San Antonio Spurs',
            'Texas Chapparals': 'San Antonio Spurs',
            'New Orleans Jazz': 'Utah Jazz',
        }
        return name_changes.get(team_name, team_name)
    

    @staticmethod
    def expectedResult(team1, team2):
        """
        Calculates the expected result of a game between two teams 
        with different ratings.
        ---
        Parameters:
            team1: float, rating of first team. 
            team2: float, rating of second team.
        ---
        Returns the expected result of the game.
        """
        return 10**(team1/400) / (10**(team1/400) + 10**(team2/400))


    def updateElo(self, original_rating, expected_score, actual_score, team, k=20):
        """
        Calculates the updated Elo of a team.
        ---
        Parameters:
            original_rating: float, original rating of the team.
            expected_score: float, expected result of the game the team partook in.
            actual_score: float, actual result of the game.
            team: str, name of the team.
            k: int, k-factor (the maximum possible adjustment of score per game)
        ---
        Returns the updated Elo rating of the team.
        """
        return original_rating + k * (actual_score - expected_score) + self.win_streak_bonus(team)
    

    def win_streak_bonus(self, team, base=1.1):
        """
        Adds a win streak bonus to the team's Elo rating using a 
        logarithmic approach.
        ---
        Parameters:
            team: str, name of the team.
            base: float, base value of the bonus.
        ---
        Returns the win streak bonus.
        """
        # Baseline of at least 3 wins to get a bonus
        win_streak = self.win_streaks[team]
        if win_streak < 3:
            return 0
        return (base ** (win_streak - 2)) - 1
    

    def eloSimulator(self, df):
        """
        Simulates an Elo rating simulator to given data.
        ---
        Parameters:
            df: pandas DataFrame object, contains NBA games.
        """
        for index, row in df.iterrows():
            team1_result = row['Win']
            team2_result = 1 - team1_result

            team1, team2 = row['Visitor'], row['Home']

            # Maps old team names to their current names
            team1 = self.map_team_names(team1)
            team2 = self.map_team_names(team2)

            # Calculates win streaks
            if team1_result == 1:
                self.win_streaks[team1] += 1
                self.win_streaks[team2] = 0
            else:
                self.win_streaks[team2] += 1
                self.win_streaks[team1] = 0

            # Calculates expected results
            team1_expected = self.expectedResult(self.teams[team1][-1], self.teams[team2][-1])
            team2_expected = self.expectedResult(self.teams[team2][-1], self.teams[team1][-1])

            # Updates Elo ratings
            team1_updated_elo = self.updateElo(self.teams[team1][-1], team1_expected, team1_result, team1)
            team2_updated_elo = self.updateElo(self.teams[team2][-1], team2_expected, team2_result, team2)

            # Ensures that Elo ratings do not go below 0
            if team1_updated_elo < 0:
                team1_updated_elo = 0
            elif team2_updated_elo < 0:
                team2_updated_elo = 0  

            # Appends updated Elo ratings to the teams' Elo data
            self.teams[team1] = np.append(self.teams[team1], 
                                          team1_updated_elo)
            self.teams[team2] = np.append(self.teams[team2], 
                                          team2_updated_elo)
        return self
            

    def getTeams(self):
        """
        Accessor function for teams' Elo data.
        ---
        Returns the team's Elo data.
        """
        return self.teams