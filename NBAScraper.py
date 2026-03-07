import pandas as pd
import requests
import bs4
import time
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import argparse
from PlayoffScraper import PlayoffScraper

DB_PATH = Path('data') / 'nba.db'


def init_db(db_path=DB_PATH):
    """Creates the games table and indexes in db_path if they don't exist; returns a Connection."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            season          INTEGER NOT NULL,
            date            TEXT NOT NULL,
            start_time      TEXT,
            visitor         TEXT NOT NULL,
            visitor_points  INTEGER,
            home            TEXT NOT NULL,
            home_points     INTEGER,
            box_score       TEXT,
            overtime        TEXT,
            attendance      TEXT,
            arena           TEXT,
            notes           TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_season ON games(season)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON games(date)")
    conn.commit()
    return conn


def season_exists(conn, season):
    """Returns True if the season already has rows in the DB."""
    cursor = conn.execute("SELECT COUNT(*) FROM games WHERE season = ?", (season,))
    return cursor.fetchone()[0] > 0


def find_gaps(beginning: int, end: int, db_path: Path = DB_PATH) -> list:
    """Return seasons in [beginning, end] not present in the DB."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT DISTINCT season FROM games")
    present = {row[0] for row in cursor.fetchall()}
    conn.close()
    return [s for s in range(beginning, end + 1) if s not in present]


