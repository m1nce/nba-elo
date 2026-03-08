import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { SlidersHorizontal, Check, X } from 'lucide-react'
import type { GameRow } from '@/lib/types'

const ALL_TEAMS = [
  'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
  'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
  'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
  'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
  'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
  'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
  'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
  'Utah Jazz', 'Washington Wizards',
]

function logoUrl(team: string) {
  // Use the same logo URL pattern as team_meta
  const abbr: Record<string, string> = {
    'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
    'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS',
  }
  const a = abbr[team]
  return a ? `https://cdn.nba.com/logos/nba/${a}/global/L/logo.svg` : null
}

function GameLogRow({ game }: { game: GameRow }) {
  const visitorWon = game.result === 'visitor'
  return (
    <tr className="border-b last:border-0 hover:bg-muted/40 text-sm">
      <td className="py-1.5 px-2 text-muted-foreground whitespace-nowrap">{game.date}</td>
      <td className={`py-1.5 ${visitorWon ? 'font-semibold' : 'text-muted-foreground'}`}>
        <span className="flex items-center gap-1.5">
          {game.v_logo && <img src={game.v_logo} alt="" className="h-5 w-5 object-contain flex-shrink-0" />}
          {game.visitor}
        </span>
      </td>
      <td className={`py-1.5 ${!visitorWon ? 'font-semibold' : 'text-muted-foreground'}`}>
        <span className="flex items-center gap-1.5">
          {game.h_logo && <img src={game.h_logo} alt="" className="h-5 w-5 object-contain flex-shrink-0" />}
          {game.home}
        </span>
      </td>
      <td className="py-1.5 text-center whitespace-nowrap">
        {game.visitor_points ?? '—'} – {game.home_points ?? '—'}
      </td>
      <td className={`py-1.5 text-right text-xs ${(game.visitor_delta ?? 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
        {game.visitor_delta != null ? `${game.visitor_delta >= 0 ? '+' : ''}${game.visitor_delta.toFixed(1)}` : '—'}
      </td>
      <td className={`py-1.5 text-right text-xs ${(game.home_delta ?? 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
        {game.home_delta != null ? `${game.home_delta >= 0 ? '+' : ''}${game.home_delta.toFixed(1)}` : '—'}
      </td>
      <td className="py-1.5 text-right text-xs text-muted-foreground">
        {game.win_prob_visitor != null ? `${(game.win_prob_visitor * 100).toFixed(1)}%` : '—'}
      </td>
      <td className="py-1.5 pr-2 text-right text-xs text-muted-foreground">{game.notes ?? ''}</td>
    </tr>
  )
}

export default function History() {
  const [team, setTeam] = useState('All')
  const [season, setSeason] = useState('All')
  const [page, setPage] = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [teamSearch, setTeamSearch] = useState('')

  const { data: seasons } = useQuery({
    queryKey: ['seasons'],
    queryFn: api.seasons,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['games', team, season, page],
    queryFn: () => api.games(team, season, page),
    placeholderData: prev => prev,
  })

  function handleTeamChange(v: string) {
    setTeam(v)
    setPage(0)
  }

  function handleSeasonChange(v: string) {
    setSeason(v)
    setPage(0)
  }

  const filteredTeams = ALL_TEAMS.filter(t =>
    t.toLowerCase().includes(teamSearch.toLowerCase())
  )

  const hasActiveFilters = team !== 'All' || season !== 'All'

  return (
    <div className="space-y-3">
      {/* Top bar */}
      <div className="flex items-center gap-3">
        <Button
          size="sm"
          variant={sidebarOpen ? 'default' : 'outline'}
          onClick={() => setSidebarOpen(o => !o)}
          className="flex items-center gap-1.5"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {hasActiveFilters && (
            <span className="ml-1 rounded-full bg-primary/20 px-1.5 py-0.5 text-xs font-medium">
              {(team !== 'All' ? 1 : 0) + (season !== 'All' ? 1 : 0)}
            </span>
          )}
        </Button>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total.toLocaleString()} games
          </span>
        )}
      </div>

      {/* Two-column layout */}
      <div className="flex gap-4">
        {/* Sidebar */}
        <div
          className={`transition-all duration-200 flex-shrink-0 overflow-hidden ${
            sidebarOpen ? 'w-[260px]' : 'w-0'
          }`}
        >
          <div className="w-[260px] bg-card border rounded-lg p-3 space-y-4">
            {/* Active filter chips */}
            {hasActiveFilters && (
              <div className="flex flex-wrap gap-1.5">
                {team !== 'All' && (
                  <span className="flex items-center gap-1 rounded-full bg-accent px-2 py-0.5 text-xs">
                    {team}
                    <button onClick={() => handleTeamChange('All')} className="ml-0.5 hover:text-destructive">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                )}
                {season !== 'All' && (
                  <span className="flex items-center gap-1 rounded-full bg-accent px-2 py-0.5 text-xs">
                    {season}–{Number(season) + 1}
                    <button onClick={() => handleSeasonChange('All')} className="ml-0.5 hover:text-destructive">
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                )}
              </div>
            )}

            {/* Teams section */}
            <div className="space-y-2">
              <p className="text-xs uppercase text-muted-foreground font-medium tracking-wide">Team</p>
              <Input
                placeholder="Search teams…"
                value={teamSearch}
                onChange={e => setTeamSearch(e.target.value)}
                className="h-7 text-sm"
              />
              <div className="max-h-[300px] overflow-y-auto space-y-0.5 -mx-1 px-1">
                {/* All Teams row */}
                <button
                  onClick={() => handleTeamChange('All')}
                  className={`flex w-full items-center gap-2 rounded px-2 py-1 text-sm hover:bg-accent/50 ${
                    team === 'All' ? 'bg-accent' : ''
                  }`}
                >
                  <span className="h-5 w-5 flex-shrink-0" />
                  <span className="flex-1 text-left">All Teams</span>
                  {team === 'All' && <Check className="h-3.5 w-3.5 text-primary" />}
                </button>
                {filteredTeams.map(t => {
                  const logo = logoUrl(t)
                  const isActive = team === t
                  return (
                    <button
                      key={t}
                      onClick={() => handleTeamChange(t)}
                      className={`flex w-full items-center gap-2 rounded px-2 py-1 text-sm hover:bg-accent/50 ${
                        isActive ? 'bg-accent' : ''
                      }`}
                    >
                      {logo
                        ? <img src={logo} alt="" className="h-5 w-5 object-contain flex-shrink-0" />
                        : <span className="h-5 w-5 flex-shrink-0" />
                      }
                      <span className="flex-1 text-left">{t}</span>
                      {isActive && <Check className="h-3.5 w-3.5 text-primary" />}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Seasons section */}
            <div className="space-y-2">
              <p className="text-xs uppercase text-muted-foreground font-medium tracking-wide">Season</p>
              <div className="flex flex-wrap gap-1.5">
                <button
                  onClick={() => handleSeasonChange('All')}
                  className={`rounded-full px-2.5 py-0.5 text-xs border transition-colors ${
                    season === 'All'
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'border-border hover:bg-accent/50'
                  }`}
                >
                  All
                </button>
                {(seasons ?? []).slice().reverse().map(s => (
                  <button
                    key={s}
                    onClick={() => handleSeasonChange(String(s))}
                    className={`rounded-full px-2.5 py-0.5 text-xs border transition-colors ${
                      season === String(s)
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'border-border hover:bg-accent/50'
                    }`}
                  >
                    {s}–{s + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Table + pagination */}
        <div className="flex-1 min-w-0 space-y-3">
          <ScrollArea className="rounded border h-[1165px]">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-background border-b">
                <tr className="text-muted-foreground text-xs">
                  <th className="py-2 text-left pl-2">Date</th>
                  <th className="py-2 text-left">Visitor</th>
                  <th className="py-2 text-left">Home</th>
                  <th className="py-2 text-center">Score</th>
                  <th className="py-2 text-right">V ELO Δ</th>
                  <th className="py-2 text-right">H ELO Δ</th>
                  <th className="py-2 text-right">Win Prob</th>
                  <th className="py-2 text-right pr-2">Notes</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-muted-foreground">Loading…</td>
                  </tr>
                ) : (
                  (data?.games ?? []).map(g => <GameLogRow key={g.id} game={g} />)
                )}
              </tbody>
            </table>
          </ScrollArea>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <Button
              size="sm"
              variant="outline"
              disabled={page <= 0}
              onClick={() => setPage(p => p - 1)}
            >
              ← Prev
            </Button>
            <span className="text-sm text-muted-foreground">
              {data
                ? `Page ${data.page + 1} of ${data.total_pages}`
                : '—'}
            </span>
            <Button
              size="sm"
              variant="outline"
              disabled={!data || page >= data.total_pages - 1}
              onClick={() => setPage(p => p + 1)}
            >
              Next →
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
