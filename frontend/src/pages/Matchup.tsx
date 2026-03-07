import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Brush, Tooltip } from 'recharts'
import { ChartContainer } from '@/components/ui/chart'
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

const H2H_FILTERS = [
  { label: 'Last 5',  value: 5 },
  { label: 'Last 10', value: 10 },
  { label: 'Last 20', value: 20 },
  { label: 'All',     value: 0 },
]

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

function GameLogRow({ game }: { game: GameRow }) {
  const visitorWon = game.result === 'visitor'
  return (
    <tr className="border-b last:border-0 hover:bg-muted/40 text-sm">
      <td className="py-1.5 text-muted-foreground">{game.date}</td>
      <td className={`py-1.5 font-medium ${visitorWon ? 'text-foreground' : 'text-muted-foreground'}`}>
        {game.visitor}
      </td>
      <td className={`py-1.5 font-medium ${!visitorWon ? 'text-foreground' : 'text-muted-foreground'}`}>
        {game.home}
      </td>
      <td className="py-1.5 text-center">
        {game.visitor_points} – {game.home_points}
      </td>
      <td className={`py-1.5 text-right text-xs ${(game.visitor_delta ?? 0) >= 0 ? 'text-green-600' : 'text-red-500'}`}>
        {(game.visitor_delta ?? 0) >= 0 ? '+' : ''}{(game.visitor_delta ?? 0).toFixed(1)}
      </td>
      <td className="py-1.5 text-right text-xs text-muted-foreground">
        {game.win_prob_visitor != null ? `${(game.win_prob_visitor * 100).toFixed(1)}%` : '—'}
      </td>
      <td className="py-1.5 text-right text-xs text-muted-foreground">{game.notes ?? ''}</td>
    </tr>
  )
}

