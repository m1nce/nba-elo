import pandas as pd
import numpy as np

HOME_ADVANTAGE = 100  # Elo points added to home team's effective rating
REVERSION_FACTOR = 1 / 3  # Fraction to pull toward mean between seasons


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

        # Use lists for O(1) appends; converted to numpy arrays in getTeams()
        self.teams = {team: [1200] for team in team_names}
        self.win_streaks = {team: 0 for team in team_names}
        self.game_log = []


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
    def expectedResult(visitor_rating, home_rating):
        """
        Calculates the expected result for the visitor.
        Home team receives a HOME_ADVANTAGE Elo bonus to their effective rating.
        ---
        Parameters:
            visitor_rating: float, Elo rating of the visiting team.
            home_rating: float, Elo rating of the home team.
        ---
        Returns the visitor's expected score (probability of winning).
        """
        adjusted_home = home_rating + HOME_ADVANTAGE
        return 10**(visitor_rating / 400) / (10**(visitor_rating / 400) + 10**(adjusted_home / 400))


    def win_streak_bonus(self, team, base=1.1):
        """
        Computes a win streak bonus using a logarithmic approach.
        Requires a minimum streak of 3 to activate.
        ---
        Parameters:
            team: str, name of the team.
            base: float, base of the exponential bonus.
        ---
        Returns the bonus Elo points to award the winner (and subtract from the loser).
        """
        win_streak = self.win_streaks[team]
        if win_streak < 3:
            return 0
        return (base ** (win_streak - 2)) - 1


    def _get_season(self, date):
        """Returns the season start year for a given date (seasons begin in October)."""
        return date.year if date.month >= 10 else date.year - 1


    def _apply_mean_reversion(self, mean=1200):
        """Pulls every team's current rating 1/3 of the way toward the mean in-place."""
        for team in self.teams:
            current = self.teams[team][-1]
            self.teams[team][-1] = current + REVERSION_FACTOR * (mean - current)


    def eloSimulator(self, df):
        """
        Simulates Elo ratings across all games in the DataFrame.
        ---
        Parameters:
            df: pandas DataFrame with columns: Date, Visitor, Home, Win, Notes.
        """
        current_season = None

        for _, row in df.iterrows():
            date = pd.to_datetime(row['Date'])
            season = self._get_season(date)

            # Apply mean reversion at each season boundary
            if current_season is not None and season != current_season:
                self._apply_mean_reversion()
            current_season = season

            visitor_result = row['Win']
            home_result = 1 - visitor_result

            visitor = self.map_team_names(row['Visitor'])
            home = self.map_team_names(row['Home'])

            # Update win streaks and compute streak bonus for the winner (zero-sum)
            if visitor_result == 1:
                self.win_streaks[visitor] += 1
                self.win_streaks[home] = 0
                streak_bonus = self.win_streak_bonus(visitor)
            elif visitor_result == 0:
                self.win_streaks[home] += 1
                self.win_streaks[visitor] = 0
                streak_bonus = self.win_streak_bonus(home)
            else:  # tie
                self.win_streaks[visitor] = 0
                self.win_streaks[home] = 0
                streak_bonus = 0

            # Expected results (home court advantage baked into expectedResult)
            old_visitor_rating = self.teams[visitor][-1]
            old_home_rating = self.teams[home][-1]
            visitor_expected = self.expectedResult(old_visitor_rating, old_home_rating)
            home_expected = 1 - visitor_expected

            k = 48 if row['Notes'] == 'Playoffs' else 32

            # Base Elo update (zero-sum: home_expected = 1 - visitor_expected)
            visitor_new = old_visitor_rating + k * (visitor_result - visitor_expected)
            home_new = old_home_rating + k * (home_result - home_expected)

            # Apply streak bonus zero-sum: winner gains, loser loses the same amount
            if visitor_result == 1:
                visitor_new += streak_bonus
                home_new -= streak_bonus
            elif visitor_result == 0:
                home_new += streak_bonus
                visitor_new -= streak_bonus

            # Floor at 0
            if visitor_new < 0:
                visitor_new = 0
            if home_new < 0:
                home_new = 0

            self.teams[visitor].append(visitor_new)
            self.teams[home].append(home_new)

            self.game_log.append({
                'date': date.strftime('%Y-%m-%d'),
                'season': season,
                'visitor': visitor,
                'home': home,
                'visitor_before': old_visitor_rating,
                'home_before': old_home_rating,
                'visitor_after': visitor_new,
                'home_after': home_new,
                'visitor_delta': visitor_new - old_visitor_rating,
                'home_delta': home_new - old_home_rating,
                'win_prob_visitor': visitor_expected,
                'result': 'visitor' if visitor_result == 1 else 'home',
                'notes': row['Notes'],
            })

        return self


    def getTeams(self):
        """
        Accessor for teams' Elo history.
        ---
        Returns a dict of team name -> numpy array of rating history.
        """
        return {team: np.array(ratings) for team, ratings in self.teams.items()}

    def getGameLog(self):
        """
        Returns a DataFrame of per-game ELO changes recorded during eloSimulator().
        """
        return pd.DataFrame(self.game_log)
