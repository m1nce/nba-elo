import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis } from 'recharts'
import { ChartContainer } from '@/components/ui/chart'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'

const CONFERENCE: Record<string, 'East' | 'West'> = {
  // East
  'Boston Celtics': 'East', 'Brooklyn Nets': 'East', 'New York Knicks': 'East',
  'Philadelphia 76ers': 'East', 'Toronto Raptors': 'East',
  'Chicago Bulls': 'East', 'Cleveland Cavaliers': 'East', 'Detroit Pistons': 'East',
  'Indiana Pacers': 'East', 'Milwaukee Bucks': 'East',
  'Atlanta Hawks': 'East', 'Charlotte Hornets': 'East', 'Miami Heat': 'East',
  'Orlando Magic': 'East', 'Washington Wizards': 'East',
  // West
  'Denver Nuggets': 'West', 'Minnesota Timberwolves': 'West',
  'Oklahoma City Thunder': 'West', 'Portland Trail Blazers': 'West', 'Utah Jazz': 'West',
  'Golden State Warriors': 'West', 'Los Angeles Clippers': 'West',
  'Los Angeles Lakers': 'West', 'Phoenix Suns': 'West', 'Sacramento Kings': 'West',
  'Dallas Mavericks': 'West', 'Houston Rockets': 'West', 'Memphis Grizzlies': 'West',
  'New Orleans Pelicans': 'West', 'San Antonio Spurs': 'West',
}

const ERAS = [
  { id: 'all',    label: 'All Time' },
  { id: 'bird',   label: 'Bird / Magic' },
  { id: 'jordan', label: 'Jordan' },
  { id: 'kobe',   label: 'Kobe Era' },
  { id: 'lebron', label: 'LeBron' },
  { id: 'last5',   label: 'Last 5 Yrs' },
  { id: 'current', label: 'Current Season' },
]