export default function Matchup() {
  const [visitor, setVisitor] = useState('Los Angeles Lakers')
  const [home, setHome] = useState('Boston Celtics')
  const [h2hFilter, setH2hFilter] = useState(10)

  const { data, isLoading, error } = useQuery({
    queryKey: ['matchup', visitor, home, h2hFilter],
    queryFn: () => api.matchup(visitor, home, h2hFilter),
    enabled: visitor !== home,
  })

  const lowPct  = data ? Math.max(0,   data.prob_v * 100 - 10) : 40
  const highPct = data ? Math.min(100, data.prob_v * 100 + 10) : 60
  const gradientStyle = data
    ? `linear-gradient(90deg, ${data.v_color}bb 0%, ${data.v_color}33 ${lowPct.toFixed(1)}%, ${data.h_color}33 ${highPct.toFixed(1)}%, ${data.h_color}bb 100%)`
    : 'linear-gradient(90deg, #eee 0%, #eee 100%)'

  // Transform per-team series into row-oriented data for Recharts
  const chartData = useMemo(() => {
    if (!data) return []
    const byDate = new Map<string, Record<string, number | string>>()
    for (const pt of data.elo_history_v) {
      byDate.set(pt.date, { date: pt.date, [visitor]: pt.elo })
    }
    for (const pt of data.elo_history_h) {
      const row = byDate.get(pt.date) ?? { date: pt.date }
      row[home] = pt.elo
      byDate.set(pt.date, row)
    }
    return Array.from(byDate.values()).sort((a, b) =>
      String(a.date).localeCompare(String(b.date))
    )
  }, [data, visitor, home])

  return (
    <div className="space-y-4">
      {/* Team selectors */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <p className="text-xs text-muted-foreground mb-1 font-medium tracking-widest uppercase">Visitor</p>
          <Select value={visitor} onValueChange={setVisitor}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {ALL_TEAMS.map(t => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="font-oswald text-xl text-muted-foreground mt-5">VS</div>

        <div className="flex-1">
          <p className="text-xs text-muted-foreground mb-1 font-medium tracking-widest uppercase">Home</p>
          <Select value={home} onValueChange={setHome}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {ALL_TEAMS.map(t => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* H2H filter */}
      <div className="flex gap-1">
        <span className="text-sm text-muted-foreground self-center mr-2">Show:</span>
        {H2H_FILTERS.map(f => (
          <Button
            key={f.value}
            size="sm"
            variant={h2hFilter === f.value ? 'default' : 'outline'}
            onClick={() => setH2hFilter(f.value)}
          >
            {f.label}
          </Button>
        ))}
      </div>

      {visitor === home && (
        <p className="text-muted-foreground text-sm">Select two different teams.</p>
      )}

      {isLoading && visitor !== home && (
        <div className="text-muted-foreground text-sm">Loading matchup…</div>
      )}

      {error && (
        <div className="text-red-500 text-sm">Failed to load matchup data.</div>
      )}

      {data && (
        <>
          {/* Scoreboard + Chart row */}
          <div className="flex gap-4 items-start">
            {/* Scoreboard card */}
            <div
              className="flex-none w-72 rounded-xl border p-6 flex flex-col items-stretch"
              style={{ background: gradientStyle }}
            >
              {/* Visitor side */}
              <div className="flex justify-between items-center">
                <div className="text-center flex-1">
                  <img src={data.v_logo} alt={data.visitor} className="h-16 mx-auto mb-2"
                    style={{ filter: `drop-shadow(0 0 8px ${data.v_color}55)` }} />
                  <div className="font-oswald text-3xl font-bold" style={{ color: data.v_color }}>
                    {(data.prob_v * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 tracking-widest uppercase">
                    Visitor · ELO {data.r_v.toFixed(0)}
                  </div>
                  <div className="text-sm font-semibold mt-1">{data.visitor}</div>
                </div>

                <div className="text-center px-3 shrink-0">
                  <div className="font-oswald text-lg font-black text-muted-foreground/50 tracking-widest">VS</div>
                  <div className="w-px h-10 bg-gradient-to-b from-transparent via-border to-transparent mx-auto my-2" />
                  <div className="text-[10px] text-muted-foreground/60 tracking-wide uppercase leading-snug">
                    Home Court<br />+100 ELO
                  </div>
                </div>

                <div className="text-center flex-1">
                  <img src={data.h_logo} alt={data.home} className="h-16 mx-auto mb-2"
                    style={{ filter: `drop-shadow(0 0 8px ${data.h_color}55)` }} />
                  <div className="font-oswald text-3xl font-bold" style={{ color: data.h_color }}>
                    {(data.prob_h * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 tracking-widest uppercase">
                    Home · ELO {data.r_h.toFixed(0)}
                  </div>
                  <div className="text-sm font-semibold mt-1">{data.home}</div>
                </div>
              </div>
            </div>

            {/* ELO chart */}
            <div className="flex-1 min-w-0">
              <ChartContainer config={{}} className="h-[260px] w-full">
                <LineChart data={chartData} margin={{ left: 10, right: 10, top: 10, bottom: 30 }}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickLine={false} axisLine={false}
                    interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} tickLine={false} axisLine={false} width={40} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null
                      return (
                        <div className="rounded border bg-background px-2 py-1 text-xs shadow space-y-0.5">
                          {payload.map(pt => (
                            <div key={pt.name}>
                              <span className="font-medium" style={{ color: pt.color as string }}>{pt.name}</span>
                              <span className="ml-2 text-muted-foreground">{Number(pt.value).toFixed(1)}</span>
                            </div>
                          ))}
                        </div>
                      )
                    }}
                  />
                  <Brush dataKey="date" height={20} travellerWidth={6} />
                  <Line type="monotone" dataKey={visitor} stroke={data.v_color} dot={false} strokeWidth={2} isAnimationActive={false} connectNulls />
                  <Line type="monotone" dataKey={home} stroke={data.h_color} dot={false} strokeWidth={2} isAnimationActive={false} connectNulls />
                </LineChart>
              </ChartContainer>
            </div>
          </div>

          {/* Record banner */}
          <div
            className="rounded-xl border p-5 flex items-center justify-between"
            style={{
              background: `linear-gradient(90deg, ${data.v_color}11 0%, #f5f5f5 40%, #f5f5f5 60%, ${data.h_color}11 100%)`,
            }}
          >
            <div className="text-center flex-1">
              <img src={data.v_logo} alt={data.visitor} className="h-12 mx-auto mb-1"
                style={{ filter: `drop-shadow(0 0 6px ${data.v_color}55)` }} />
              <div className="font-oswald text-sm text-muted-foreground tracking-wide">{data.visitor}</div>
            </div>
            <div className="text-center px-6">
              <div className="font-oswald text-4xl font-bold tracking-widest">
                {data.a_wins} – {data.b_wins}
              </div>
              <div className="text-[10px] text-muted-foreground tracking-widest uppercase mt-1">
                {data.record_label}
              </div>
            </div>
            <div className="text-center flex-1">
              <img src={data.h_logo} alt={data.home} className="h-12 mx-auto mb-1"
                style={{ filter: `drop-shadow(0 0 6px ${data.h_color}55)` }} />
              <div className="font-oswald text-sm text-muted-foreground tracking-wide">{data.home}</div>
            </div>
          </div>

          {/* H2H game log */}
          {data.h2h_games.length === 0 ? (
            <p className="text-muted-foreground text-sm">No games found between these teams.</p>
          ) : (
            <ScrollArea className="h-80 rounded border">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background border-b">
                  <tr className="text-muted-foreground text-xs">
                    <th className="py-2 text-left pl-2">Date</th>
                    <th className="py-2 text-left">Visitor</th>
                    <th className="py-2 text-left">Home</th>
                    <th className="py-2 text-center">Score</th>
                    <th className="py-2 text-right">V ELO Δ</th>
                    <th className="py-2 text-right">Win Prob</th>
                    <th className="py-2 text-right pr-2">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.h2h_games.map(g => <GameLogRow key={g.id} game={g} />)}
                </tbody>
              </table>
            </ScrollArea>
          )}
        </>
      )}
    </div>
  )
}