def insert_season(conn, season, df):
    """Bulk-inserts a season's DataFrame rows into the games table."""
    dates = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
    visitor_pts = pd.to_numeric(df['Visitor Points'], errors='coerce')
    home_pts = pd.to_numeric(df['Home Points'], errors='coerce')

    def _s(v):
        if v is None:
            return None
        try:
            if pd.isna(v):
                return None
        except (TypeError, ValueError):
            pass
        s = str(v).strip()
        return s if s else None

    records = [
        (
            season,
            dates.iloc[i],
            _s(df['Start Time (ET)'].iloc[i]),
            _s(df['Visitor'].iloc[i]),
            None if pd.isna(visitor_pts.iloc[i]) else int(visitor_pts.iloc[i]),
            _s(df['Home'].iloc[i]),
            None if pd.isna(home_pts.iloc[i]) else int(home_pts.iloc[i]),
            _s(df['Box Score'].iloc[i]),
            _s(df['Overtime'].iloc[i]),
            _s(df['Attendance'].iloc[i]),
            _s(df['Arena'].iloc[i]),
            _s(df['Notes'].iloc[i]),
        )
        for i in range(len(df))
    ]
    conn.executemany("""
        INSERT INTO games (season, date, start_time, visitor, visitor_points, home, home_points,
                           box_score, overtime, attendance, arena, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, records)
    conn.commit()


def migrate_csv(conn, csv_dir=Path('data')):
    """Reads CSVs in csv_dir, derives season per row, and inserts missing seasons into the DB."""
    csv_dir = Path(csv_dir)
    total = 0
    for csv_file in sorted(csv_dir.glob('*.csv')):
        df = pd.read_csv(csv_file)
        df['Date'] = pd.to_datetime(df['Date'])
        # Season starting year: Oct+ of year Y → season Y; earlier months → season Y-1
        df['_season'] = df['Date'].apply(lambda d: d.year if d.month >= 9 else d.year - 1)
        for season, sdf in df.groupby('_season'):
            if season_exists(conn, season):
                tqdm.write(f"  Season {season}-{season+1} already in DB, skipping migration")
                continue
            insert_season(conn, season, sdf.drop(columns=['_season']).reset_index(drop=True))
            total += len(sdf)
            tqdm.write(f"  Migrated season {season}-{season+1}: {len(sdf)} games")
    print(f"Migration complete: {total} rows inserted.")


class NBAScraper:
    # Class-level rate limiter: serializes requests to basketball-reference.com
    # with a minimum interval to comply with their crawler policy.
    _bball_ref_lock = threading.Lock()
    _last_bball_ref_request = 0.0
    _min_bball_ref_interval = 5.0  # seconds between requests
    _db_write_lock = threading.Lock()

    def __init__(self):
        """
        Initializes the NBAScraper object.
        """
        pass

    def _rate_limited_get(self, url, retries=3):
        """
        Makes a GET request to basketball-reference.com, blocking until the
        minimum interval since the last request has elapsed. Retries on 429.
        """
        for attempt in range(retries):
            with NBAScraper._bball_ref_lock:
                elapsed = time.time() - NBAScraper._last_bball_ref_request
                if elapsed < NBAScraper._min_bball_ref_interval:
                    time.sleep(NBAScraper._min_bball_ref_interval - elapsed)
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                })
                NBAScraper._last_bball_ref_request = time.time()

            if response.status_code == 429:
                wait = 10 * (attempt + 1)
                tqdm.write(f"  Rate limited (429), waiting {wait}s before retry...")
                time.sleep(wait)
                continue
            return response

        response.raise_for_status()
        return response

    @staticmethod
    def allowed_by_robots_txt(url):
        """
        Returns a boolean value representing if a url is allowed
        to be scraped, according to the site's robots.txt
        ---
        Parameters:
            url: string representing url to scrape
        ---
        Returns a boolean value.
        """
        # Get robots.txt
        url_split = url.split("/")
        robots_txt_url = url_split[0] + '//' + url_split[2] + '/robots.txt'

        response = requests.get(robots_txt_url)
        response.raise_for_status()

        lines = response.text.split('\n')

        user_agent_reached = False

        for line in lines:
            if line.strip() == 'User-agent: *':
                user_agent_reached = True

            if line.lower().startswith('disallow') and user_agent_reached:
                # Check if the URL is disallowed
                disallowed_path = line.split(':', 1)[1].strip()
                if disallowed_path == '/':
                    break
                if disallowed_path in url:
                    return False

        # If no specific rule is found, the URL is allowed
        return True

    def get_data(self, url, start_playoff, end_playoff):
        """
        Creates DataFrame containing a month's amount of data from url.
        ---
        Parameters:
            url: string representing url to scrape
            start_playoff: datetime, start of playoffs
            end_playoff: datetime, end of playoffs
        ---
        Returns a DataFrame containing the data.
        """
        response = self._rate_limited_get(url)

        if response.status_code == 200:
            html_content = response.text
        else:
            raise Exception(f"Error: Unable to fetch content. Status code: {response.status_code}.")

        # create soup object and get only 'tr' tags
        page = bs4.BeautifulSoup(html_content, features='lxml')

        # Try modern div chain first; fall back to any schedule table for older pages
        try:
            rows = (page
                    .find('body', class_='bbr')
                    .find('div', {'id': 'wrap'})
                    .find('div', {'id': 'content'})
                    .find('div', {'id': 'all_schedule'})
                    .find('div', {'id': 'div_schedule'})
                    .find('tbody')
                    .find_all('tr'))
        except AttributeError:
            table = page.find('table', {'id': 'schedule'}) or page.find('table')
            rows = table.find('tbody').find_all('tr') if table else []

        # collect data
        date, start, visitor, visitor_pts, home, home_pts, box_score, ot, attend, arena, notes = [], [], [], [], [], [], [], [], [], [], []
        for game in rows:
            ths = game.find_all('th')
            tds = game.find_all('td')

            # Skip header/separator rows (no date th or no tds)
            if not ths or not tds:
                continue
            try:
                game_date = datetime.strptime(ths[0].text.strip(), '%a, %b %d, %Y')
            except ValueError:
                continue

            # Detect format: modern pages (2008+) have 11 TDs with start time at TD[0];
            # old pages (pre-2008) have 10 TDs with visitor team at TD[0].
            is_modern = len(tds) >= 11

            if is_modern:
                start_time   = tds[0].text
                visitor_team = tds[1].text
                v_pts        = tds[2].text
                home_team    = tds[3].text
                h_pts        = tds[4].text
                box_td       = tds[5]
                ot_val       = tds[6].text
                attend_val   = tds[7].text
                arena_val    = tds[8].text
                note_val     = tds[9].text
            else:
                start_time   = ''
                visitor_team = tds[0].text
                v_pts        = tds[1].text
                home_team    = tds[2].text
                h_pts        = tds[3].text
                box_td       = tds[4]
                ot_val       = tds[5].text
                attend_val   = tds[6].text
                arena_val    = tds[7].text if len(tds) > 7 else ''
                note_val     = tds[8].text if len(tds) > 8 else ''

            box_a = box_td.find('a')
            box_url = ('https://www.basketball-reference.com/' + box_a.get('href')) if box_a else ''

            # change note to 'Playoffs' if playoffs have started
            if start_playoff and start_playoff <= game_date <= end_playoff:
                note_val = 'Playoffs'

            date.append(game_date)
            start.append(start_time)
            visitor.append(visitor_team)
            visitor_pts.append(v_pts)
            home.append(home_team)
            home_pts.append(h_pts)
            box_score.append(box_url)
            ot.append(ot_val)
            attend.append(attend_val)
            arena.append(arena_val)
            notes.append(note_val)

        # create DataFrame
        data = {'Date': date,
                'Start Time (ET)': start,
                'Visitor': visitor,
                'Visitor Points': visitor_pts,
                'Home': home,
                'Home Points': home_pts,
                'Box Score': box_score,
                'Overtime': ot,
                'Attendance': attend,
                'Arena': arena,
                'Notes': notes}
        return pd.DataFrame(data)

    def nba_season(self, year):
        """
        Creates DataFrame for a specific year.
        ---
        Parameters:
            year: integer, representing what year to scrape
        ---
        Returns a DataFrame containing the data.
        """
        season_label = f"{year - 1}-{year}"
        df = pd.DataFrame()
        months = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']

        playoff_scraper = PlayoffScraper()
        start_playoff, end_playoff = None, None
        if year <= datetime.now().year:
            start_playoff, end_playoff = playoff_scraper.get_data(year)

        for month in months:
            url = f'https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html'
            try:
                month_df = self.get_data(url, start_playoff, end_playoff)
                df = pd.concat([df, month_df], ignore_index=True)
            except Exception:
                pass

        playoff_str = (f", playoffs {start_playoff.strftime('%b %d')}–{end_playoff.strftime('%b %d')}"
                       if start_playoff else "")
        tqdm.write(f"  [{season_label}] {len(df)} games{playoff_str}")
        return df

    def _scrape_season(self, year, db_path, force):
        """Fetches a single season; returns (year, df) or (year, None) if already in DB."""
        # Open a per-thread read connection just for the existence check
        conn_read = sqlite3.connect(db_path)
        exists = season_exists(conn_read, year)
        conn_read.close()

        if exists and not force:
            tqdm.write(f"  Season {year}-{year + 1} already in DB, skipping")
            return year, None

        return year, self.nba_season(year + 1)

    def data_years(self, beginning=2013, end=2023, db_path=DB_PATH, force=False):
        """
        Scrapes seasons in [beginning, end] and writes each to the SQLite DB.
        Skips seasons already present unless --force is set.
        Seasons are fetched concurrently; requests to basketball-reference.com
        are serialized via a rate limiter to comply with their crawler policy.
        ---
        Parameters:
            beginning: first season start year to include (inclusive)
            end: last season start year to include (inclusive)
            db_path: path to the SQLite database
            force: if True, re-scrape and replace seasons already in the DB
        """
        conn = init_db(db_path)
        years = list(range(beginning, end + 1))
        seasons_added = 0

        with tqdm(total=len(years), desc='Scraping seasons') as pbar:
            for year in years:
                try:
                    year_out, df = self._scrape_season(year, db_path, force)
                    if df is not None and not df.empty:
                        if force:
                            conn.execute("DELETE FROM games WHERE season = ?", (year_out,))
                            conn.commit()
                        insert_season(conn, year_out, df)
                        seasons_added += 1
                except Exception as e:
                    tqdm.write(f"Warning: failed to scrape {year}-{year + 1}: {e}")
                pbar.update(1)

        conn.close()
        print(f"Done. {seasons_added} season(s) added to {db_path}")


    def scrape_upcoming(self, days=7):
        """
        Fetches games not yet played within the next `days` days.
        Returns a DataFrame with columns: date, visitor, home.
        """
        from datetime import date, timedelta
        today = date.today()
        cutoff = today + timedelta(days=days)
        season_end_year = today.year + 1 if today.month >= 10 else today.year

        months = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
        upcoming = []

        for month in months:
            url = f'https://www.basketball-reference.com/leagues/NBA_{season_end_year}_games-{month}.html'
            try:
                response = self._rate_limited_get(url)
                if response.status_code != 200:
                    continue
                soup = bs4.BeautifulSoup(response.text, features='lxml')
                div = soup.find('div', {'id': 'div_schedule'})
                if div is None:
                    continue
                tbody = div.find('tbody')
                if tbody is None:
                    continue
                for game in tbody.find_all('tr'):
                    ths = game.find_all('th')
                    tds = game.find_all('td')
                    if not ths or len(tds) < 5:
                        continue
                    try:
                        game_date = datetime.strptime(ths[0].text.strip(), '%a, %b %d, %Y').date()
                    except ValueError:
                        continue
                    if game_date < today or game_date > cutoff:
                        continue
                    # Skip already-played games (score columns populated)
                    if tds[2].text.strip() or tds[4].text.strip():
                        continue
                    upcoming.append({
                        'date': game_date.strftime('%Y-%m-%d'),
                        'visitor': tds[1].text.strip(),
                        'home': tds[3].text.strip(),
                    })
            except Exception:
                pass

        return pd.DataFrame(upcoming) if upcoming else pd.DataFrame(columns=['date', 'visitor', 'home'])


def main():
    parser = argparse.ArgumentParser(description="Scrape NBA data for specified years and save to data/nba.db.")
    parser.add_argument("--beginning", type=int, default=2013, help="First season start year to scrape")
    parser.add_argument("--end", type=int, default=2023, help="Last season start year to scrape")
    parser.add_argument("--force", action="store_true", help="Re-scrape and replace seasons already in the DB")
    parser.add_argument("--migrate-only", action="store_true", help="Migrate existing CSVs in data/ into the DB and exit")
    parser.add_argument("--fill-gaps", action="store_true",
                        help="Detect and scrape all missing seasons in --beginning..--end range")
    parser.add_argument("--report-gaps", action="store_true",
                        help="Print missing seasons in range and exit without scraping")
    args = parser.parse_args()

    if args.migrate_only:
        conn = init_db(DB_PATH)
        migrate_csv(conn, Path('data'))
        conn.close()
        return

    if args.report_gaps or args.fill_gaps:
        gaps = find_gaps(args.beginning, args.end)
        if not gaps:
            print("No gaps found — all seasons present.")
        else:
            print(f"Missing seasons ({len(gaps)}): {gaps}")
        if args.report_gaps:
            return
        if gaps:
            scraper = NBAScraper()
            scraper.data_years(beginning=min(gaps), end=max(gaps), db_path=DB_PATH)
        return

    # Migrate any existing CSVs into the DB if the DB is new/empty
    conn = init_db(DB_PATH)
    cursor = conn.execute("SELECT COUNT(*) FROM games")
    db_empty = cursor.fetchone()[0] == 0
    conn.close()
    if db_empty:
        print("DB is empty — migrating existing CSVs in data/ ...")
        conn = init_db(DB_PATH)
        migrate_csv(conn, Path('data'))
        conn.close()

    nba_scraper = NBAScraper()
    print(f"Scraping seasons {args.beginning}–{args.end} into {DB_PATH} ...")
    nba_scraper.data_years(beginning=args.beginning, end=args.end, db_path=DB_PATH, force=args.force)

if __name__ == "__main__":
    main()
