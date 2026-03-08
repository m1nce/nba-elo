export interface EloDataPoint {
  date: string
  elo: number
}

export interface TeamEloSeries {
  team: string
  color: string
  data: EloDataPoint[]
}

export interface StandingRow {
  rank: number
  team: string
  logo_url: string
  current_elo: number
  delta: number
}

export interface GameRow {
  id: number
  date: string
  season: number
  visitor: string
  home: string
  v_logo: string | null
  h_logo: string | null
  visitor_points: number | null
  home_points: number | null
  result: string | null
  visitor_elo_before: number | null
  visitor_elo_after: number | null
  home_elo_before: number | null
  home_elo_after: number | null
  visitor_delta: number | null
  home_delta: number | null
  win_prob_visitor: number | null
  notes: string | null
}

export interface PaginatedGames {
  games: GameRow[]
  total: number
  page: number
  total_pages: number
}

export interface MatchupResponse {
  visitor: string
  home: string
  prob_v: number
  prob_h: number
  r_v: number
  r_h: number
  v_color: string
  h_color: string
  v_logo: string
  h_logo: string
  a_wins: number
  b_wins: number
  record_label: string
  elo_history_v: EloDataPoint[]
  elo_history_h: EloDataPoint[]
  h2h_games: GameRow[]
}

export interface UpcomingGame {
  date: string
  visitor: string
  home: string
  v_logo: string
  h_logo: string
  prob_v: number
  prob_h: number
  r_v: number
  r_h: number
}

export interface TeamMeta {
  name: string
  abbrev: string
  primary: string
  secondary: string
  logo_url: string
}

export interface EraInfo {
  id: string
  label: string
}