export default function EloStandings() {
  const [era, setEra] = useState('current')
  const [conference, setConference] = useState<'All' | 'East' | 'West'>('All')
  const [activeTeams, setActiveTeams] = useState<Set<string>>(new Set())
  const [hoveredDate, setHoveredDate] = useState<string | null>(null)
  const [lockedDate, setLockedDate] = useState<string | null>(null)

  const { data: eloData, isLoading: eloLoading } = useQuery({
    queryKey: ['elo-history', era],
    queryFn: () => api.eloHistory(era),
  })

  const { data: standings, isLoading: standingsLoading } = useQuery({
    queryKey: ['standings'],
    queryFn: api.standings,
  })

  // Initialize activeTeams once standings load
  useEffect(() => {
    if (standings && activeTeams.size === 0) {
      setActiveTeams(new Set(standings.map(r => r.team)))
    }
  }, [standings])

  const toggleTeam = (team: string) =>
    setActiveTeams(prev => {
      const next = new Set(prev)
      next.has(team) ? next.delete(team) : next.add(team)
      return next
    })

  // Build color map from eloData (team → color)
  const colorMap = useMemo(() => {
    const map: Record<string, string> = {}
    for (const series of eloData ?? []) {
      map[series.team] = series.color
    }
    return map
  }, [eloData])

  // Transform per-team series into row-oriented data for Recharts
  const chartData = useMemo(() => {
    const byDate = new Map<string, Record<string, number | string>>()
    for (const series of eloData ?? []) {
      for (const pt of series.data) {
        const row = byDate.get(pt.date) ?? { date: pt.date }
        row[series.team] = pt.elo
        byDate.set(pt.date, row)
      }
    }
    return Array.from(byDate.values()).sort((a, b) =>
      String(a.date).localeCompare(String(b.date))
    )
  }, [eloData])

  const yDomain = useMemo(() => {
    let min = Infinity, max = -Infinity
    for (const row of chartData) {
      for (const [k, v] of Object.entries(row)) {
        if (k !== 'date' && typeof v === 'number') {
          if (v < min) min = v
          if (v > max) max = v
        }
      }
    }
    if (!isFinite(min)) return ['auto', 'auto'] as const
    const pad = 50
    return [Math.floor((min - pad) / 10) * 10, Math.ceil((max + pad) / 10) * 10] as const
  }, [chartData])

  function interpolateElo(idx: number, team: string): number | null {
    const direct = chartData[idx][team]
    if (typeof direct === 'number') return direct

    let before: number | null = null, beforeIdx = -1
    for (let i = idx - 1; i >= 0; i--) {
      if (typeof chartData[i][team] === 'number') { before = chartData[i][team] as number; beforeIdx = i; break }
    }
    let after: number | null = null, afterIdx = -1
    for (let i = idx + 1; i < chartData.length; i++) {
      if (typeof chartData[i][team] === 'number') { after = chartData[i][team] as number; afterIdx = i; break }
    }

    if (before !== null && after !== null) {
      const t = (idx - beforeIdx) / (afterIdx - beforeIdx)
      return before + t * (after - before)
    }
    return before ?? after
  }

  const filteredStandings = (standings ?? []).filter(row =>
    conference === 'All' || CONFERENCE[row.team] === conference
  )

  const logoMap = useMemo(() => {
    const m: Record<string, string> = {}
    for (const r of standings ?? []) m[r.team] = r.logo_url
    return m
  }, [standings])

  const snapshotStandings = useMemo(() => {
    const targetDate = lockedDate ?? hoveredDate
    if (!targetDate || !chartData.length) return null

    const idx = chartData.findIndex(r => r.date === targetDate)
    if (idx === -1) return null

    return (eloData ?? [])
      .map(s => ({ team: s.team, elo: interpolateElo(idx, s.team), color: s.color }))
      .filter((r): r is { team: string; elo: number; color: string } => r.elo !== null)
      .filter(r => conference === 'All' || CONFERENCE[r.team] === conference)
      .sort((a, b) => b.elo - a.elo)
  }, [lockedDate, hoveredDate, chartData, eloData, conference])

  const allTeams = standings?.map(r => r.team) ?? []

  return (
    <div className="flex gap-4 h-full">
      {/* ELO Chart */}
      <div className="relative flex-1 min-w-0">
        <div className="flex gap-1 flex-wrap mb-2 justify-center">
          {ERAS.map(e => (
            <Button
              key={e.id}
              size="sm"
              variant={era === e.id ? 'default' : 'outline'}
              onClick={() => setEra(e.id)}
            >
              {e.label}
            </Button>
          ))}
        </div>
        {eloLoading ? (
          <div className="flex items-center justify-center h-[380px] text-muted-foreground">
            Loading chart…
          </div>
        ) : (
          <>
          <ChartContainer config={{}} className="h-[380px] w-full">
            <LineChart
              data={chartData}
              margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
              onMouseMove={(state) => {
                if (!lockedDate && state.activeLabel) setHoveredDate(state.activeLabel as string)
              }}
              onMouseLeave={() => {
                if (!lockedDate) setHoveredDate(null)
              }}
              onClick={(state) => {
                if (state?.activeLabel) setLockedDate(state.activeLabel as string)
              }}
            >
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false}
                interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={45} domain={yDomain} />
              {(eloData ?? [])
                .filter(s => activeTeams.has(s.team))
                .map(s => (
                  <Line key={s.team} type="monotone" dataKey={s.team}
                    stroke={s.color} dot={false} strokeWidth={1.5} isAnimationActive={false} connectNulls />
                ))}
            </LineChart>
          </ChartContainer>

          </>
        )}
      </div>

      {/* Standings */}
      <div className="w-[440px] shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-oswald text-lg tracking-wide">
            {lockedDate ?? hoveredDate
              ? `Standings — ${lockedDate ?? hoveredDate}`
              : 'Current Standings'}
          </h2>
          <div className="flex items-center gap-2">
            {lockedDate && (
              <Button size="sm" variant="outline" className="h-6 text-xs px-2"
                onClick={() => { setLockedDate(null); setHoveredDate(null) }}>
                Reset
              </Button>
            )}
            <Button
              size="sm"
              variant="outline"
              className="h-6 text-xs px-2"
              onClick={() => setActiveTeams(new Set(allTeams))}
            >
              Select All
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-6 text-xs px-2"
              onClick={() => setActiveTeams(new Set())}
            >
              Clear
            </Button>
            <span className="text-xs text-muted-foreground">
              {activeTeams.size} / {allTeams.length}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1 mb-2">
          <span className="text-xs text-muted-foreground mr-1">Conference</span>
          {(['All', 'East', 'West'] as const).map(c => (
            <Button
              key={c}
              size="sm"
              variant={conference === c ? 'default' : 'outline'}
              className="h-6 text-xs px-2"
              onClick={() => {
                setConference(c)
                const teams = (standings ?? [])
                  .filter(r => c === 'All' || CONFERENCE[r.team] === c)
                  .map(r => r.team)
                setActiveTeams(new Set(teams))
              }}
            >
              {c}
            </Button>
          ))}
        </div>
        <ScrollArea className="h-[500px]">
          {standingsLoading ? (
            <div className="text-muted-foreground text-sm p-2">Loading…</div>
          ) : (
            <table className="w-full text-sm pr-3">
              <thead>
                <tr className="text-muted-foreground text-xs border-b">
                  <th className="py-1 text-left w-10">#</th>
                  <th className="py-1 w-7" />
                  <th className="py-1 text-left">Team</th>
                  <th className="py-1 text-right">ELO</th>
                  {!snapshotStandings && <th className="py-1 text-right">Δ Season</th>}
                </tr>
              </thead>
              <tbody>
                {snapshotStandings
                  ? snapshotStandings.map((row, idx) => {
                      const isActive = activeTeams.has(row.team)
                      return (
                        <tr key={row.team} onClick={() => toggleTeam(row.team)}
                          className={`border-b last:border-0 hover:bg-muted/40 cursor-pointer transition-opacity ${isActive ? 'opacity-100' : 'opacity-40'}`}>
                          <td className="py-1 text-muted-foreground">
                            <span className="inline-flex items-center gap-1">
                              <span className="text-base leading-none" style={{ color: isActive && row.color ? row.color : undefined }}>
                                {isActive ? '●' : <span className="text-muted-foreground">○</span>}
                              </span>
                              {idx + 1}
                            </span>
                          </td>
                          <td className="py-1">
                            <img src={logoMap[row.team]} alt={row.team} className="h-6 w-6 object-contain" />
                          </td>
                          <td className="py-1 font-medium truncate max-w-[140px]">{row.team}</td>
                          <td className="py-1 text-right tabular-nums">{row.elo.toFixed(1)}</td>
                        </tr>
                      )
                    })
                  : filteredStandings.map((row, idx) => {
                      const isActive = activeTeams.has(row.team)
                      const dotColor = colorMap[row.team]
                      return (
                        <tr
                          key={row.team}
                          onClick={() => toggleTeam(row.team)}
                          className={`border-b last:border-0 hover:bg-muted/40 cursor-pointer transition-opacity ${isActive ? 'opacity-100' : 'opacity-40'}`}
                        >
                          <td className="py-1 text-muted-foreground">
                            <span className="inline-flex items-center gap-1">
                              <span
                                className="text-base leading-none"
                                style={{ color: isActive && dotColor ? dotColor : undefined }}
                              >
                                {isActive ? '●' : <span className="text-muted-foreground">○</span>}
                              </span>
                              {idx + 1}
                            </span>
                          </td>
                          <td className="py-1">
                            <img src={row.logo_url} alt={row.team} className="h-6 w-6 object-contain" />
                          </td>
                          <td className="py-1 font-medium truncate max-w-[140px]">{row.team}</td>
                          <td className="py-1 text-right">{row.current_elo.toFixed(1)}</td>
                          <td className="py-1 text-right">
                            <Badge
                              variant="outline"
                              className={
                                row.delta > 0
                                  ? 'text-green-600 border-green-200 text-xs px-1'
                                  : row.delta < 0
                                  ? 'text-red-500 border-red-200 text-xs px-1'
                                  : 'text-muted-foreground text-xs px-1'
                              }
                            >
                              {row.delta > 0 ? '+' : ''}{row.delta.toFixed(1)}
                            </Badge>
                          </td>
                        </tr>
                      )
                    })}
              </tbody>
            </table>
          )}
        </ScrollArea>
      </div>
    </div>
  )
}
