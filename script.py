import pandas as pd
import numpy as np

class NBARater:
    def __init__(self):
        self.teams = {
            'Atlanta Hawks': np.array([1200]), 
            'Boston Celtics': np.array([1200]), 
            'Brooklyn Nets': np.array([1200]), 
            'Charlotte Hornets': np.array([1200]), 
            'Chicago Bulls': np.array([1200]), 
            'Cleveland Cavaliers': np.array([1200]), 
            'Dallas Mavericks': np.array([1200]), 
            'Denver Nuggets': np.array([1200]), 
            'Detroit Pistons': np.array([1200]), 
            'Golden State Warriors': np.array([1200]), 
            'Houston Rockets': np.array([1200]), 
            'Indiana Pacers': np.array([1200]), 
            'Los Angeles Clippers': np.array([1200]), 
            'Los Angeles Lakers': np.array([1200]), 
            'Memphis Grizzlies': np.array([1200]), 
            'Miami Heat': np.array([1200]), 
            'Milwaukee Bucks': np.array([1200]), 
            'Minnesota Timberwolves': np.array([1200]), 
            'New Orleans Pelicans': np.array([1200]), 
            'New York Knicks': np.array([1200]), 
            'Oklahoma City Thunder': np.array([1200]), 
            'Orlando Magic': np.array([1200]), 
            'Philadelphia 76ers': np.array([1200]), 
            'Phoenix Suns': np.array([1200]), 
            'Portland Trail Blazers': np.array([1200]), 
            'Sacramento Kings': np.array([1200]), 
            'San Antonio Spurs': np.array([1200]), 
            'Toronto Raptors': np.array([1200]), 
            'Utah Jazz': np.array([1200]), 
            'Washington Wizards': np.array([1200]), 
        }

    @staticmethod
    def expectedResult(team1, team2):
        return 10**(team1/400) / (10**(team1/400) + 10**(team2/400))

    @staticmethod
    def updateElo(original_rating, expected_score, actual_score, k=20):
        return original_rating + k * (actual_score - expected_score)

    def eloSimulator(self, df):
        for index, row in df.iterrows():
            team1_result = row['Win']
            team2_result = 1 - team1_result

            team1, team2 = row['Visitor'], row['Home']

            if team1 == 'Charlotte Bobcats':
                team1 = 'Charlotte Hornets'
            if team2 == 'Charlotte Bobcats':
                team2 = 'Charlotte Hornets'
            if team1 == 'New Orleans Hornets':
                team1 = 'New Orleans Pelicans'
            if team2 == 'New Orleans Hornets':
                team2 = 'New Orleans Pelicans'

            team1_expected = self.expectedResult(self.teams[team1][-1], self.teams[team2][-1])
            team2_expected = self.expectedResult(self.teams[team2][-1], self.teams[team1][-1])

            self.teams[team1] = np.append(self.teams[team1], 
                                          self.updateElo(self.teams[team1][-1], 
                                                          team1_expected, 
                                                          team1_result))
            self.teams[team2] = np.append(self.teams[team2], 
                                          self.updateElo(self.teams[team2][-1], 
                                                         team2_expected, 
                                                         team2_result))
            
    def getTeams(self):
        return self.teams