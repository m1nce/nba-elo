import type {
  TeamEloSeries,
  StandingRow,
  MatchupResponse,
  PaginatedGames,
  UpcomingGame,
  TeamMeta,
  EraInfo,
} from './types'

const BASE = 'http://localhost:8000/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`)
  return res.json() as Promise<T>
}

export const api = {
  eloHistory: (era = 'all') =>
    get<TeamEloSeries[]>(`/elo/history?era=${era}`),

  standings: () =>
    get<StandingRow[]>('/standings'),

  matchup: (visitor: string, home: string, h2hFilter: number) =>
    get<MatchupResponse>(
      `/matchup?visitor=${encodeURIComponent(visitor)}&home=${encodeURIComponent(home)}&h2h_filter=${h2hFilter}`
    ),

  games: (team: string, season: string, page: number) =>
    get<PaginatedGames>(
      `/games?team=${encodeURIComponent(team)}&season=${encodeURIComponent(season)}&page=${page}`
    ),

  upcoming: () =>
    get<UpcomingGame[]>('/upcoming'),

  teams: () =>
    get<TeamMeta[]>('/teams'),

  seasons: () =>
    get<number[]>('/seasons'),

  eras: () =>
    get<EraInfo[]>('/eras'),

  refresh: () =>
    fetch(`${BASE}/refresh`, { method: 'POST' }).then(r => r.json()),

  refreshStatus: () =>
    get<{ running: boolean }>('/refresh/status'),
}
