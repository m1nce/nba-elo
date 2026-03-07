import { useState, useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts'
import { ChartContainer } from '@/components/ui/chart'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'

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
  const [activeTeams, setActiveTeams] = useState<Set<string>>(new Set())

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

  const allTeams = standings?.map(r => r.team) ?? []

  return (
    <div className="flex gap-4 h-full">
      {/* ELO Chart */}
      <div className="flex-1 min-w-0">
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
          <ChartContainer config={{}} className="h-[380px] w-full">
            <LineChart data={chartData} margin={{ left: 10, right: 10, top: 10, bottom: 10 }}>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false}
                interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={45} />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.length) return null
                  const pt = payload[0]
                  return (
                    <div className="rounded border bg-background px-2 py-1 text-xs shadow">
                      <span className="font-medium" style={{ color: pt.color }}>{pt.name}</span>
                      <span className="ml-2 text-muted-foreground">{Number(pt.value).toFixed(1)}</span>
                    </div>
                  )
                }}
              />
              {(eloData ?? [])
                .filter(s => activeTeams.has(s.team))
                .map(s => (
                  <Line key={s.team} type="monotone" dataKey={s.team}
                    stroke={s.color} dot={false} strokeWidth={1.5} isAnimationActive={false} connectNulls />
                ))}
            </LineChart>
          </ChartContainer>
        )}
      </div>

      {/* Standings */}
      <div className="w-[440px] shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-oswald text-lg tracking-wide">Current Standings</h2>
          <div className="flex items-center gap-2">
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
                  <th className="py-1 text-right">Δ Season</th>
                </tr>
              </thead>
              <tbody>
                {(standings ?? []).map(row => {
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
                          {row.rank}
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
