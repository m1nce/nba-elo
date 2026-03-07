import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { GameRow } from '@/lib/types'

const ALL_TEAMS = [
  'All',
  'Atlanta Hawks', 'Boston Celtics', 'Brooklyn Nets', 'Charlotte Hornets',
  'Chicago Bulls', 'Cleveland Cavaliers', 'Dallas Mavericks', 'Denver Nuggets',
  'Detroit Pistons', 'Golden State Warriors', 'Houston Rockets', 'Indiana Pacers',
  'Los Angeles Clippers', 'Los Angeles Lakers', 'Memphis Grizzlies', 'Miami Heat',
  'Milwaukee Bucks', 'Minnesota Timberwolves', 'New Orleans Pelicans', 'New York Knicks',
  'Oklahoma City Thunder', 'Orlando Magic', 'Philadelphia 76ers', 'Phoenix Suns',
  'Portland Trail Blazers', 'Sacramento Kings', 'San Antonio Spurs', 'Toronto Raptors',
  'Utah Jazz', 'Washington Wizards',
]

function GameLogRow({ game }: { game: GameRow }) {
  const visitorWon = game.result === 'visitor'
  return (
    <tr className="border-b last:border-0 hover:bg-muted/40 text-sm">
      <td className="py-1.5 px-2 text-muted-foreground whitespace-nowrap">{game.date}</td>
      <td className={`py-1.5 ${visitorWon ? 'font-semibold' : 'text-muted-foreground'}`}>{game.visitor}</td>
      <td className={`py-1.5 ${!visitorWon ? 'font-semibold' : 'text-muted-foreground'}`}>{game.home}</td>
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

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex gap-3">
        <div className="w-56">
          <Select value={team} onValueChange={handleTeamChange}>
            <SelectTrigger><SelectValue placeholder="All Teams" /></SelectTrigger>
            <SelectContent>
              {ALL_TEAMS.map(t => (
                <SelectItem key={t} value={t}>{t === 'All' ? 'All Teams' : t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-40">
          <Select value={season} onValueChange={handleSeasonChange}>
            <SelectTrigger><SelectValue placeholder="All Seasons" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="All">All Seasons</SelectItem>
              {(seasons ?? []).map(s => (
                <SelectItem key={s} value={String(s)}>{s}–{s + 1}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Table */}
      <ScrollArea className="rounded border h-[520px]">
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
            ? `Page ${data.page + 1} of ${data.total_pages} · ${data.total.toLocaleString()} games`
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
  )
}
